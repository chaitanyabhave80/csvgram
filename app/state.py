from dataclasses import dataclass, field
from typing import Optional

from .config import MISSING_VALUE


@dataclass
class Project:
    columns: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    missing_value: str = MISSING_VALUE
    mode: Optional[str] = None
    current_row: list[str] = field(default_factory=list)
    column_index: int = 0


class SessionStore:
    def __init__(self):
        self._projects: dict[int, Project] = {}

    def get(self, user_id: int) -> Project:
        return self._projects.setdefault(user_id, Project())

    def reset(self, user_id: int) -> Project:
        project = Project()
        self._projects[user_id] = project
        return project

    def delete(self, user_id: int) -> None:
        self._projects.pop(user_id, None)
