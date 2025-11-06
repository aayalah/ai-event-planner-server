from dotenv import load_dotenv
import csv
import io
import json
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Request, Depends, UploadFile, File, Form
from contextlib import asynccontextmanager
from schemas.query import PlannerQuery, ConceptsPayload, Concept, Vendor, VendorPayload
from agents.concepts import Concepts
from agents.vendors import Vendors
from typing import Dict, List, Optional, TypedDict
# from agents.iteration2 import EventPlanner_Iteration2

load_dotenv()

def get_concepts(request: Request) -> Concepts:
    return request.app.state.concepts

def get_vendors(request: Request) -> Vendors:
    return request.app.state.vendors

# def get_event_planner2(request: Request) -> EventPlanner_Iteration2:
#     return request.app.state.event_planner2

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...") 

    concepts = Concepts()
    concepts.initialize()

    vendors = Vendors()
    vendors.initialize()

    app.state.concepts = concepts
    app.state.vendors = vendors

    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "Hello World"}

# @app.post("/planner")
# def planner(request: PlannerQuery, event_planner: EventPlanner_Iteration1 = Depends(get_event_planner)):

#     response = event_planner.process_message(request.query)
#     return {"response": response}


# @app.post("/chat")
# async def chat(
#     message: str = Form(..., description="User's chat message"),
#     user_id: str = Form(..., description="User id"),
#     files: Optional[List[UploadFile]] = File(None),
#     event_planner: EventPlanner_Iteration1 = Depends(get_event_planner)
# ):

#     # file_data = {}
#     # if files:
#     #     for f in files:
#     #         if f.content_type == "text/csv":
#     #             file_data[Path(f.filename).stem] = await get_file_data(f)

#     user_message = f"{message}"

#     response = event_planner.process_message(user_message, user_id)

#     return {"message": response}





@app.post("/concepts", response_model=List[Concept])
async def concepts(user_id: str, payload: ConceptsPayload, concepts: Concepts= Depends(get_concepts)):
    
    json_str = payload.json()

    response = concepts.process_message(json_str, user_id)

    data = json.loads(response)  
    
    concepts = [Concept.model_validate(item) for item in data["concepts"]]

    return concepts



@app.post("/vendors", response_model=List[Vendor])
async def concepts(user_id: str, payload: VendorPayload, vendors: Vendors= Depends(get_vendors)):
    
    json_str = payload.json()

    response = vendors.process_message(json_str, user_id)

    data = json.loads(response)  
    
    concepts = [Vendor.model_validate(item) for item in data["vendors"]]

    return concepts


# async def get_file_data(file: UploadFile) -> str:
#     content = await file.read()

#     csv_string = content.decode("utf-8")

#     csv_string.strip()

#     reader = csv.DictReader(io.StringIO(csv_string))
#     data = [row for row in reader]

#     return json.dumps(data, indent=2)