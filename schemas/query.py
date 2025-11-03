from pydantic import BaseModel

class PlannerQuery(BaseModel):
    query: str


class PlannerReponse(BaseModel):
    plan: str