import os
os.environ["CREWAI_TRACKING"] = "false"
os.environ["PYTHONHTTPSVERIFY"] = "0"
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import yaml
import importlib

# Load environment variables from .env file
load_dotenv()

# Check if OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not found in environment variables. Please add it to the .env file.")

app = FastAPI(title="CrewAccess API")

# Define available crews
AVAILABLE_CREWS = [
    {"id": 1, "name": "marketing_crew", "description": "Access the marketing_crew functionality"},
    {"id": 2, "name": "sales_crew", "description": "Access the sales_crew functionality"}
]

# Define request model for running a crew
class CrewRunRequest(BaseModel):
    topic: str

def get_crew_module(crew_id: int):
    """Get the appropriate crew module based on the crew_id"""
    print("get the crew")
    crew_modules = {
        1: ("crews.marketing.marketing", "MarketingCrew"),
        2: ("crews.sales.sales", "SalesCrew")
    }
    
    if crew_id not in crew_modules:
        return None
    
    module_path, class_name = crew_modules[crew_id]
    try:
        module = importlib.import_module(module_path)
        crew_class = getattr(module, class_name)
        return crew_class
    except (ImportError, AttributeError) as e:
        print(f"Error loading crew module: {e}")
        return None

@app.get("/")
async def root():
    """Root endpoint that provides information about the API"""
    print("main root")
    crew_list = [f"{crew['id']}: {crew['name']}" for crew in AVAILABLE_CREWS]
    return {
        "message": "Welcome to CrewAccess API",
        "available_crews": crew_list,
        "usage": "To run a crew, send a POST request to: /crew/{crew_id}/run with a JSON body containing the topic"
    }

@app.get("/crews")
async def list_crews():
    print("show all crew loaded")
    """List all available crews"""
    return {"crews": AVAILABLE_CREWS}

@app.get("/crews/{crew_id}")
async def crew_details(crew_id: int):
    print("show particular crew")
    """Showing Crew details"""
    crew_info = next((crew for crew in AVAILABLE_CREWS if crew["id"] == crew_id), None)
    if not crew_info:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": f"No crew found with ID {crew_id}"
            }
        )
    return crew_info

@app.post("/crew/{crew_id}/run")
async def run_crew(crew_id: int, request: CrewRunRequest):
    """Run a specific crew with the topic provided in the request body"""
    print(f"Running crew {crew_id} with topic: {request.topic}")
    
    # Check if crew_id is valid
    crew_ids = [crew["id"] for crew in AVAILABLE_CREWS]
    if crew_id not in crew_ids:
        crew_list = [f"{crew['id']}: {crew['name']}" for crew in AVAILABLE_CREWS]
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": f"No crew assigned for ID {crew_id}",
                "available_crews": crew_list
            }
        )
    
    # Get the appropriate crew module
    crew_class = get_crew_module(crew_id)
    if not crew_class:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to load crew module for ID {crew_id}"
            }
        )
    
    try:
        # Instantiate and run the crew
        crew_instance = crew_class(request.topic)
        result = crew_instance.run()
        
        return {
            "status": "success",
            "crew_id": crew_id,
            "topic": request.topic,
            "result": result
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error executing crew: {str(e)}"
            }
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)