# reusable-workflows

Reusable GitHub Actions workflows for narrowly scoped security and release policy. Application build, test, artifact, and deployment steps remain in each consuming repository.

## Workflows

### Semantic release

`semantic_release.yml` creates a semantic-version tag and GitHub Release for the caller repository. It checks out the caller repository at `github.sha` with complete history before it performs Git or GitHub operations.

An existing `vX.Y.Z` baseline tag is required; the workflow fails clearly if none exists. It never updates floating major-version branches.

With no `release_type` input, the current Conventional Commit determines the increment:

- `type!:` or `type(scope)!:`, or `BREAKING CHANGE:` anywhere in the message: major
- `feat:` or `feat(scope):`: minor
- All other commits: patch

It is idempotent: a valid version tag already pointing at `github.sha` exits successfully when its release exists, or creates only the missing GitHub Release when it does not.

```yaml
name: Release

on:
  push:
    branches: [main]

jobs:
  release:
    permissions:
      contents: write
    uses: appsecdemos/reusable-workflows/.github/workflows/semantic_release.yml@v1.3.0
```

To override inference, pass `release_type: major`, `minor`, or `patch`. Consumers may use an exact trusted first-party SemVer release tag such as `@v1.3.0`; do not use mutable `@main` or floating `@v1` references.

### PR dependency review

`pr_dependency_review.yml` runs GitHub's dependency-review action for pull requests. It uses `contents: read`, SHA-pinned actions, and a checkout without persisted credentials.

```yaml
name: Dependency review

on:
  pull_request:

permissions:
  contents: read

jobs:
  dependency-review:
    uses: appsecdemos/reusable-workflows/.github/workflows/pr_dependency_review.yml@v1.3.0
```

No inherited secrets are required.

### SBOM upload

`sbom_upload.yml` generates a Software Bill of Materials (SBOM) using Trivy and submits it to the repository's [Dependency Graph](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph). The caller must grant `contents: write`.

```yaml
name: Generate SBOM

on:
  push:
    branches: [main]

jobs:
  sbom:
    permissions:
      contents: write
    uses: appsecdemos/reusable-workflows/.github/workflows/sbom_upload.yml@v1.3.0
```

## License

MIT License - see [LICENSE](LICENSE) for details.
