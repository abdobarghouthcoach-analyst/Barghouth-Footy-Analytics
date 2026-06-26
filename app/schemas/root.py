from pydantic import BaseModel


class RootResponse(BaseModel):
    app: str
    status: str
