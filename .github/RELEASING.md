# Releasing CLDPM

This document describes how to release new versions of CLDPM.

## Release Workflows

CLDPM uses separate workflows for each package:

| Workflow | Tag Pattern | Package |
|----------|-------------|---------|
| `release-typescript.yml` | `ts-v*` | npm |
| `release-python.yml` | `py-v*` | PyPI |

## Prerequisites

### npm Trusted Publishing Setup

1. Go to [npmjs.com](https://www.npmjs.com) and sign in
2. Navigate to your package settings
3. Go to **Settings** → **Publishing access**
4. Configure GitHub Actions OIDC:
   - **Repository**: `transilienceai/cpm`
   - **Environment**: `npm`
   - **Workflow**: `.github/workflows/release-typescript.yml`

### PyPI Trusted Publishing Setup

1. Go to [pypi.org](https://pypi.org) and sign in
2. Navigate to your project: **Manage** → **Publishing**
3. Add a new trusted publisher:
   - **Owner**: `transilienceai`
   - **Repository**: `cpm`
   - **Workflow name**: `release-python.yml`
   - **Environment name**: `pypi`

### GitHub Environments

Create two environments in your GitHub repository settings:

1. **npm** - For npm publishing
2. **pypi** - For PyPI publishing

Go to **Settings** → **Environments** → **New environment**

## Release Process

### TypeScript Release

```bash
# Create and push tag
git tag ts-v0.2.0
git push origin ts-v0.2.0
```

This triggers `release-typescript.yml` which:
1. Builds and tests the TypeScript package
2. Publishes to npm with OIDC provenance
3. Creates a GitHub release with the tarball

### Python Release

```bash
# Create and push tag
git tag py-v0.2.0
git push origin py-v0.2.0
```

This triggers `release-python.yml` which:
1. Builds and tests the Python package
2. Publishes to PyPI using trusted publishing
3. Creates a GitHub release with wheel and source dist

### Manual Workflow Dispatch

You can also trigger releases manually:

1. Go to **Actions** → Select the workflow
2. Click **Run workflow**
3. Enter the version number (e.g., `0.2.0`)
4. Click **Run workflow**

## Tag Naming Convention

| Tag | Example | Package |
|-----|---------|---------|
| `ts-v*` | `ts-v0.2.0` | TypeScript (npm) |
| `py-v*` | `py-v0.2.0` | Python (PyPI) |

## Version Synchronization

Before releasing, update the version in the respective package file:

**Python** (`python/pyproject.toml`):
```toml
version = "0.2.0"
```

**TypeScript** (`typescript/package.json`):
```json
"version": "0.2.0"
```

Note: The workflows automatically update the version from the tag, so this is optional but recommended for consistency.

## Pre-release Versions

For pre-release versions, use semantic versioning:

```bash
# TypeScript alpha
git tag ts-v0.2.0-alpha.1
git push origin ts-v0.2.0-alpha.1

# Python beta
git tag py-v0.2.0-beta.1
git push origin py-v0.2.0-beta.1
```

Pre-releases are automatically marked as such in GitHub releases.

## Security Features

### npm
- **OIDC provenance**: Packages are signed with supply chain attestation
- **Environment protection**: Requires `npm` environment approval

### PyPI
- **Trusted publishing**: Uses OIDC, no API tokens stored
- **Environment protection**: Requires `pypi` environment approval

## Troubleshooting

### npm Publishing Fails

- Verify the `npm` environment exists in GitHub repository settings
- Check that OIDC is configured on npmjs.com
- Ensure `NPM_TOKEN` secret is set as fallback

### PyPI Publishing Fails

- Verify the `pypi` environment exists in GitHub repository settings
- Check that trusted publishing is configured on pypi.org
- Verify the workflow name matches exactly: `release-python.yml`

### Tag Already Exists

If a tag already exists and you need to re-release:

```bash
# Delete local tag
git tag -d ts-v0.2.0

# Delete remote tag
git push origin :refs/tags/ts-v0.2.0

# Create new tag
git tag ts-v0.2.0
git push origin ts-v0.2.0
```
