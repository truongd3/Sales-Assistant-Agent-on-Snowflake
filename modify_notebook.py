import nbformat
import pandas as pd
import base64 # Often used for images, good to know

# 1. Load the notebook file
with open('SETUP_TOOLS.ipynb', 'r') as f:
    nb = nbformat.read(f, as_version=4)

# 2. Read downloaded CSV data
try:
    df = pd.read_csv('2025-10-05T01-51_export.csv')
    # 3. Format the data as an HTML table
    html_output = df.to_html()

    # Create a new output object in the format Jupyter expects
    # This represents a rich display output with an HTML representation
    new_output = nbformat.v4.new_output(
        output_type='execute_result',  # <-- Add this line
        data={
            'text/html': html_output,
            'text/plain': df.to_string()
        },
        execution_count=1  # <-- This is the cell execution number, e.g., In [1]:
    )

    # 4. Find the target cell and insert the output
    cell_index = 35
    print("Line 29", nb.cells[cell_index])
    if cell_index != -1:
        # Append the new output to the cell's 'outputs' list
        # nb.cells[cell_index].outputs.append(new_output)
        nb.cells[cell_index].outputs = [new_output]
        print(f"Successfully inserted output into code cell {cell_index}.")
    else:
        print("No code cell found in the notebook.")

    # 5. Save the modified notebook
    with open('my_notebook_with_outputs.ipynb', 'w') as f:
        nbformat.write(nb, f)
    print("New notebook 'my_notebook_with_outputs.ipynb' has been saved.")

except FileNotFoundError:
    print("Error: Make sure 'my_snowflake_notebook.ipynb' and 'cell_output_1.csv' are in the same directory.")
except Exception as e:
    print(f"An error occurred: {e}")