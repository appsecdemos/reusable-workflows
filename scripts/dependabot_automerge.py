"""Evaluate a workflow_run without executing any pull request content."""
import json
import os
import re
import sys
import urllib.parse
import urllib.request


class Denied(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Denied(reason)


def api(path, token, method="GET", data=None):
    request = urllib.request.Request(
        os.environ.get("GITHUB_API_URL", "https://api.github.com") + path,
        data=None if data is None else json.dumps(data).encode(), method=method,
        headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def pages(path, token, key=None):
    items = []
    for page in range(1, 101):
        value = api(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}", token)
        batch = value if key is None else value[key]
        items.extend(batch)
        if len(batch) < 100:
            return items
    raise Denied("API pagination limit exceeded")


def evaluate(token, repository, event, trusted):
    root = "/repos/" + repository
    repo = api(root, token)
    trigger = event["workflow_run"]
    require(event.get("action") == "completed" and trigger["event"] == "pull_request",
            "trigger must be a completed pull_request workflow run")
    require(isinstance(trusted, dict) and trusted and all(
        isinstance(k, str) and isinstance(v, str) and v.startswith(".github/workflows/")
        and v.endswith((".yml", ".yaml")) for k, v in trusted.items()), "invalid trusted check mapping")
    candidates = [p for p in pages(root + "/pulls?state=open", token)
                  if p["head"]["sha"] == trigger["head_sha"]]
    require(len(candidates) == 1, "trigger does not identify exactly one open PR")
    pr = api(root + "/pulls/" + str(candidates[0]["number"]), token)
    print(json.dumps({"pr": pr["number"], "head": pr["head"]["sha"],
                      "base": pr["base"]["sha"], "merge_candidate": pr["merge_commit_sha"]}))
    require(pr["state"] == "open" and not pr["draft"], "PR is not open and ready")
    require(pr["user"]["login"] == "dependabot[bot]" and pr["user"]["id"] == 49699333
            and pr["user"]["type"] == "Bot", "PR author is not Dependabot")
    require(pr["head"]["repo"] is not None and pr["head"]["repo"]["id"] == repo["id"]
            and pr["base"]["repo"]["id"] == repo["id"] and pr["base"]["ref"] == repo["default_branch"],
            "PR origin or target is invalid")
    require(pr["head"]["sha"] == trigger["head_sha"], "PR head changed")
    require(pr["mergeable"] is True and pr["merge_commit_sha"], "mergeability is unknown or conflicts")
    base = api(root + "/branches/" + urllib.parse.quote(repo["default_branch"], safe=""), token)
    require(base["commit"]["sha"] == pr["base"]["sha"], "base branch changed")
    merge = api(root + "/commits/" + pr["merge_commit_sha"], token)
    require([p["sha"] for p in merge["parents"]] == [pr["base"]["sha"], pr["head"]["sha"]],
            "merge candidate parents do not match current base and head")
    rules = pages(root + "/rules/branches/" + urllib.parse.quote(repo["default_branch"], safe=""), token)
    status_rules = [r for r in rules if r["type"] == "required_status_checks"]
    require(status_rules and all(r["parameters"]["strict_required_status_checks_policy"] for r in status_rules),
            "strict required CI ruleset missing")
    required = [c for r in status_rules for c in r["parameters"]["required_status_checks"]]
    require(required and set(c["context"] for c in required) == set(trusted),
            "trusted check mapping differs from required ruleset checks")
    require(all(c.get("integration_id") == 15368 for c in required),
            "required checks must be restricted to GitHub Actions")
    checks = pages(root + "/commits/" + pr["merge_commit_sha"] + "/check-runs?filter=all", token, "check_runs")
    for name, workflow in trusted.items():
        matches = [c for c in checks if c["name"] == name]
        require(len(matches) == 1, "missing or ambiguous check: " + name)
        check = matches[0]
        print(json.dumps({"check": name, "status": check["status"], "conclusion": check["conclusion"],
                          "id": check["id"]}))
        require(check["status"] == "completed" and check["conclusion"] == "success"
                and check["app"]["id"] == 15368, "check is not a successful GitHub Actions check: " + name)
        # A check run's details URL binds it to an Actions workflow run.
        url = check.get("details_url") or ""
        match = re.fullmatch(r"https://github\.com/" + re.escape(repository) +
                             r"/actions/runs/(\d+)/job/\d+", url, re.IGNORECASE)
        require(match is not None, "check has no unambiguous Actions run: " + name)
        run = api(root + "/actions/runs/" + match.group(1), token)
        require(run["path"] in (workflow, workflow + "@refs/pull/" + str(pr["number"]) + "/merge")
                and run["event"] == "pull_request"
                and run["head_sha"] == pr["head"]["sha"] and run["status"] == "completed"
                and run["conclusion"] == "success" and run["check_suite_id"] == check["check_suite"]["id"],
                "check workflow or revision does not match: " + name)
    current = api(root + "/pulls/" + str(pr["number"]), token)
    require(current["state"] == "open" and not current["draft"] and current["mergeable"] is True
            and current["base"]["ref"] == repo["default_branch"]
            and current["base"]["repo"]["id"] == repo["id"]
            and current["head"]["repo"] is not None and current["head"]["repo"]["id"] == repo["id"]
            and current["head"]["sha"] == pr["head"]["sha"]
            and current["base"]["sha"] == pr["base"]["sha"]
            and current["merge_commit_sha"] == pr["merge_commit_sha"], "PR changed during evaluation")
    return pr


def main():
    token = os.environ["GH_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    try:
        with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
            event = json.load(f)
        pr = evaluate(token, repo, event, json.loads(os.environ["TRUSTED_CHECKS"]))
        merge_token = os.environ.get("MERGE_TOKEN")
        if merge_token:
            result = api(f"/repos/{repo}/pulls/{pr['number']}/merge", merge_token, "PUT",
                         {"sha": pr["head"]["sha"], "merge_method": "squash"})
            require(result.get("merged") is True, "merge API did not confirm merge")
            print("Decision: merged with squash")
        else:
            print("Decision: eligible; merge would be attempted (dry run)")
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
                f.write("eligible=true\n")
    except Denied as exc:
        print("Decision: denied: " + str(exc))
    except Exception as exc:
        print("Decision: denied: API error or uncertain state (" + type(exc).__name__ + ")")
        sys.exit(1)


if __name__ == "__main__":
    main()
