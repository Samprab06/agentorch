import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

from agentorch import tracker


class TrackerTests(unittest.TestCase):
    def test_pr_lifecycle_uses_current_github_state(self):
        github = Mock()
        url = "https://github.com/acme/app/pull/12"
        pr = {"body": tracker.marker("ENG-12"), "state": "open", "merged": False, "html_url": url}
        github.get.return_value = pr
        with patch("agentorch.tracker.from_settings") as factory:
            backend = factory.return_value
            self.assertTrue(tracker.sync_pr(github, 12, {}))
            backend.update.assert_called_once_with("ENG-12", "in-review", url)
            backend.reset_mock()
            pr["state"] = "closed"
            self.assertFalse(tracker.sync_pr(github, 12, {}))
            backend.update.assert_not_called()
            pr["merged"] = True
            self.assertTrue(tracker.sync_pr(github, 12, {}))
            backend.update.assert_called_once_with("ENG-12", "done", url)
            pr["body"] += "\n" + tracker.marker("OTHER-1")
            with self.assertRaises(ValueError):
                tracker.sync_pr(github, 12, {})

    def test_command_bridge_can_read_and_update_a_non_linear_ticket(self):
        script = '''
import json, sys
request = json.load(sys.stdin)
assert request["id"] == "JIRA-7"
if request["operation"] == "read":
    print(json.dumps(dict(ok=True, id="JIRA-7", title="Hello", description="", url="https://jira.example/7")))
else:
    assert request["stage"] == "done" and request["status"] == "Released"
    assert request["pr_url"] == "https://github.com/acme/app/pull/7"
    print('{"ok": true}')
'''
        argv = json.dumps([sys.executable, "-c", script])
        with patch.dict(os.environ, {"AGENTORCH_TRACKER_COMMAND": argv}):
            backend = tracker.from_settings({
                "backend": "command", "states": {"in-progress": "Active", "in-review": "QA", "done": "Released"},
            })
            self.assertEqual(backend.read("JIRA-7")["title"], "Hello")
            backend.update("JIRA-7", "done", "https://github.com/acme/app/pull/7")

    def test_linear_uses_exact_mapping_and_does_not_regress_review(self):
        working = {"id": "active", "name": "In Development", "type": "started"}
        review = {"id": "review", "name": "In Review", "type": "started"}
        done = {"id": "done", "name": "Done", "type": "completed"}
        issue = {"id": "issue", "team": {"id": "team"}, "state": review}
        with patch("agentorch.linear.from_settings") as factory:
            client = factory.return_value
            client.issue.return_value = issue
            client.team.return_value = {"id": "team", "states": {"nodes": [working, review, done]}}
            backend = tracker.from_settings({
                "backend": "linear", "team": "ENG",
                "states": {"in-progress": "In Development", "in-review": "In Review", "done": "Done"},
            })
            backend.update("ENG-1", "in-progress")
            client.update_issue.assert_not_called()
            backend.update("ENG-1", "done", "https://github.com/acme/app/pull/1")
            client.attach.assert_called_once_with("issue", "https://github.com/acme/app/pull/1")
            client.update_issue.assert_called_once_with("issue", stateId="done")
            issue["team"]["id"] = "other"
            with self.assertRaisesRegex(ValueError, "different Linear team"):
                backend.update("OTHER-1", "done")
