"""Slack Bolt event handlers for the Purpose HR Assistant.

Registers handlers for:
  - direct messages to the bot (``message.im``)
  - ``app_mention`` in channels
  - the ``/ask-hr`` slash command

Loop prevention: messages from bots (or from the bot's own user id) are ignored.
Channel mentions are answered in-thread; the ``thread_ts`` (falling back to the
message ts, then channel id) is used as the key for ephemeral thread memory.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Matches a leading <@U123456> style mention so it can be stripped out.
_MENTION_RE = re.compile(r"<@[A-Z0-9]+>")


def _thread_key(channel: str, thread_ts: str | None, ts: str | None) -> str:
    """Build a stable key for thread memory.

    Prefer the thread timestamp; fall back to the message ts, then the channel.
    """
    return f"{channel}:{thread_ts or ts or channel}"


def _strip_mentions(text: str) -> str:
    return _MENTION_RE.sub("", text or "").strip()


def register_handlers(app, assistant) -> None:
    """Register all Slack handlers on the given Bolt ``app``.

    ``assistant`` is an hr_assistant.claude_client.HRAssistant instance.
    """

    @app.event("app_mention")
    def handle_app_mention(event, say, client, logger):  # noqa: ARG001
        # Ignore messages from bots or without a human author (loop prevention).
        if event.get("bot_id") or event.get("subtype") == "bot_message":
            return

        channel = event["channel"]
        ts = event.get("ts")
        # Reply in-thread: use the existing thread, or start one on this message.
        thread_ts = event.get("thread_ts") or ts
        question = _strip_mentions(event.get("text", ""))

        if not question:
            say(
                text="Hi! Ask me an HR question and I'll check the Team Playbook. :hibiscus:",
                thread_ts=thread_ts,
            )
            return

        key = _thread_key(channel, event.get("thread_ts"), ts)
        answer = assistant.answer(question, key)
        say(text=answer, thread_ts=thread_ts)

    @app.event("message")
    def handle_message(event, say, logger):  # noqa: ARG001
        # Only handle direct messages (IM). Other message events are ignored.
        if event.get("channel_type") != "im":
            return
        # Ignore bot messages, edits, and other subtypes (loop prevention).
        if event.get("bot_id") or event.get("subtype"):
            return

        channel = event["channel"]
        ts = event.get("ts")
        thread_ts = event.get("thread_ts")
        question = (event.get("text") or "").strip()

        if not question:
            return

        key = _thread_key(channel, thread_ts, ts)
        answer = assistant.answer(question, key)
        # In a DM, reply in-thread if the user started one, else at top level.
        say(text=answer, thread_ts=thread_ts)

    @app.command("/ask-hr")
    def handle_ask_hr(ack, respond, command, logger):  # noqa: ARG001
        ack()
        question = (command.get("text") or "").strip()
        if not question:
            respond(
                "Usage: `/ask-hr <your question>` - for example "
                "`/ask-hr how much vacation do I get?`"
            )
            return

        channel = command.get("channel_id", "")
        user = command.get("user_id", "")
        # Slash commands aren't threaded; key memory by channel+user.
        key = f"cmd:{channel}:{user}"
        answer = assistant.answer(question, key)
        respond(answer)
