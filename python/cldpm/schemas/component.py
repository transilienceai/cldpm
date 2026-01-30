"""Pydantic schema for component metadata."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ComponentDependencies(BaseModel):
    """Dependencies for a component."""

    skills: list[str] = Field(default_factory=list)
    agents: list[str] = Field(default_factory=list)
    hooks: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)


class ComponentMetadata(BaseModel):
    """Metadata for a shared component (skill, agent, hook, rule)."""

    model_config = ConfigDict(extra="allow")

    name: str
    description: Optional[str] = None
    dependencies: ComponentDependencies = Field(default_factory=ComponentDependencies)
