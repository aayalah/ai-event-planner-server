import json
from typing import Dict, List, Optional, TypedDict
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, MessagesState, START, END
from opik.integrations.langchain import OpikTracer
from agents.prompts import prompts
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver


class State(MessagesState):
    event_profile: Optional[Dict[str, str]] = None
    vendor_list: Optional[Dict[str, str]] = None
    vendor_bids: Optional[Dict[str, str]] = None
    theme: str = ""
    final_report: str = ""
    step: str = "event_profile"
    awaiting_user: bool = False
    vendors_attendees_completed: bool 
    asked_theme: bool = False
    pass

class Theme(BaseModel):
    theme: str = Field(description="The theme for the event")

class EventProfile(BaseModel):
    event_type: str = Field(description="The type of event")
    formality: str = Field(description="Formality of event one of (casual, semi-forma, formal)")
    location: str = Field(description="The city the event will occur in")
    dates: list[str] = Field(description="The list of potential dates for the event")
    attendee_count: int = Field(description="The number of attendees")
    budget: int = Field(description="The maximum budget of the event.")


class EventPlanner_Iteration1:

    def __init__(self):
        self.llm = None
        self.graph = None
        self.tracer = None

    def should_pause(self, state: State) -> str:
        return "pause" if state["awaiting_user"] else "continue"

    def is_valid(self, event_profile: Dict[str,str]) -> bool:
        if not event_profile:
            return False
        
        required_keys = ["event_type", "formality", "location", "dates", "attendee_count", "budget"]
        for k in required_keys:
            if k not in event_profile or event_profile[k] in (None, "", []):
                return False
        return True

    def theme_selection(self, state: State):
        
        if not state["awaiting_user"] and "asked_theme" in state and state["asked_theme"]:
            print(state)
            # this is the *second* time through (resumed) → do NOT ask again
            return state

        chain = prompts["theme_suggestions"] | self.llm
        response = chain.invoke({"messages": state["messages"], "event_profile": json.dumps(state["event_profile"])})
        return {"messages": [f"Great — I’ve created your event profile. These are potential themes: {response.content}"], "awaiting_user": True, "asked_theme": True}


    def theme_confirmation(self, state: State):
        print("confirmation")
        chain = prompts["theme_interpreter"] | self.llm.with_structured_output(Theme)
        response = chain.invoke({"messages": state["messages"]})
        if response.theme != "":
            return {"theme": response.theme, "awaiting_user": False, "step": "vendors_and_attendees"}
        return {"messages": "I couldn’t tell the theme. Can you name it directly, e.g. 'rustic barn'?", "awaiting_user": True}


    def create_event_profile(self, state: State):
        print(state)
        chain = prompts["event_profile_parsing"] | self.llm.with_structured_output(EventProfile)
        response = chain.invoke({"user_requirements": state["messages"]})
        return {"event_profile": response.model_dump(),
                                  "messages": ["Great — I’ve created your event profile."],
                                  "step": "theme_selection"}

    def is_event_profile_complete(self, state: State) -> bool:
        if self.is_valid(state["event_profile"]):
            return True
        return False
    
    def is_theme_selected(self, state: State) -> bool:
        return "theme" in state and state["theme"] != ""

    def ask_for_vendors_and_attendees(self, state: State):
        return {"messages": [f"Great, the theme you have chosen is {state["theme"]}. Please attach a vendors and attendees list in csv format."], "awaiting_user": True}

    def confirm_if_vendors_and_attendees_added(self, state: State):
        return {"vendors_attendees_completed": True}

    def choose_step(self, state: State):

        if not "step" in state:
            return ""
        return state["step"]


    def initialize(self):
        self.llm = init_chat_model(model="gpt-5-mini", model_provider="openai", reasoning_effort="minimal")

        graph_builder = StateGraph(State)
        graph_builder.add_node("create_event_profile", self.create_event_profile)
        graph_builder.add_node("theme_selection", self.theme_selection)
        graph_builder.add_node("theme_confirmation", self.theme_confirmation)
        graph_builder.add_node("confirm_if_vendors_and_attendees_added", self.confirm_if_vendors_and_attendees_added)
        graph_builder.add_node("ask_for_vendors_and_attendees", self.ask_for_vendors_and_attendees)
        graph_builder.add_conditional_edges("create_event_profile", self.is_event_profile_complete, {True: "theme_selection", False: "create_event_profile"})
        graph_builder.add_conditional_edges(
            "theme_selection",
            self.should_pause,
            {"pause": END, "continue": "theme_confirmation"}
        )
        graph_builder.add_conditional_edges(
            "ask_for_vendors_and_attendees",
            self.should_pause,
            {"pause": END, "continue": "confirm_if_vendors_and_attendees_added"}
        )
        graph_builder.add_conditional_edges(
            "theme_confirmation",
            self.is_theme_selected,
            {True: "ask_for_vendors_and_attendees", False: END}
        )

        graph_builder.add_conditional_edges(START, self.choose_step, {"theme_selection": "theme_selection", "vendors_and_attendees": "ask_for_vendors_and_attendees", "": "create_event_profile", "create_event_profile": "create_event_profile"})
        checkpointer = MemorySaver()
        self.graph = graph_builder.compile(checkpointer=checkpointer)
        self.tracer = OpikTracer(graph=self.graph.get_graph(xray=True))
        
    def process_message(self, message: str, user_id: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        response = self.graph.invoke({
            "messages": [message],
            "awaiting_user": False,
        }, config={"callbacks": [self.tracer], "configurable": {"thread_id": user_id}})

        return response["messages"][-1].content