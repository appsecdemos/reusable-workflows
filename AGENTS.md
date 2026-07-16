# Repository Guidelines

- Keep reusable workflows simple, focused, and documented in `README.md`.
- Grant `GITHUB_TOKEN` only the minimum required permissions and avoid inheriting secrets unless necessary.
- Pin every external GitHub Action to a full 40-character commit SHA with its SemVer version in an inline comment:
  `uses: owner/action@<full-commit-sha> # vX.Y.Z`
- Validate changed YAML and embedded shell scripts, and run `git diff --check` before handing off changes.
- Never publish releases, move refs, push, or run workflows unless the user explicitly requests it.
