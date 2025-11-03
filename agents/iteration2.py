from langchain.chat_models import init_chat_model
from typing import Dict, List, Optional, TypedDict
from langgraph.prebuilt import ToolNode, create_react_agent, tools_condition
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END, MessagesState
from google.maps import places_v1
from google.type import latlng_pb2
from langchain.tools import tool  
import os
import json

class State(MessagesState):

class PlannerResponse:
    plan: str = Field(description="The plan for the event")

class EventPlanner_Iteration2:

    def __init__(self):
        self.llm = None
        self.graph = None
        self.placesAPI = None


    def create_plan(self, state: State) -> State:


        chain = prompts["event_planner"] | self.llm.with_structured_output(PlannerResponse)
        return {"messages": ["Plan created"]}
    

    async def react_agent(self, state: State):
        agent = create_react_agent(self.llm, tools=self.tools, prompt=prompts["AGENT_PROMPT"])
        response = await agent.ainvoke({"messages": state["messages"]})
        return {"messages": response["messages"]}
    

    def initialize(self):


        @tool("places_search", is_async=True)
        async def places_search(lat: float, long: float, query: str) -> str:
            """Google Places API Search - lets you search for places based on a text query and returns a list of places. Takes as input: the latitude as float, the longitude as float, and the query as a string."""
            center_point = latlng_pb2.LatLng(latitude=lat, longitude=long)
            circle_area = places_v1.types.Circle(
                center=center_point,
                radius=1000.0
            )
            location_bias = places_v1.SearchTextRequest.LocationBias(
                 circle=circle_area
            )
            search_query = query
            min_place_rating = 4.0
            request = self.placesAPI.SearchTextRequest(
                text_query=search_query,
                location_bias=location_bias,
                min_rating=min_place_rating,
                price_levels=[
                    places_v1.types.PRICE_LEVEL_MODERATE,
                    places_v1.types.PRICE_LEVEL_EXPENSIVE
                ]
            )
            fieldMask = "places.formattedAddress,places.displayName"

            response = await self.placesAPI.search_text(request=request, metadata=[("x-goog-fieldmask",fieldMask)])

            print(response)                     
            return ""


        @tool
        def get_web_search_results(query: str) -> str:
            """Web search tool. Searches the web for the answer to the query and return the search results."""
            results = self.search_tool.invoke({"query": query})

            formatted_results = []

            for result in results['results']:
                formatted_result = {
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "raw_content": result.get("raw_content", "")
                }
                formatted_results.append(formatted_result)

            formatted_json = "\n\n".join([
                json.dumps(result, indent=2)
                for result in formatted_results
            ])
                
            return formatted_json

        self.llm = init_chat_model(model="gpt-5-mini", model_provider="openai", reasoning_effort="minimal")
        self.placesAPI = places_v1.PlacesAsyncClient(
                # Instantiates the Places client, passing the API key
                client_options={"api_key": os.getenv("GOOGLE_API_KEY")}
            )
        
        self.tools = [places_search, get_web_search_results]

        graph_builder = StateGraph(State)
        graph_builder.add_node("agent", self.react_agent)
        graph_builder.add_edge(START, "agent")
        graph_builder.add_edge("agent", END)
        self.graph = graph_builder.compile()

        
    async def process_message(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        response = await self.graph.ainvoke({"messages": [message]})
        return response["messages"][-1].content