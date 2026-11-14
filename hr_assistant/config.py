"""Configuration loaded from environment variables.

Required:
  - SLACK_BOT_TOKEN   (xoxb-...)  bot user OAuth token
  - SLACK_APP_TOKEN   (xapp-...)  app-level token with connections:write (Socket Mode)
  - ANTHROPIC_API_KEY             Claude API key

Optional (with defaults):
  - ANTHROPIC_MODEL   default "claude-opus-5-5"
  - HR_BOT_EFFORT     default "low"  (one of: low | medium | high | xhigh | max)
"""

import os


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


# Default model. claude-sonnet-5-5 is a strong lower-cost alternative that can
# be selected by setting ANTHROPIC_MODEL.
DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "low"
VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max"}


class Config:
    """Resolved runtime configuration."""

    def __init__(
        self,
        slack_bot_token: str,
        slack_app_token: str,
        anthropic_api_key: str,
        anthropic_model: str,
        hr_bot_effort: str,
    ) -> None:
        self.slack_bot_token = slack_bot_token
        self.slack_app_token = slack_app_token
        self.anthropic_api_key = anthropic_api_key
        self.anthropic_model = anthropic_model
        self.hr_bot_effort = hr_bot_effort


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(
            f"Required environment variable {name} is not set. "
            "See .env.example for the full list."
        )
    return value


def load_config() -> Config:
    """Read and validate configuration from the environment.

    Raises ConfigError with a clear message if a required value is missing.
    """
    slack_bot_token = _require("SLACK_BOT_TOKEN")
    slack_app_token = _require("SLACK_APP_TOKEN")
    anthropic_api_key = _require("ANTHROPIC_API_KEY")

    anthropic_model = os.environ.get("ANTHROPIC_MODEL", "").strip() or DEFAULT_MODEL

    hr_bot_effort = os.environ.get("HR_BOT_EFFORT", "").strip() or DEFAULT_EFFORT
    if hr_bot_effort not in VALID_EFFORTS:
        raise ConfigError(
            f"HR_BOT_EFFORT='{hr_bot_effort}' is invalid. "
            f"Choose one of: {', '.join(sorted(VALID_EFFORTS))}."
        )

    return Config(
        slack_bot_token=slack_bot_token,
        slack_app_token=slack_app_token,
        anthropic_api_key=anthropic_api_key,
        anthropic_model=anthropic_model,
        hr_bot_effort=hr_bot_effort,
    )
