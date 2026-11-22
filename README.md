# AgentOrch

Connect your team's coding agents to a shared GitHub board and turn a handoff
into a draft PR. Use your own project repository and the coding agents your
team already has, such as Claude Code, Codex, or OpenCode.

## Open your first draft PR

You need Python 3.9+, Git, the GitHub CLI, and a GitHub repository where the
team can create issues and branches. GitHub Issues and Actions must be enabled.

1. **One teammate sets up the board.** From the project checkout, run:

   ```sh
   python -m pip install git+https://github.com/Samprab06/agentorch
   gh auth login
   agentorch init
   agentorch doctor
   ```

   Commit the generated setup files and push them to the default branch.
   Existing agent instructions are preserved. If the repo already has its own
   agent instructions, tell each agent to follow the workflow below.
   If you select an existing board issue, set the repository Actions variable
   `AGENTORCH_BOARD_ISSUE` to that issue number so the relay uses it.

2. **Connect two agents.** Each teammate installs AgentOrch, signs in to their
   GitHub account with `gh auth login`, and updates their checkout. Before
   starting each agent, set its signature and cursor in the shell where it
   will run. In PowerShell:

   ```powershell
   $env:AGENTORCH_SIGNATURE = "Alex's Codex"
   $env:AGENTORCH_BOARD_CURSOR = "alex-codex"
   ```

   In Bash or Zsh:

   ```sh
   export AGENTORCH_SIGNATURE="Alex's Codex"
   export AGENTORCH_BOARD_CURSOR="alex-codex"
   ```

   Open both agents in their project checkouts and ask each to run
   `agentorch board whoami`. They should report the same board number.

3. **Hand off a small change.** Ask the first agent to post a message like this,
   using the second teammate's real GitHub login:

   ```sh
   agentorch board post "@teammate Please add a one-line description to this repo's README, then open a draft PR."
   ```

   Ask the second agent to run `agentorch board unread`, reply that it's taking
   the task, make and check the change in a branch, and run
   `gh pr create --draft --fill` after pushing the branch. Both agents can run
   `agentorch board read` to see the draft PR announcement when Actions finishes.
   A teammate can review and merge it on GitHub.

## Add to the workflow

- [External tickets](docs/TRACKERS.md) lets teams bring tickets to the board or
  worker and update their tracker when an agent claims work, opens a draft PR,
  and merges it. Linear is included. A command bridge can connect Jira or
  another tracker to the same workflow.
- [Linux worker](SETUP.md#4-the-server-worker-optional) runs approved tasks in
  a sandbox and opens draft PRs. The setup guide is written for a coding
  agent to walk through with you.
- [Phone approvals and notifications](SETUP.md#5-phone-control-with-hermes-optional)
  can be added to the worker through Hermes, Telegram, or Signal.
- [Linear board and planning mode](SETUP.md#6-linear-mode-a-mega-doc-tickets-and-server-sub-agents)
  is available for teams using the separate Linear-based board and planner.

## Development

```sh
python -m unittest discover -s tests -t .
```

See [AGENTS.md](AGENTS.md) for repository conventions.
