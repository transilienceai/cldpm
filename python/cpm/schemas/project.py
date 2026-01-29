"""Pydantic model for project.json (project configuration)."""

from typing import Optional

from pydantic import BaseModel, Field


class ProjectDependencies(BaseModel):
    """Dependencies for a project."""

    skills: list[str] = Field(default_factory=list, description="List of skill names")
    agents: list[str] = Field(default_factory=list, description="List of agent names")
    hooks: list[str] = Field(default_factory=list, description="List of hook names")
    rules: list[str] = Field(default_factory=list, description="List of rule names")


class ProjectConfig(BaseModel):
    """Configuration for a CPM project."""

    name: str = Field(..., description="Name of the project")
    description: Optional[str] = Field(
        default=None, description="Description of the project"
    )
    dependencies: ProjectDependencies = Field(
        default_factory=ProjectDependencies,
        description="Project dependencies on shared components",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
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
