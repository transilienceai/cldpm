"""Implementation of cldpm link command."""

import json
from pathlib import Path
from typing import Optional

import click

from ..core.config import load_cldpm_config, load_component_metadata
from ..schemas import ComponentDependencies, ComponentMetadata
from ..utils.fs import find_repo_root
from ..utils.output import console, print_error, print_success, print_warning


def parse_component_spec(spec: str) -> tuple[str, str]:
    """Parse a component specification into type and name.

    Args:
        spec: Component spec like "skill:my-skill" or "skills:my-skill".

    Returns:
        Tuple of (component_type, component_name).

    Raises:
        ValueError: If format is invalid.
    """
    if ":" not in spec:
        raise ValueError(
            f"Invalid component format: '{spec}'. Use 'type:name' format (e.g., skill:my-skill)"
        )

    comp_type, comp_name = spec.split(":", 1)

    # Normalize type to plural form
    type_map = {
        "skill": "skills",
        "skills": "skills",
        "agent": "agents",
        "agents": "agents",
        "hook": "hooks",
        "hooks": "hooks",
        "rule": "rules",
        "rules": "rules",
    }

    if comp_type not in type_map:
        raise ValueError(f"Unknown component type: {comp_type}")

    return type_map[comp_type], comp_name


def load_component_metadata_full(
    comp_type: str, comp_name: str, repo_root: Path
) -> tuple[Optional[ComponentMetadata], Path]:
    """Load component metadata and return the metadata file path.

    Args:
        comp_type: Component type (skills, agents, hooks, rules).
        comp_name: Component name.
        repo_root: Path to the repo root.

    Returns:
        Tuple of (ComponentMetadata or None, metadata_file_path).
    """
    cldpm_config = load_cldpm_config(repo_root)
    shared_dir = repo_root / cldpm_config.shared_dir

    component_path = shared_dir / comp_type / comp_name
    if not component_path.exists():
        return None, component_path

    singular_type = comp_type.rstrip("s")
    metadata_path = component_path / f"{singular_type}.json"

    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            data = json.load(f)
        return ComponentMetadata.model_validate(data), metadata_path

    # Return minimal metadata if no file exists
    return ComponentMetadata(name=comp_name), metadata_path


