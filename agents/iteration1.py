from langchain.chat_models import init_chat_model
from typing import Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    query: str
    response: str

class PlannerResponse(BaseModel):
    plan: str = Field(description="The plan for the event")

class EventPlanner_Iteration1(BaseModel):

    def __init__(self):
        self.llm = None
        self.graph = None

    def create_plan(self, state: State) -> State:


        chain = prompts["event_planner"] | self.llm.with_structured_output(PlannerResponse)
        return {"response": "Plan created"}


    def initialize(self):
        self.llm = init_chat_model(model="gpt-5-mini", model_provider="openai", reasoning_effort="minimal")

        graph_builder = StateGraph(State)
        graph_builder.add_node("planner", self.create_plan)
        graph_builder.add_edge(START, "planner")
        graph_builder.add_edge("planner", END)
        self.graph = graph_builder.compile()
        
    def process_message(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        response = self.graph.invoke({"query": message})
        return response["response"]