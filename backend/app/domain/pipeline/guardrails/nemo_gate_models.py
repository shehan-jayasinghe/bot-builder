from dataclasses import dataclass
from enum import Enum


class NeMoGateIntent(str, Enum):
    PROCEED = "proceed"
    GREETING = "greeting"
    HELP = "help"
    BYE = "bye"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class NeMoGateContext:
    agent_name: str
    industry: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class ScriptedMatch:
    intent: NeMoGateIntent
    matched_phrase: str
    reply: str


@dataclass(frozen=True)
class GuardrailCheckResult:
    allowed: bool
    intent: NeMoGateIntent = NeMoGateIntent.PROCEED
    refusal_message: str | None = None
    scripted_reply: str | None = None
    matched_phrase: str | None = None
    rail: str | None = None


@dataclass(frozen=True)
class NeMoOutputCheckResult:
    allowed: bool
    refusal_message: str | None = None
    rail: str | None = None
