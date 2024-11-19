# Analysis API

This API provides access to AI-generated analysis of potential acquisitions and allows for updates to the analysis.

## Setup

1. Install dependencies:

   ```bash
   pip install fastapi uvicorn
   ```

2. Run server:

   ```bash
   uvicorn main:app --reload
   ```

The API will be available at http://localhost:8000 with two endpoints:
- GET /analysis - Returns the current markdown
- POST /analysis - Updates the markdown with new content

# State file name in .env file

ANALYSIS_DB_PATH=analysis.db
# Replace with the path to the JSON file containing the analysis data
# e.g. ANALYSIS_DATA_JSON=config.json 
ANALYSIS_DATA_JSON=preppy.json

Right now the default is for preppy.json, but you can change it to any other JSON file that contains the analysis data. 

## Testing

You can test the API using curl:

### Basic GET request
curl http://localhost:8000/analysis

### Pretty print the JSON response
curl http://localhost:8000/analysis | json_pp

### With headers displayed
curl -i http://localhost:8000/analysis

### POST request

You can also add new insights to the analysis by sending a POST request.

This is an example of adding two new insights to the analysis:

```
curl -X POST http://localhost:8000/analysis \
  -H "Content-Type: application/json" \
  -d '{"new_content": "Google Classroom could leverage Preppy LLC'\''s educational content to enhance their platform."}'

curl -X POST http://localhost:8000/analysis \
  -H "Content-Type: application/json" \
  -d '{"new_content": "The synergy between both companies would create a 20% increase in market share."}'
```

where `<INSERT YOUR NEW INSIGHT HERE>` is the new insight you want to add to the analysis.

curl -X POST http://localhost:8000/analysis \
  -H "Content-Type: application/json" \
  -d '{"new_content": <INSERT YOUR NEW INSIGHT HERE>}'