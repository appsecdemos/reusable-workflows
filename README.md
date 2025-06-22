# reusable-workflows

Reusable workflows for Dependabot/GitHub Advanced Security

## Workflows

This repository contains reusable GitHub Actions workflows for security and dependency management:

- **PR Dependency Review** - Reviews dependencies in pull requests using GitHub's dependency review action
- **SBOM Upload** - Generates Software Bill of Materials (SBOM) using Trivy

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
```r

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

Note that this means every PR will have a "skipped" check for `sbom-generation` due to the triggers. Dependancy Graph snapshots should only be uploaded on updates to your default branch.

## License

MIT License - see [LICENSE](LICENSE) for details.