def save_component_metadata(metadata: ComponentMetadata, metadata_path: Path) -> None:
    """Save component metadata to a JSON file.

    Args:
        metadata: The ComponentMetadata to save.
        metadata_path: Path to the metadata file.
    """
    data = {"name": metadata.name}

    if metadata.description:
        data["description"] = metadata.description

    deps = metadata.dependencies
    if deps.skills or deps.agents or deps.hooks or deps.rules:
        data["dependencies"] = {}
        if deps.skills:
            data["dependencies"]["skills"] = deps.skills
        if deps.agents:
            data["dependencies"]["agents"] = deps.agents
        if deps.hooks:
            data["dependencies"]["hooks"] = deps.hooks
        if deps.rules:
            data["dependencies"]["rules"] = deps.rules

    # Preserve any extra fields from the original
    with open(metadata_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


@click.command()
@click.argument("dependencies")
@click.option("--to", "-t", "target", required=True, help="Target component (type:name)")
def link(dependencies: str, target: str) -> None:
    """Link dependencies to an existing shared component.

    Adds one or more components as dependencies of another component.
    This updates the target component's metadata file.

    \b
    DEPENDENCIES format:
      type:name              - Single dependency
      type:a,type:b,type:c   - Multiple dependencies

    \b
    TARGET format:
      type:name              - The component to add dependencies to

    \b
    Examples:
      cldpm link skill:base-utils --to skill:advanced-review
      cldpm link rule:security --to agent:security-audit
      cldpm link skill:scan,skill:review,rule:security --to agent:auditor
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        print_error("Not in a CLDPM mono repo. Run 'cldpm init' first.")
        raise SystemExit(1)

    # Parse target component
    try:
        target_type, target_name = parse_component_spec(target)
    except ValueError as e:
        print_error(str(e))
        raise SystemExit(1)

    # Load target component metadata
    target_metadata, metadata_path = load_component_metadata_full(
        target_type, target_name, repo_root
    )

    if target_metadata is None:
        print_error(f"Target component not found: {target_type}/{target_name}")
        raise SystemExit(1)

    # Ensure metadata file exists
    if not metadata_path.exists():
        # Create minimal metadata file
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        target_metadata = ComponentMetadata(
            name=target_name,
            dependencies=ComponentDependencies(),
        )

    # Parse dependency specifications
    dep_specs = [d.strip() for d in dependencies.split(",") if d.strip()]

    if not dep_specs:
        print_error("No dependencies specified")
        raise SystemExit(1)

    # Load CLDPM config to check if dependencies exist
    cldpm_config = load_cldpm_config(repo_root)
    shared_dir = repo_root / cldpm_config.shared_dir

    # Process each dependency
    added = []
    already_linked = []
    not_found = []

    for dep_spec in dep_specs:
        try:
            dep_type, dep_name = parse_component_spec(dep_spec)
        except ValueError as e:
            print_error(str(e))
            raise SystemExit(1)

        # Check if dependency exists
        dep_path = shared_dir / dep_type / dep_name
        if not dep_path.exists():
            not_found.append(f"{dep_type}/{dep_name}")
            continue

        # Get the appropriate dependency list
        dep_list = getattr(target_metadata.dependencies, dep_type)

        # Check if already linked
        if dep_name in dep_list:
            already_linked.append(f"{dep_type}/{dep_name}")
            continue

        # Add dependency
        dep_list.append(dep_name)
        added.append(f"{dep_type}/{dep_name}")

    # Save updated metadata
    if added:
        save_component_metadata(target_metadata, metadata_path)
        print_success(f"Linked dependencies to {target_type}/{target_name}")
        for dep in added:
            console.print(f"  [green]✓[/green] {dep}")

    if already_linked:
        print_warning("Already linked:")
        for dep in already_linked:
            console.print(f"  [dim]-[/dim] {dep}")

    if not_found:
        print_error("Dependencies not found:")
        for dep in not_found:
            console.print(f"  [red]✗[/red] {dep}")
        if not added:
            raise SystemExit(1)


@click.command()
@click.argument("dependencies")
@click.option("--from", "-f", "target", required=True, help="Target component (type:name)")
def unlink(dependencies: str, target: str) -> None:
    """Remove dependencies from an existing shared component.

    Removes one or more components as dependencies of another component.
    This updates the target component's metadata file.

    \b
    DEPENDENCIES format:
      type:name              - Single dependency
      type:a,type:b,type:c   - Multiple dependencies

    \b
    TARGET format:
      type:name              - The component to remove dependencies from

    \b
    Examples:
      cldpm unlink skill:base-utils --from skill:advanced-review
      cldpm unlink rule:security --from agent:security-audit
      cldpm unlink skill:scan,skill:review --from agent:auditor
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        print_error("Not in a CLDPM mono repo. Run 'cldpm init' first.")
        raise SystemExit(1)

    # Parse target component
    try:
        target_type, target_name = parse_component_spec(target)
    except ValueError as e:
        print_error(str(e))
        raise SystemExit(1)

    # Load target component metadata
    target_metadata, metadata_path = load_component_metadata_full(
        target_type, target_name, repo_root
    )

    if target_metadata is None:
        print_error(f"Target component not found: {target_type}/{target_name}")
        raise SystemExit(1)

    if not metadata_path.exists():
        print_error(f"No metadata file for: {target_type}/{target_name}")
        raise SystemExit(1)

    # Parse dependency specifications
    dep_specs = [d.strip() for d in dependencies.split(",") if d.strip()]

    if not dep_specs:
        print_error("No dependencies specified")
        raise SystemExit(1)

    # Process each dependency
    removed = []
    not_linked = []

    for dep_spec in dep_specs:
        try:
            dep_type, dep_name = parse_component_spec(dep_spec)
        except ValueError as e:
            print_error(str(e))
            raise SystemExit(1)

        # Get the appropriate dependency list
        dep_list = getattr(target_metadata.dependencies, dep_type)

        # Check if linked
        if dep_name not in dep_list:
            not_linked.append(f"{dep_type}/{dep_name}")
            continue

        # Remove dependency
        dep_list.remove(dep_name)
        removed.append(f"{dep_type}/{dep_name}")

    # Save updated metadata
    if removed:
        save_component_metadata(target_metadata, metadata_path)
        print_success(f"Unlinked dependencies from {target_type}/{target_name}")
        for dep in removed:
            console.print(f"  [green]✓[/green] {dep}")

    if not_linked:
        print_warning("Not linked (skipped):")
        for dep in not_linked:
            console.print(f"  [dim]-[/dim] {dep}")
