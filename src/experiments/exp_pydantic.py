
from pydantic import BaseModel


class Some(BaseModel):
    name: str
    value: int


instance = Some(name="example", value=42)
print(instance)  # Output: name='example' value=42
