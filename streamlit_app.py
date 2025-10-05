import streamlit as st
import json
import _snowflake
from snowflake.snowpark.context import get_active_session
from typing import Dict, List, Any, Optional, Tuple, Union
from streamlit_extras.stylable_container import stylable_container


session = get_active_session()

API_ENDPOINT = "/api/v2/cortex/agent:run"
API_TIMEOUT = 50000  # in milliseconds

CORTEX_SEARCH_DOCUMENTATION = "CC_CORTEX_AGENTS_SUMMIT.PUBLIC.DOCUMENTATION_TOOL"
SEMANTIC_MODEL = "@CC_CORTEX_AGENTS_SUMMIT.PUBLIC.SEMANTIC_FILES/semantic_search.yaml"

def run_snowflake_query(query):
    try:
        df = session.sql(query.replace(';',''))
        return df

    except Exception as e:
        st.error(f"Error executing SQL: {str(e)}")
        return None, None

def snowflake_api_call(query: str, limit: int = 10):
    
    payload = {
        "model": "claude-3-5-sonnet",
        "messages": [{"role": "user",
                      "content": 
                          [{"type": "text","text": query}]}],
        
        ##############  MAKE CHANGES HERE for your own services/yamls ##############
        "tools": [
            {"tool_spec": 
                {"type": "cortex_analyst_text_to_sql",
                 "name": "Sales Analyst"}},
            
            {"tool_spec": 
                {"type": "cortex_search",
                 "name": "Docs and Images Search"}},   
        ],
        "tool_resources": {
            "Sales Analyst": 
                {"semantic_model_file": SEMANTIC_MODEL},
            "Docs and Images Search": 
                {"name": CORTEX_SEARCH_DOCUMENTATION, 
                 "max_results": 3, 
                 "title_column":"RELATIVE_PATH",
                 "id_column": "CHUNK_INDEX",
                 "experimental": {"returnConfidenceScores": True}},
        },    
        "response_instruction": "You will be asked about bikes or ski specifications or analytical data. Be concise in your answer"
    }   
     
    try:
        resp = _snowflake.send_snow_api_request(
            "POST",  # method
            API_ENDPOINT,  # path
            {},  # headers
            {'stream': True},  # query params
            payload,  # body
            None,  # request_guid
            API_TIMEOUT,  # timeout in milliseconds,
        )
        
        if resp["status"] != 200:
            st.error(f"❌ HTTP Error: {resp['status']} - {resp.get('reason', 'Unknown reason')}")
            st.error(f"Response details: {resp}")
            return None
    
        try:
            response_content = json.loads(resp["content"])
        except json.JSONDecodeError:
            st.error("❌ Failed to parse API response. The server may have returned an invalid JSON format.")
            st.error(f"Raw response: {resp['content'][:200]}...")
            return None

        return response_content  
    except Exception as e:
        st.error(f"Error making request: {str(e)}")
        return None

def process_sse_response(response):
    """Process SSE response"""
    text = ""
    sql = ""
    citations = []
    
    if not response:
        return text, sql, citations
    if isinstance(response, str):
        return text, sql, citations
    try:
        for event in response:
            if event.get('event') == "message.delta":
                data = event.get('data', {})
                delta = data.get('delta', {})
                
                for content_item in delta.get('content', []):
                    content_type = content_item.get('type')
                    if content_type == "tool_results":
                        tool_results = content_item.get('tool_results', {})
                        if 'content' in tool_results:
                            for result in tool_results['content']:
                                if result.get('type') == 'json':
                                    json_data = result.get('json', {})
                                    text += json_data.get('text', '')
                                    search_results = json_data.get('searchResults', [])
                                    for search_result in search_results:
                                        citations.append({'source_id': search_result.get('source_id', ''), 
                                                          'doc_title': search_result.get('doc_title', ''),
                                                          'doc_chunk': search_result.get('doc_id')})
                                    sql = json_data.get('sql', '')
                    if content_type == 'text':
                        text += content_item.get('text', '')                   
    except json.JSONDecodeError as e:
        st.error(f"Error processing events: {str(e)}")           
    except Exception as e:
        st.error(f"Error processing events: {str(e)}")
        
    return text, sql, citations

def display_citations(citations):
    for citation in citations:
        source_id = citation.get("source_id", "")
        doc_title = citation.get("doc_title", "")
        doc_chunk = citation.get("doc_chunk", "")
    
        if (doc_title.lower().endswith("jpeg")):
            query = f"SELECT GET_PRESIGNED_URL('@DOCS', '{doc_title}') as URL"
            result = run_snowflake_query(query)
            result_df = result.to_pandas()
            if not result_df.empty:
                url = result_df.iloc[0, 0]
            else:
                url = "No URL available"
    
            with st.expander(f"[{source_id}]"):
                st.image(url)

        if (doc_title.lower().endswith("pdf")):
            query = f"""
                    SELECT CHUNK from DOCS_CHUNKS_TABLE
                    WHERE RELATIVE_PATH = '{doc_title}' AND
                          CHUNK_INDEX = {doc_chunk}
            """
            result = run_snowflake_query(query)
            result_df = result.to_pandas()
            if not result_df.empty:
                text = result_df.iloc[0, 0]
            else:
                text = "No text available"

            with st.expander(f"[{source_id}]"):
                with stylable_container(
                        f"[{source_id}]",
                        css_styles="""
                        {
                            border: 1px solid #e0e7ff;
                            border-radius: 8px;
                            padding: 14px;
                            margin-bottom: 12px;
                            background-color: #f5f8ff;
                        }
                        """
                    ):
                    st.markdown(text)

def main():
    st.title("Intelligent Sales Assistant")

    # Sidebar for new chat
    with st.sidebar:
        if st.button("New Conversation", key="new_chat"):
            st.session_state.messages = []
            st.rerun()

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'].replace("•", "\n\n"))

    if query := st.chat_input("Would you like to learn?"):
        # Add user message to chat
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Get response from API
        with st.spinner("Processing your request..."):
            response = snowflake_api_call(query, 1)
            text, sql, citations = process_sse_response(response)
            
            # Add assistant response to chat
            if text:
                text = text.replace("【†", "[")
                text = text.replace("†】", "]")
                st.session_state.messages.append({"role": "assistant", "content": text})
                
                with st.chat_message("assistant"):
                    st.markdown(text.replace("•", "\n\n"))
                    if citations:
                        display_citations(citations)
    
            # Display SQL if present
            if sql:
                st.markdown("### Generated SQL")
                st.code(sql, language="sql")
                sales_results = run_snowflake_query(sql)
                if sales_results:
                    st.write("### Sales Metrics Report")
                    st.dataframe(sales_results)

if __name__ == "__main__":
    main()