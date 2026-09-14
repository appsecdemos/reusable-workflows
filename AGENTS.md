# Repository Guidelines

- Keep reusable workflows simple, focused, and documented in `README.md`.
- Grant `GITHUB_TOKEN` only the minimum required permissions and avoid inheriting secrets unless necessary.
- Pin every external GitHub Action to a full 40-character commit SHA with its SemVer version in an inline comment:
  `uses: owner/action@<full-commit-sha> # vX.Y.Z`
- Validate changed YAML and embedded shell scripts, and run `git diff --check` before handing off changes.
- Never publish releases, move refs, push, or run workflows unless the user explicitly requests it.

## Agent provenance and authority

- Keep changes scoped to the requested task. Do not make unrelated cleanup changes.
- For commits materially assisted by an AI coding agent, add a `Co-authored-by:` trailer using the agent's provided identity. Do not invent an identity.
- For AI-assisted pull requests, append this metadata when known:

  ```text
  AI-Assisted-By: <tool or agent>
  AI-Model: <model>
  AI-Reasoning: <reasoning level>
  ```

- Omit unknown provenance fields rather than guessing them.
- Do not push, publish releases, move refs, merge pull requests, or change repository settings unless explicitly authorized.
