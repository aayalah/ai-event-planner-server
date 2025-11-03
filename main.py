from fastapi import FastAPI 
from schemas.query import Query


app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.post("/planner")
def planner(request: Query):
    print(request.query)
    return {"message": "Hello World"}