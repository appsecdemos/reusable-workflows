import copy
import unittest
from unittest.mock import patch

from scripts.dependabot_automerge import Denied, evaluate


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.pr = {"number": 7, "state": "open", "draft": False,
                   "user": {"login": "dependabot[bot]", "id": 49699333, "type": "Bot"},
                   "head": {"sha": "head", "repo": {"id": 1}},
                   "base": {"sha": "base", "repo": {"id": 1}, "ref": "main"},
                   "mergeable": True, "merge_commit_sha": "merge"}
        self.check = {"name": "test", "status": "completed", "conclusion": "success",
                      "id": 2, "app": {"id": 15368}, "check_suite": {"id": 3},
                      "details_url": "https://github.com/a/b/actions/runs/4/job/5"}
        self.run = {"path": ".github/workflows/ci.yml", "event": "pull_request", "head_sha": "head",
                    "status": "completed", "conclusion": "success", "check_suite_id": 3}
        self.event = {"action": "completed", "workflow_run": {"event": "pull_request", "head_sha": "head"}}
        self.rules = [{"type": "required_status_checks", "parameters": {
            "strict_required_status_checks_policy": True,
            "required_status_checks": [{"context": "test", "integration_id": 15368}]}}]
        self.final_pr = None
        self.pr_reads = 0

    def api(self, path, token):
        if path == "/repos/a/b": return {"id": 1, "default_branch": "main"}
        if path.endswith("/pulls/7"):
            self.pr_reads += 1
            return self.final_pr if self.pr_reads > 1 and self.final_pr else self.pr
        if path.endswith("/branches/main"): return {"commit": {"sha": "base"}}
        if path.endswith("/commits/merge"): return {"parents": [{"sha": "base"}, {"sha": "head"}]}
        if path.endswith("/actions/runs/4"): return self.run
        raise AssertionError(path)

    def pages(self, path, token, key=None):
        if "/pulls?" in path: return [self.pr]
        if "/rules/branches/" in path: return self.rules
        if "/check-runs?" in path: return [self.check]
        raise AssertionError(path)

    def evaluate(self):
        with patch("scripts.dependabot_automerge.api", self.api), patch("scripts.dependabot_automerge.pages", self.pages):
            return evaluate("token", "a/b", self.event, {"test": ".github/workflows/ci.yml"})

    def test_success(self):
        self.assertEqual(self.evaluate()["number"], 7)

    def test_wrong_author_and_fork(self):
        for mutation in (lambda p: p["user"].update(id=1), lambda p: p["head"].update(repo={"id": 2})):
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.pr)
                mutation(self.pr)
                with self.assertRaises(Denied): self.evaluate()
                self.pr = original

    def test_stale_check_and_failed_checks(self):
        for key, value in (("head_sha", "old"), ("conclusion", "skipped"), ("status", "in_progress"),
                           ("path", ".github/workflows/untrusted.yml")):
            with self.subTest(key=key):
                original = self.run[key]
                self.run[key] = value
                with self.assertRaises(Denied): self.evaluate()
                self.run[key] = original

    def test_race_and_unknown_mergeability(self):
        self.final_pr = copy.deepcopy(self.pr)
        self.final_pr["head"]["sha"] = "new"
        with self.assertRaises(Denied): self.evaluate()
        self.final_pr = None
        self.pr_reads = 0
        self.pr["mergeable"] = None
        with self.assertRaises(Denied): self.evaluate()

    def test_rule_must_be_strict_and_from_actions(self):
        self.rules[0]["parameters"]["strict_required_status_checks_policy"] = False
        with self.assertRaises(Denied): self.evaluate()
        self.rules[0]["parameters"]["strict_required_status_checks_policy"] = True
        self.rules[0]["parameters"]["required_status_checks"][0]["integration_id"] = None
        with self.assertRaises(Denied): self.evaluate()


if __name__ == "__main__":
    unittest.main()
