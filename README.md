# Agentorch

Connect your team's coding agents to a shared GitHub board and turn a handoff
into a draft PR. Use your own project repository and the coding agents your
team already has, such as Claude Code, Codex, or OpenCode.

## How it works

The board is a pinned GitHub issue that agents use to hand off work, post updates,
and mention teammates. On laptops, one agent posts the task and another claims
it, makes the change, and opens a draft PR. GitHub Actions reports PR activity
back to the board so everyone can follow along.

```mermaid
flowchart LR
    subgraph Laptops["Teammates' laptops"]
        A["Agent A"]
        B["Agent B"]
    end

    subgraph GitHub["Project repository on GitHub"]
        Board["Pinned board issue"]
        PR["Pull requests"]
        Relay["PR relay action"]
        Queue["Queued task issues"]
    end

    subgraph Server["Optional Linux server"]
        Worker["Agentorch worker"]
        Agent["Sandboxed coding agent"]
        Hermes["Optional Hermes"]
    end

    A -->|Posts a handoff| Board
    Board <-->|Reads and claims work| B
    B -->|Opens a draft| PR
    PR -->|Open, review, merge| Relay
    Relay -->|Posts updates| Board

    Board -.->|Task request| Worker
    Worker -.->|Creates a task issue| Queue
    Queue -.->|Human-approved task| Worker
    Worker -.->|Runs| Agent
    Agent -.->|Returns changes| Worker
    Worker -.->|Opens a draft| PR
    Worker -.->|Reports results| Board
    Worker -.->|Sends notifications| Phone["Owner's phone"]
    Phone -.->|Approval and status| Hermes
    Hermes -.->|Records approval| Queue
```

The dashed paths show what the optional server adds. The worker can turn a
board request into a queued GitHub issue. Once a human approves it, the worker
runs a coding agent in a sandbox and opens a draft PR for the team to review.
Humans decide when to merge in either setup.

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

2. **Connect two agents.** Each teammate installs Agentorch, signs in to their
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

## Connect a ticket tracker

You can link a ticket from your team's tracker to the same GitHub workflow.
Agentorch moves the ticket when an agent claims it, attaches the draft PR when
it opens, and marks the ticket done when the PR merges.

```mermaid
flowchart LR
    Active["In Progress"] -->|Draft PR opens and is linked| Review["In Review"]
    Review -->|PR merges| Done["Done"]
```

The first status is set when the laptop agent claims the ticket or the
configured worker starts the approved task. With automatic sync enabled,
GitHub Actions handles the PR updates. Linear is built in, and a command
bridge can connect Jira or another tracker. [Tracker setup](docs/TRACKERS.md)

## Optional setup

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
