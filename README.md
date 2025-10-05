# Sales Assistant Agent on Snowflake

_Members: Truong Dang, Snowflake Solution Engineers_

![test1](https://i.imgur.com/vEHZ5KT.png)

Test 2A             |  Test 2B
:-------------------------:|:-------------------------:
![test2a](https://i.imgur.com/cT8SP1j.png) | ![test2b](https://i.imgur.com/QcnCjGG.png)

## What It Does

This project develops a **Sales Assistant Agent** using data tools in **Snowflake Cortex**. The Agent is able to analyze structured and unstructured data (PDFs and images), classify data, and make data searchable through Cortex Search.

### Step 1: Create Tools for Unstructured Data (_Cortex Search_)

- Extract PDF content
- Split PDFs into chunks
- Classify the PDFs: Uses `CORTEX.CLASSIFY_TEXT` to classify documents as `Bike` or `Snow` based on the first text chunk and filename

### Step 2: Process Images

- Use [Claude 3.5 Sonnot](https://www.anthropic.com/news/claude-3-5-sonnet) model API to
  - Describe image content
  - Classify image as `Bike` or `Snow`
  - Insert result into the same `DOCS_CHUNKS_TABLE`

### Step 3: Enable Cortex Search

- Create a Warehouse
- Create the Search Service: build a **Cortex Search index** that automatically embeds text, vectorizes text, indexes text for fast retrieval, and refreshes hourly

### Step 4: Structured Data Setup

- Create structured tables for sales analysis:
  - `DIM_ARTICLE`: Store description of the products (articles being sold) like name, brand, category, color, price, ...
  - `DIM_CUSTOMER`: Store demographic and segmentation info about each customer
  - `FACT_SALES`: Store sales transaction (facts) with references to article and customer

### Step 5: Chatbot Interface ([streamlit_app.py](streamlit_app.py))

## Technology

- Snowflake
  - Snowflake Cortex Agents
  - Snowflake Cortex LLM Functions
- Python
  - `snowflake.cortex`
  - `snowflake.snowpark`
  - `pandas`
- Streamlit
- SQL