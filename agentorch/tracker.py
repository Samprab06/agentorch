"""Optional ticket integrations for the GitHub board and PR workflow."""
from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any, Dict, Optional

from agentorch.config import _argv

STAGES = ("in-progress", "in-review", "done")
REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")
MARKER = re.compile(r"^<!-- agentorch:ticket=(\S+) -->$", re.MULTILINE)


def marker(reference: str) -> str:
    if not REFERENCE.fullmatch(reference):
        raise ValueError("Invalid tracker ticket ID")
    return f"<!-- agentorch:ticket={reference} -->"


def linked_ticket(body: Optional[str]) -> Optional[str]:
    matches = MARKER.findall(body or "")
    if not matches:
        return None
    if len(matches) != 1 or not REFERENCE.fullmatch(matches[0]):
        raise ValueError("Expected exactly one valid AgentOrch ticket marker")
    return matches[0]


class CommandTracker:
    """Run an operator-provided bridge, with one JSON request per invocation."""

    def __init__(self, states: dict):
        self.argv = _argv(json.loads(os.environ.get("AGENTORCH_TRACKER_COMMAND", "null")),
                          "AGENTORCH_TRACKER_COMMAND")
        if self.argv is None:
            raise ValueError("Set AGENTORCH_TRACKER_COMMAND to a JSON argv array")
        self.states = states

    def call(self, operation: str, reference: str, **fields: Any) -> Dict[str, Any]:
        try:
            result = subprocess.run(self.argv, input=json.dumps({
                "operation": operation, "id": reference, **fields,
            }), encoding="utf-8", capture_output=True, timeout=60)
        except subprocess.TimeoutExpired as error:
            raise ValueError("Tracker command timed out") from error
        if result.returncode:
            raise ValueError(f"Tracker command failed (exit {result.returncode})")
        response = json.loads(result.stdout)
        if not isinstance(response, dict) or response.get("ok") is not True:
            raise ValueError("Tracker command must return a JSON object with ok=true")
        return response

    def read(self, reference: str) -> Dict[str, Any]:
        response = self.call("read", reference)
        keys = ("id", "title", "description", "url")
        if any(not isinstance(response.get(key), str) for key in keys):
            raise ValueError("Tracker read must return string id, title, description and url fields")
        return {key: response[key] for key in keys}

    def update(self, reference: str, stage: str, pr_url: Optional[str] = None) -> None:
        self.call("update", reference, stage=stage, status=self.states[stage], pr_url=pr_url)


class LinearTracker:
    def __init__(self, settings: dict, states: dict):
        from agentorch.linear import from_settings

        self.client = from_settings({"team": settings.get("team")})
        self.states = states

    def issue(self, reference: str) -> Dict[str, Any]:
        issue = self.client.issue(reference)
        if issue["team"]["id"] != self.client.team()["id"]:
            raise ValueError("Ticket belongs to a different Linear team")
        return issue

    def read(self, reference: str) -> Dict[str, Any]:
        issue = self.issue(reference)
        return {"id": issue["identifier"], "title": issue["title"],
                "description": issue.get("description") or "", "url": issue["url"]}

    def update(self, reference: str, stage: str, pr_url: Optional[str] = None) -> None:
        issue = self.issue(reference)
        current = issue["state"]
        status_name = self.states[stage].casefold()
        states = self.client.team()["states"]["nodes"]
        target = next((state for state in states if state["name"].casefold() == status_name), None)
        if target is None:
            raise ValueError(f"Linear team has no status named {self.states[stage]!r}")
        if current["type"] == "canceled":
            return
        if pr_url:
            self.client.attach(issue["id"], pr_url)
        rank = {self.states[name].casefold(): index for index, name in enumerate(STAGES)}
        if (current["type"] != "completed" and current["id"] != target["id"]
                and rank.get(current["name"].casefold(), -1) < rank[status_name]):
            self.client.update_issue(issue["id"], stateId=target["id"])


def from_settings(settings: dict):
    if not isinstance(settings, dict):
        raise ValueError("Configure a tracker in .agentorch.json")
    states = settings.get("states", {"in-progress": "In Progress", "in-review": "In Review", "done": "Done"})
    if (not isinstance(states, dict) or set(states) != set(STAGES)
            or any(not isinstance(value, str) or not value.strip() for value in states.values())
            or len({value.casefold() for value in states.values()}) != len(STAGES)):
        raise ValueError("Tracker states must map in-progress, in-review and done to three distinct names")
    backend = settings.get("backend")
    if backend == "linear":
        return LinearTracker(settings, states)
    if backend == "command":
        return CommandTracker(states)
    raise ValueError("Tracker backend must be linear or command")


def sync_pr(github: Any, number: int, settings: Optional[dict]) -> bool:
    pr = github.get(f"/pulls/{number}")
    reference = linked_ticket(pr.get("body"))
    if not reference or (pr["state"] == "closed" and not pr["merged"]):
        return False
    from_settings(settings).update(reference, "done" if pr["merged"] else "in-review", pr["html_url"])
    return True
