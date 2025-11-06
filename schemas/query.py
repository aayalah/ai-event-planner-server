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
    concept: str

class ConceptsPayload(BaseModel):
    event_ideas: str
    event_profile: EventProfile

class Concept(BaseModel):
    name: str
    description: str
    location_ideas: str

class VendorPayload(BaseModel):
    event_profile: EventProfile


class Vendor(BaseModel):
    name: str
    category: str
    service: str
    price: float
    email: str