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

### Dependabot automerge

`dependabot_automerge.yml` considers open, same-repository Dependabot PRs targeting the default branch after a successful PR workflow completes. It verifies the triggering revision against the PR head and, when enabled, rechecks it before a direct squash merge guarded by that SHA. It never checks out PR code or downloads artifacts. GitHub enforces the required CI checks at merge time; this workflow does not inspect them. Dry run is the default and does not create an App token or attempt a merge.

Add a caller on the protected default branch. Replace the example workflow names with the **exact names** of both required CI workflows, and replace `<RELEASE>` with an exact SemVer release containing this workflow. Both workflows must trigger it so the last successful completion can retry the merge.

```yaml
name: Dependabot automerge
on:
  workflow_run:
    workflows: [Test, Dependency review]
    types: [completed]

permissions:
  contents: read
  pull-requests: read

jobs:
  automerge:
    uses: appsecdemos/reusable-workflows/.github/workflows/dependabot_automerge.yml@<RELEASE>
    with:
      dry_run: true
    secrets:
      app_client_id: ${{ secrets.AUTOMERGE_APP_CLIENT_ID }}
      app_private_key: ${{ secrets.AUTOMERGE_APP_PRIVATE_KEY }}
```

The caller explicitly passes the App secrets. Only after a PR passes the identity and revision checks, and only when dry run is disabled, the workflow creates a short-lived App token restricted to the caller repository with Contents write and Pull Requests read. The App merges; it does not approve the PR.

Before enabling writes, configure and verify **two separate rulesets** for the default branch:

1. Require CODEOWNER approval, with the App allowed to bypass this ruleset **only via pull requests**.
2. Require strict mandatory CI checks, with **no App bypass**. Include both CI workflows and ensure their checks are independently trustworthy.

Review the reusable workflow and publish a release separately, add the caller in dry-run mode, and inspect its logs on representative Dependabot PRs. Verify the rulesets and required check names before a later authorized change sets `dry_run: false`. The first workflow completion may attempt a merge while another check is pending; GitHub must reject it, and the next successful completion retries. The merge API protects the head SHA, but does not atomically guard against a base branch or target change between the final check and merge; protect target branches and rules accordingly.

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
