from pydantic import BaseModel, Field
from typing import List

class MoleculeRequest(BaseModel):
    atoms: List[str] = Field(..., min_length=1, max_length=6, description="List of atomic symbols, e.g., ['Si', 'O', 'O']")
