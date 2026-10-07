from pydantic import BaseModel

class Addnotes(BaseModel):
    title:str
    notes:str