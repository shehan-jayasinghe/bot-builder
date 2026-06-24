from typing import TypedDict


class GuardrailDef(TypedDict):
    key: str
    label: str
    instruction: str
    enabled: bool


DEFAULT_PERSONALITY = "Professional, Empathetic, Solution-oriented"
DEFAULT_TONE = "Friendly, Reassuring, Clear"

DEFAULT_GUARDRAILS: list[GuardrailDef] = [
    {
        "key": "stay_on_topic",
        "label": "Stay on topic",
        "instruction": "Only answer questions related to the business and your assigned role.",
        "enabled": True,
    },
    {
        "key": "no_harmful_content",
        "label": "Safe responses",
        "instruction": "Refuse harmful, illegal, or abusive requests.",
        "enabled": True,
    },
    {
        "key": "no_secrets",
        "label": "Protect secrets",
        "instruction": "Never request or expose passwords, OTPs, or full payment card numbers.",
        "enabled": True,
    },
    {
        "key": "honest_limits",
        "label": "Admit limits",
        "instruction": "Say when you do not know. Do not invent account balances or policies.",
        "enabled": True,
    },
    {
        "key": "human_escalation",
        "label": "Escalate when needed",
        "instruction": "Offer human support for disputes, fraud, or unresolved issues.",
        "enabled": True,
    },
]

INDUSTRY_RESPONSIBILITIES: dict[tuple[str, str | None], list[str]] = {
    ("financial_services", "payment_collections"): [
        "Send payment reminders and explain outstanding balances",
        "Generate secure payment links when requested",
        "Help customers set up payment plans",
        "Escalate unresolved cases to human agents",
    ],
    ("financial_services", "customer_onboarding"): [
        "Guide customers through KYC and onboarding steps",
        "Collect required documents and application details",
        "Provide application status updates",
    ],
    ("financial_services", "customer_support_triage"): [
        "Identify customer issues and route to the correct team",
        "Resolve common queries within the conversation",
        "Escalate complex cases with collected context",
    ],
    ("logistics", None): [
        "Track shipments and delivery status",
        "Answer questions about orders and returns",
        "Escalate lost or damaged package cases",
    ],
    ("travel", None): [
        "Assist with bookings, changes, and cancellations",
        "Answer travel policy and itinerary questions",
        "Escalate urgent travel disruptions",
    ],
    ("healthcare", None): [
        "Help patients with appointments and general inquiries",
        "Never provide medical diagnosis or treatment advice",
        "Escalate clinical questions to qualified staff",
    ],
    ("insurance", None): [
        "Explain policy coverage and claim steps",
        "Guide customers through claim submissions",
        "Escalate complex or disputed claims",
    ],
    ("other", None): [
        "Answer customer questions clearly and accurately",
        "Collect context before escalating",
        "Stay within the scope of the business",
    ],
}


def get_responsibilities(*, industry: str, agent_type: str | None) -> list[str]:
    if agent_type:
        specific = INDUSTRY_RESPONSIBILITIES.get((industry, agent_type))
        if specific:
            return specific
    return INDUSTRY_RESPONSIBILITIES.get((industry, None), INDUSTRY_RESPONSIBILITIES[("other", None)])


def merge_guardrails(user_guardrails: list[GuardrailDef] | None) -> list[GuardrailDef]:
    merged: dict[str, GuardrailDef] = {g["key"]: g for g in DEFAULT_GUARDRAILS}
    if user_guardrails:
        for item in user_guardrails:
            merged[item["key"]] = item
    return list(merged.values())
