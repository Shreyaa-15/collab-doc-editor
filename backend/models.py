from pydantic import BaseModel
from typing import Optional

class CreateDocument(BaseModel):
    title: str
    owner: str

class OperationPayload(BaseModel):
    doc_id: str
    user_id: str
    revision: int
    ops: list[dict]        # list of {type, pos, chars, length}

class DocumentResponse(BaseModel):
    id: str
    title: str
    owner: str
    content: str
    revision: int