from typing import Optional
from pydantic import BaseModel


class Environment(BaseModel):
    working_directory: Optional[str] = None
    environment_directory: Optional[str] = None
