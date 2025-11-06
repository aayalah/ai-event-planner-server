import json
from typing import Dict, List, Optional, TypedDict
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, MessagesState, START, END
from opik.integrations.langchain import OpikTracer
from agents.prompts import prompts
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from schemas.query import PlannerQuery, ConceptsPayload, Concept

class State(MessagesState):
    pass

class ConceptsResponse(BaseModel):
    concepts: List[Concept] =  Field(description="The list of concepts.")


class Concepts:

    def __init__(self):
        self.llm = None
        self.graph = None
        self.tracer = None

    def concepts_suggestions(self, state: State):

        chain = prompts["concept_suggestions"] | self.llm.with_structured_output(ConceptsResponse)
        response = chain.invoke({"messages": state["messages"]})
        print(response)
        return {"messages": [response.json()]}

    def initialize(self):
        self.llm = init_chat_model(model="gpt-5-mini", model_provider="openai", reasoning_effort="minimal")

        graph_builder = StateGraph(State)
        graph_builder.add_node("concepts_suggestions", self.concepts_suggestions)
        graph_builder.add_edge(START, "concepts_suggestions")
        graph_builder.add_edge("concepts_suggestions", END)

        checkpointer = MemorySaver()
        self.graph = graph_builder.compile(checkpointer=checkpointer)
        self.tracer = OpikTracer(graph=self.graph.get_graph(xray=True))
        
    def process_message(self, message: str, user_id: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        response = self.graph.invoke({
            "messages": [message],
        }, config={"callbacks": [self.tracer], "configurable": {"thread_id": user_id}})

        return response["messages"][-1].content