import os
os.environ["CREWAI_TRACKING"] = "false"
os.environ["PYTHONHTTPSVERIFY"] = "0"
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
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
    {"id": 0, "name": "marketing_crew", "description": "Access the marketing_crew functionality"},
    {"id": 1, "name": "sales_crew", "description": "Access the sales_crew functionality"}
]

def get_crew_module(crew_id: int):
    """Get the appropriate crew module based on the crew_id"""
    print("get the crew")
    crew_modules = {
        0: ("crews.marketing.marketing", "MarketingCrew"),
        1: ("crews.sales.sales", "SalesCrew")
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
        "usage": "To run a crew, use: /run_crew/{crew_id}?topic=your_topic"
    }

@app.get("/crews")
async def list_crews():
    print("show all crew loaded")
    """List all available crews"""
    return {"crews": AVAILABLE_CREWS}

@app.get("/run_crew/{crew_id}")
async def run_crew(crew_id: int, topic: Optional[str] = None):
    """Run a specific crew with the given topic"""
    # Check if crew_id is valid
    print("nature of the request id")
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
    
    # If no topic is provided, return the crew information
    if not topic:
        # Find the specific crew information
        crew_info = next((crew for crew in AVAILABLE_CREWS if crew["id"] == crew_id), None)
        return crew_info
    
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
        crew_instance = crew_class(topic)
        result = crew_instance.run()
        
        return {
            "status": "success",
            "crew_id": crew_id,
            "topic": topic,
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