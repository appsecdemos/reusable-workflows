# reusable-workflows

Reusable GitHub Actions workflows for security, dependency management, and releases.

## Workflows

This repository contains the following reusable workflows:

- **PR Dependency Review** - Reviews dependencies in pull requests using GitHub's dependency review action
- **SBOM Upload** - Generates Software Bill of Materials (SBOM) using Trivy
- **Auto Release** - Creates SemVer releases and updates the floating major branch

## Usage

### PR Dependency Review

Use this workflow to automatically review dependencies in pull requests and identify potential security vulnerabilities.

```yaml
name: PR Security Review

on:
  pull_request:
    branches: [ main ]

jobs:
  dependency-review:
    uses: appsecdemos/reusable-workflows/.github/workflows/pr_dependency_review.yml@v1
    secrets: inherit
```

### SBOM Upload

Use this workflow to generate an SBOM (Software Bill of Materials) to your repo's [Dependency Graph](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph) using Trivy.

```yaml
name: Generate SBOM

on:
  push:
    branches: [ main ]
  release:
    types: [ published ]

jobs:
  sbom:
    uses: appsecdemos/reusable-workflows/.github/workflows/sbom_upload.yml@v1
    secrets: inherit
```

### Auto Release

Use this workflow with an existing `vX.Y.Z` tag to release automatically from Conventional Commits (`!` or `BREAKING CHANGE:` for major, `fix:` for patch, and everything else for minor); callers can pass `release_type` to select major, minor, or patch explicitly.

```yaml
name: Release

on:
  push:
    branches: [ main ]

jobs:
  release:
    permissions:
      contents: write
    uses: appsecdemos/reusable-workflows/.github/workflows/auto_release.yml@v1
```

### Combined Example

You can also combine workflows in a single workflow file:

```yaml
name: Security Workflows

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  dependency-review:
    if: github.event_name == 'pull_request'
    uses: appsecdemos/reusable-workflows/.github/workflows/pr_dependency_review.yml@v1
    secrets: inherit

  sbom-generation:
    if: github.event_name == 'push'
    uses: appsecdemos/reusable-workflows/.github/workflows/sbom_upload.yml@v1
    secrets: inherit
```

Note that this means every PR will have a "skipped" check for `sbom-generation` due to the triggers. Dependency Graph snapshots should only be uploaded on updates to your default branch.

## License

MIT License - see [LICENSE](LICENSE) for details.
