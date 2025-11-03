from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager
from schemas.query import PlannerQuery
from agents.iteration1 import EventPlanner_Iteration1
from agents.iteration2 import EventPlanner_Iteration2

load_dotenv()

def get_event_planner(request: Request) -> EventPlanner_Iteration1:
    return request.app.state.event_planner

def get_event_planner2(request: Request) -> EventPlanner_Iteration2:
    return request.app.state.event_planner2

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...") 
    event_planner = EventPlanner_Iteration1()
    event_planner.initialize()

    event_planner_2 = EventPlanner_Iteration2()
    event_planner_2.initialize()

    app.state.event_planner = event_planner
    app.state.event_planner2 = event_planner_2

    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.post("/planner")
def planner(request: PlannerQuery, event_planner: EventPlanner_Iteration1 = Depends(get_event_planner2)):

    response = event_planner.process_message(request.query)
    return {"response": response}