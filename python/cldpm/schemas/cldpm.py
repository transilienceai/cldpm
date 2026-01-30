"""Pydantic model for cldpm.json (root configuration)."""

from pydantic import BaseModel, Field


class CldpmConfig(BaseModel):
    """Root configuration for a CLDPM mono repo."""

    name: str = Field(..., description="Name of the mono repo")
    version: str = Field(default="1.0.0", description="Version of the mono repo")
    projects_dir: str = Field(
        default="projects",
        alias="projectsDir",
        description="Directory containing projects",
    )
    shared_dir: str = Field(
        default="shared",
        alias="sharedDir",
        description="Directory containing shared components",
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "name": "my-monorepo",
                "version": "1.0.0",
                "projectsDir": "projects",
                "sharedDir": "shared",
            }
        },
    }
