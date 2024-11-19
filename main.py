from fastapi import FastAPI, HTTPException
from contextlib import contextmanager, asynccontextmanager
from pydantic import BaseModel, Field, validator
import sqlite3
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get configuration from environment variables
DB_PATH = os.getenv('ANALYSIS_DB_PATH', 'analysis.db')  # fallback to default if not set
JSON_PATH = os.getenv('ANALYSIS_DATA_JSON', 'analysis_data.json')

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        yield conn
    except sqlite3.Error as e:
        raise DatabaseError(f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

class UpdateRequest(BaseModel):
    new_content: str = Field(..., min_length=1, max_length=5000)
    
    @validator('new_content')
    def validate_content(cls, v):
        if v.strip() == "":
            raise ValueError("Content cannot be empty or just whitespace")
        return v.strip()

class AnalysisError(Exception):
    """Base exception for analysis operations"""
    pass

class DatabaseError(AnalysisError):
    """Database operation errors"""
    pass

class ValidationError(AnalysisError):
    """Input validation errors"""
    pass

# Initialize database and load initial data
def init_db():
    try:
        with get_db_connection() as conn:
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
                try:
                    with open(JSON_PATH, 'r') as f:
                        data = json.load(f)
                        c.execute('''INSERT INTO analysis 
                                   (company, buyer, matrix_cell, gpt_output) 
                                   VALUES (?, ?, ?, ?)''', 
                                (data['company'], 
                                 data['buyer'], 
                                 data['matrix_cell'], 
                                 data['gptOutput']))
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error loading initial data: {str(e)}"
                    )
            conn.commit()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database initialization error: {str(e)}"
        )

@app.get("/analysis")
def get_analysis():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''SELECT company, buyer, matrix_cell, gpt_output 
                        FROM analysis WHERE id = 1''')
            result = c.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Analysis not found")
                
            return {
                "company": result[0],
                "buyer": result[1],
                "matrix_cell": result[2],
                "markdown": result[3]
            }
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/analysis")
def update_analysis(update: UpdateRequest):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Get current content
            c.execute('SELECT gpt_output FROM analysis WHERE id = 1')
            result = c.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Analysis not found")
                
            current_text = result[0]
            
            # Update with new content
            updated_text = f"{current_text}\n\n{update.new_content}"
            c.execute('UPDATE analysis SET gpt_output = ? WHERE id = 1', 
                     (updated_text,))
            conn.commit()
            
            # Return updated content
            c.execute('''SELECT company, buyer, matrix_cell, gpt_output 
                        FROM analysis WHERE id = 1''')
            result = c.fetchone()
            
            return {
                "company": result[0],
                "buyer": result[1],
                "matrix_cell": result[2],
                "markdown": result[3]
            }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")