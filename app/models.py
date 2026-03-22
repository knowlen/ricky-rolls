from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class MatchupRequest(BaseModel):
    defender_id: int
    wins_control: Optional[int] = Field(None, ge=0)
    wins_ricky: Optional[int] = Field(None, ge=0)
    losses_control: Optional[int] = Field(None, ge=0)
    losses_ricky: Optional[int] = Field(None, ge=0)
    order_first: Optional[str] = Field(None, pattern=r"^(control|ricky)$")
    notes: Optional[str] = None


class OfficerMetaRequest(BaseModel):
    comp: Optional[str] = ""
    ricky_replaces: Optional[str] = ""


class DefenderRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: Optional[str] = ""
    comp: Optional[str] = ""
    trophies: Optional[int] = Field(None, ge=0)
