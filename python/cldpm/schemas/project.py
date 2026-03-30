"""Pydantic model for project.json (project configuration)."""

import re
from typing import Optional

from pydantic import BaseModel, Field, model_validator


def to_kebab_case(value: str) -> str:
    """Convert a string to kebab-case."""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.strip().lower())).strip(
        "-"
    )


class ProjectDependencies(BaseModel):
    """Dependencies for a project."""

    skills: list[str] = Field(default_factory=list, description="List of skill names")
    agents: list[str] = Field(default_factory=list, description="List of agent names")
    hooks: list[str] = Field(default_factory=list, description="List of hook names")
    rules: list[str] = Field(default_factory=list, description="List of rule names")


class ProjectConfig(BaseModel):
    """Configuration for a CLDPM project."""

    id: str = Field(
        default="",
        description="Stable, filesystem-safe project identifier (kebab-case)",
    )
    name: str = Field(..., description="Name of the project")
    description: Optional[str] = Field(
        default=None, description="Description of the project"
    )
    dependencies: ProjectDependencies = Field(
        default_factory=ProjectDependencies,
        description="Project dependencies on shared components",
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "ProjectConfig":
        """Ensure id is always present using name-derived fallback."""
        if not self.id or not self.id.strip():
            self.id = to_kebab_case(self.name)
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "my-project",
                "name": "my-project",
                "description": "Project description",
                "dependencies": {
                    "skills": ["my-skill"],
                    "agents": ["my-agent"],
                    "hooks": ["my-hook"],
                    "rules": ["my-rule"],
                },
            }
        },
    }
