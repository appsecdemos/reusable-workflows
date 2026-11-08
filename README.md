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

### Dependabot automerge (dry run)

`dependabot_automerge.yml` evaluates Dependabot PRs after a trusted CI workflow completes. It does not inspect dependency versions. It requires a same-repository PR against the default branch, the current GitHub-generated merge candidate, and successful GitHub Actions checks for every required status check in the active strict rulesets. Each required check must be bound to GitHub Actions in the ruleset and to a trusted workflow path in the caller's mapping. It rejects missing, skipped, failed, duplicate, stale, or ambiguous checks and reports the decision in the job log. It rechecks before a SHA-guarded squash merge. The default `dry_run: true` never requests an App token or writes to the repository.

The caller must use `workflow_run` from the protected default branch, subscribe to **both** CI workflows, and pass the exact check names shown in the ruleset. The names below are examples and must be verified against the actual check runs (reusable workflows can add job-name prefixes). Replace `<RELEASE>` with an exact SemVer release containing this workflow; no such release is created by this change.

```yaml
name: Dependabot automerge
on:
  workflow_run:
    workflows: [Deploy and Release, Dependency review]
    types: [completed]

permissions:
  actions: read
  checks: read
  contents: read
  pull-requests: read

jobs:
  automerge:
    uses: appsecdemos/reusable-workflows/.github/workflows/dependabot_automerge.yml@<RELEASE>
    with:
      dry_run: true
      trusted_checks: >-
        {"test":".github/workflows/publish_site.yml",
         "dependency-review / dependency-review":".github/workflows/dependency_review.yml"}
    secrets:
      app_client_id: ${{ secrets.AUTOMERGE_APP_CLIENT_ID }}
      app_private_key: ${{ secrets.AUTOMERGE_APP_PRIVATE_KEY }}
```

The workflow requires GitHub.com (it uses `job.workflow_repository` and `job.workflow_sha`). It checks out the reusable workflow's own trusted revision, not the caller or PR, and does not download artifacts. The caller's `GITHUB_TOKEN` is read-only as shown. Secrets are explicitly passed; an installation token is only created after eligibility when dry-run is disabled, restricted to the caller repository and Contents write, and revoked by the token action. The App needs Contents write and Pull Requests read installed; it does not submit an approval. Concurrent or changed PR state is rejected and the merge API receives the evaluated head SHA.

Before enabling merging, use **two separate active rulesets** targeting the default branch:

1. Require CODEOWNER review in a pull request ruleset. Give the App a **pull-request-only** bypass on this ruleset, after dry-run review.
2. Require all CI checks in a separate strict status-check ruleset, without an App bypass. Bind every required check to GitHub Actions. Keep the branch up to date before merging. This separate rule is essential because the merge API guards the head SHA, not the base SHA.

Keep the trusted workflow definitions and their check names protected from PR modification. A workflow path and GitHub Actions identity alone do not prove the code that produced a check was trusted: a PR that changes a CI workflow can influence its own results. Establish independently enforced trusted CI (for example, an organization-enforced required workflow) before allowing the App to bypass review. Confirm that the ruleset API returns the complete required-check set and that both CI runs report against the current test merge commit; unsupported check types, differently shaped API results, reruns producing duplicate check runs, or an unavailable test merge commit fail closed. Traditional branch-protection-only checks are not discovered by the ruleset API and must be migrated to the mandatory CI ruleset. The workflow does not verify ruleset bypass lists, so administrators must audit them before enabling writes.

Deployment: release this repository after review; add the caller above on the caller's default branch with the actual release tag, workflow names and check names; run and inspect dry-run decisions on representative PRs and stale/failed CI; configure and verify the separated rulesets and trusted CI; then, in a later authorized change, set `dry_run: false` and monitor the App's merge audit trail. No caller changes or bypass are made by this repository workflow.

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
