from fastapi import FastAPI
from contextlib import asynccontextmanager
from pydantic import BaseModel
import sqlite3
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get configuration from environment variables
DB_PATH = os.getenv('ANALYSIS_DB_PATH', 'analysis.db')  # fallback to default if not set
JSON_PATH = os.getenv('ANALYSIS_DATA_JSON', 'analysis_data.json')

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

class UpdateRequest(BaseModel):
    new_content: str

# Initialize database and load initial data
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS analysis
                 (id INTEGER PRIMARY KEY, 
                  company TEXT,
                  buyer TEXT,
                  matrix_cell TEXT,
                  gpt_output TEXT)''')
    
    # Load initial data if table is empty
    c.execute('SELECT COUNT(*) FROM analysis')
    if c.fetchone()[0] == 0:
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
            c.execute('''INSERT INTO analysis 
                        (company, buyer, matrix_cell, gpt_output) 
                        VALUES (?, ?, ?, ?)''', 
                     (data['company'], 
                      data['buyer'], 
                      data['matrix_cell'], 
                      data['gptOutput']))
    conn.commit()
    conn.close()

@app.get("/analysis")
def get_analysis():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT company, buyer, matrix_cell, gpt_output 
                 FROM analysis WHERE id = 1''')
    result = c.fetchone()
    conn.close()
    if result:
        return {
            "company": result[0],
            "buyer": result[1],
            "matrix_cell": result[2],
            "markdown": result[3]
        }
    return {"error": "No analysis found"}

@app.post("/analysis")
def update_analysis(update: UpdateRequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get current content
    c.execute('SELECT gpt_output FROM analysis WHERE id = 1')
    current_text = c.fetchone()[0]
    
    # Update with new content
    updated_text = f"{current_text}\n\n{update.new_content}"
    c.execute('UPDATE analysis SET gpt_output = ? WHERE id = 1', (updated_text,))
    conn.commit()
    
    # Return updated content
    c.execute('SELECT company, buyer, matrix_cell, gpt_output FROM analysis WHERE id = 1')
    result = c.fetchone()
    conn.close()
    
    return {
        "company": result[0],
        "buyer": result[1],
        "matrix_cell": result[2],
        "markdown": result[3]
    }