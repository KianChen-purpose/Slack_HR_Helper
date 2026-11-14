# Purpose HR Assistant

An internal Slack bot that answers Purpose (Purpose Unlimited) employees' HR
questions in English, grounded **only** in the Purpose Team Playbook. If the
answer isn't in the playbook, the bot doesn't guess - it points the employee to
the People & Culture (P&C) team.

## How it works: full-context, no RAG

The entire Team Playbook (~22K tokens) is sent to Claude on **every** request as
a single `document` content block. There is no vector database, no embeddings,
and no chunking.

Why this design:

- **It fits.** The playbook is small enough to live comfortably in the model's
  context window, so there's no need to retrieve fragments.
- **It's cached.** The document block is sent with
  `cache_control: {"type": "ephemeral"}` and is kept byte-identical across
  calls, so after the first request the playbook is served from Claude's prompt
  cache - roughly 90% cheaper on repeat queries.
- **It's cited.** The document block has `citations: {"enabled": true}`, which
  grounds answers in the playbook text.
- **It's grounded-only.** The system prompt instructs the model to answer strictly
  from the playbook and to fall back to P&C when the answer is missing, unclear,
  a placeholder, or flagged for confirmation.

Answers end with a short `Source: <section>` line when they draw on the playbook.
For anything not covered, the bot replies with a polite P&C fallback.

## Setup

1. **Create the Slack app from the manifest.**
   - Go to <https://api.slack.com/apps> -> *Create New App* -> *From an app manifest*.
   - Pick your workspace and paste the contents of [`manifest.yaml`](manifest.yaml).
2. **Install the app to your workspace** (OAuth & Permissions -> *Install to Workspace*).
3. **Get the tokens:**
   - **Bot token** (`xoxb-...`) from *OAuth & Permissions* -> this is `SLACK_BOT_TOKEN`.
   - **App-level token** (`xapp-...`) with the `connections:write` scope, created
     under *Basic Information* -> *App-Level Tokens* -> this is `SLACK_APP_TOKEN`
     (required for Socket Mode).
4. **Get an Anthropic API key** (`sk-ant-...`) -> this is `ANTHROPIC_API_KEY`.
5. **Configure the environment:**
   ```bash
   cp .env.example .env
   # edit .env and fill in the tokens / key
   ```
6. **Install dependencies and run:**
   ```bash
   pip install -r requirements.txt
   python app.py
   ```

The bot loads `knowledge_base/team_playbook.md` at startup and will exit with a
clear error if that file is missing or empty.

## Using the bot

- **Direct message** the bot a question.
- **@mention** the bot in a channel - it replies in-thread.
- Use the **`/ask-hr <question>`** slash command.

Messages from bots (and the bot's own messages) are ignored to prevent loops.

## Model and effort knobs

Two optional environment variables tune cost and quality:

| Variable | Default | Notes |
| --- | --- | --- |
| `ANTHROPIC_MODEL` | `claude-opus-5-5` | `claude-sonnet-5-5` is a strong, lower-cost option you can set here. |
| `HR_BOT_EFFORT` | `low` | One of `low`, `medium`, `high`, `xhigh`, `max`. Grounded Q&A doesn't need high effort, so `low` keeps it fast and cheap. |

## Keeping the playbook up to date

The bot reads the playbook from `knowledge_base/team_playbook.md`. To update it,
replace that file with the new content and **restart the bot** (`python app.py`).
The playbook is loaded and cached once at startup, so changes take effect on
restart.

## Thread memory

The bot keeps a small amount of per-thread conversation context (the last few
turns) so follow-up questions in the same thread have context. This memory is
**in-memory and ephemeral** - it is lost whenever the bot restarts. That's fine
for v1. Only the first user turn in a thread carries the cached playbook document
block; later turns are plain text, which keeps the prompt cache warm.

## Deployment

Because the bot runs in Slack **Socket Mode**, it needs no public URL and no
inbound webhook. It can run on any always-on host or container - just set the
environment variables and run `python app.py`.
