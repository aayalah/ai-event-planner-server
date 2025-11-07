from pydantic import BaseModel
from typing import Dict, List, Optional, TypedDict

class PlannerQuery(BaseModel):
    query: str


class PlannerReponse(BaseModel):
    plan: str


class EventProfile(BaseModel):
    description: str
    min_budget: int
    max_budget: int
    min_guests: int
    max_guests: int
    event_datetime: str
    must_haves: List[str]
    nice_to_haves: List[str]
    things_to_avoid: List[str]
    special_needs: str
    restrictions: str
    concept: Optional[str] = ""

class ConceptsPayload(BaseModel):
    event_ideas: str
    event_profile: EventProfile
    user_feedback: Optional[str] = ""

class Concept(BaseModel):
    name: str
    description: str

class VendorPayload(BaseModel):
    event_profile: EventProfile
    user_feedback: Optional[str] = ""


class Ideas(BaseModel):
    name: str
    explanation: str

class Vendor(BaseModel):
    category: str
    description: str
    ideas: List[Ideas]