# Connect a ticket tracker

The GitHub board and PR relay work on their own. Add a tracker when your team
wants to keep tickets in an external system. Agentorch uses three stages:

| GitHub workflow | Tracker stage |
| --- | --- |
| An agent claims the work | In Progress |
| The draft PR opens | In Review, with a link to the PR |
| The PR merges | Done |

## Set up Linear

Ask your coding agent to walk through these steps with you. Add a `tracker`
block to the project’s existing `.agentorch.json`. Replace `ENG` and the status
names with your team key and actual Linear workflow states:

```json
{
  "tracker": {
    "backend": "linear",
    "team": "ENG",
    "states": {
      "in-progress": "In Progress",
      "in-review": "In Review",
      "done": "Done"
    }
  }
}
```

Keep the other project settings that `agentorch init` wrote. For CLI commands,
set `LINEAR_API_KEY` in the session or use the owner-only
`~/.config/agentorch/linear-key` file. Use a credential that can read issues,
change their states, and add attachments. You can use the same Linear team
that an existing Claude Code MCP connection uses. MCP credentials stay with
that client, so the CLI and Actions each need their own configured access.

Commit the project config and tracker workflow to the default branch. To
enable automatic review and merge updates, set the GitHub Actions repository
variable `AGENTORCH_SYNC_TRACKER` to `true` and add the `LINEAR_API_KEY` Actions
secret. The workflow installs Agentorch from its main branch by default. Set
`AGENTORCH_TRACKER_REF` to a tested tag or commit SHA to pin it.

## Use a ticket

For a laptop handoff, ask the agent to do the following:

1. Run `agentorch tracker show ENG-123` to read the ticket and get its PR marker.
   Share the ticket link on the board. Check who can read the GitHub repo before
   copying private ticket details into GitHub.
2. When taking the task, run `agentorch tracker claim ENG-123` and post the
   claim on the board.
3. Open the draft PR from a branch in the project repository. Paste the
   `pr_marker` value on its own line in the PR body. Include the ticket's URL
   in the body so reviewers can open it directly.

The tracker workflow reads the current PR state and updates the linked ticket.
It runs only for PRs from branches in the same repository. For fork PRs, or
to retry a sync, run `agentorch tracker sync-pr <PR number>` from your checkout
with tracker credentials. Run it after the draft opens and again after merge
if automatic sync is disabled. A PR closed without merging leaves the ticket
status alone.

For a server handoff, run `agentorch tracker queue ENG-123` to create an
approval-gated GitHub task. This copies the ticket description into the GitHub
issue. A collaborator with repository write access should queue the issue. Add
the same `tracker` object inside the corresponding `repositories[]` entry in
the worker config, and give the worker its own tracker credentials. When it
starts the approved task, it updates the ticket to In Progress. It carries the
ticket marker into the resulting PR, where the same Actions workflow handles
review and merge. If a claim update fails, the worker logs the error and
continues. Retry it with `agentorch tracker claim ENG-123`.

If your existing worker runs the Linear board and planner, use a separate
worker config and state directory for this GitHub queue. That older mode
dispatches directly from Linear.

## Connect Jira or another tracker

Use `"backend": "command"` with the same `states` mapping. Provide a trusted
bridge as a JSON argument array in `AGENTORCH_TRACKER_COMMAND`. For example,
`["python3","./scripts/tracker_bridge.py"]` runs a bridge checked into the
project. Use absolute paths when configuring the worker service. Set the array
in the CLI or worker environment, and in the GitHub
Actions variable of the same name for automated PR sync. Supply the bridge's
credentials in its environment, adding the corresponding Actions secret
mapping to the tracker workflow if needed.

The bridge reads one JSON object from stdin and writes one JSON object to
stdout. It can use the tracker's API or call a compatible MCP client to perform
the operation. Configure and authenticate that client in each environment
where the bridge runs.

| Operation | Request | Successful response |
| --- | --- | --- |
| Read | `{"operation":"read","id":"ENG-123"}` | `{"ok":true,"id":"ENG-123","title":"...","description":"...","url":"https://..."}` |
| Update | `{"operation":"update","id":"ENG-123","stage":"in-review","status":"Review","pr_url":"https://github.com/..."}` | `{"ok":true}` |

`pr_url` is null on a claim. Use the PR URL to add or update the link
idempotently. Support repeated requests and preserve a completed ticket if an
earlier lifecycle event is retried. Exit nonzero or return `{"ok":false}` when
the requested operation fails.
