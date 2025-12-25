from pydantic import BaseModel

from .project import Project


class Solution(BaseModel):
    projects: list[Project]
