from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
import os
import sys

# Import llama-cpp-python
from llama_cpp import Llama

app = Flask(__name__)

# Database configuration using environment variables for security
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = 'TSMs0lolift!'  # Ensure this environment variable is set
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'customer_db')

# SQLAlchemy engine
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

# Load the model
# Provide the path to your local GGUF model file
model_path = 'path/to/your/model/Hrida-T2SQL-3B-128k-V0.1.gguf'
llm = Llama(model_path=model_path)

# Generate SQL
def generate_sql(question):
    # Database schema and examples provided to the model
    prompt = f"""
You are an AI assistant that converts natural language questions into SQL queries based on the provided database schema.

Database Schema:

Table: customers
- customer_id (INT, PRIMARY KEY)
- first_name (VARCHAR)
- last_name (VARCHAR)
- phone (VARCHAR)

Table: products
- product_id (INT, PRIMARY KEY)
- product_name (VARCHAR)
- product_description (TEXT)
- price (DECIMAL)

Table: invoices
- invoice_id (INT, PRIMARY KEY)
- customer_id (INT, FOREIGN KEY -> customers.customer_id)
- invoice_date (DATETIME)
- total_amount (DECIMAL)

Table: invoice_items
- invoice_id (INT, FOREIGN KEY -> invoices.invoice_id)
- product_id (INT, FOREIGN KEY -> products.product_id)
- quantity (INT)
- price (DECIMAL)

Examples:

Q: How many customers are there?
SQL: SELECT COUNT(*) FROM customers;

Q: List all products with a price greater than $50.
SQL: SELECT * FROM products WHERE price > 50;

Q: Show all invoices for customer with customer_id 1.
SQL: SELECT * FROM invoices WHERE customer_id = 1;

Please generate the SQL query for the following question:

Q: {question}
SQL:
"""

    # Generate the SQL query using the Llama model
    output = llm(prompt=prompt, max_tokens=256, stop=["\nQ:", "\n"])
    generated_text = output['choices'][0]['text']

    # Extract the SQL query from the generated text
    sql_query = generated_text.strip()

    return sql_query

# Function to check if the SQL query is safe
def is_sql_safe(query):
    # Allow only SELECT statements
    query = query.strip().upper()
    return query.startswith('SELECT')

# Flask route to handle user interaction
@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    columns = None
    error = None

    if request.method == 'POST':
        question = request.form['question']

        # Generate SQL query from natural language
        try:
            sql_query = generate_sql(question)
            print(f"Generated SQL Query: {sql_query}")

            # Secure the query
            if not is_sql_safe(sql_query):
                raise ValueError("Generated SQL query contains unsafe operations.")

            # Execute the SQL query
            with engine.connect() as connection:
                result_proxy = connection.execute(text(sql_query))
                results = [dict(row._mapping) for row in result_proxy]
                columns = results[0].keys() if results else []
        except Exception as e:
            error = "An error occurred while processing your request."
            app.logger.error(f"Error: {str(e)}")

    return render_template('index.html', results=results, columns=columns, error=error)

if __name__ == "__main__":
    app.run(debug=True)