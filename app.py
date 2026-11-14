"""Entrypoint for the Purpose HR Assistant Slack bot.

Runs in Slack Socket Mode, so no public URL / inbound webhook is required - it
can run on any always-on host or container.

Usage:
    python app.py

Requires the environment variables documented in .env.example (loaded here via
python-dotenv). See README.md for setup.
"""

import logging
import sys

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from hr_assistant.claude_client import build_assistant
from hr_assistant.config import ConfigError, load_config
from hr_assistant.knowledge import PlaybookError
from hr_assistant.slack_handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("hr_assistant.app")


def main() -> int:
    # Load environment variables from a local .env file, if present.
    load_dotenv()

    try:
        config = load_config()
    except ConfigError as e:
        logger.error("Configuration error: %s", e)
        return 1

    try:
        assistant = build_assistant(
            api_key=config.anthropic_api_key,
            model=config.anthropic_model,
            effort=config.hr_bot_effort,
        )
    except PlaybookError as e:
        logger.error("Playbook error: %s", e)
        return 1

    logger.info(
        "Starting Purpose HR Assistant (model=%s, effort=%s)",
        config.anthropic_model,
        config.hr_bot_effort,
    )

    app = App(token=config.slack_bot_token)
    register_handlers(app, assistant)

    handler = SocketModeHandler(app, config.slack_app_token)
    handler.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
