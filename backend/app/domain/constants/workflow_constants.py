WORKFLOW_STATUS_DRAFT = "draft"
WORKFLOW_STATUS_PUBLISHED = "published"

MAX_WORKFLOWS_PER_ORGANIZATION = 5
DEFAULT_WORKFLOW_NAME = "Welcome"

DEFAULT_STARTER_NODES: list[dict] = [
    {
        "id": "start-1",
        "type": "start",
        "position": {"x": 120, "y": 220},
        "data": {},
    },
    {
        "id": "message-1",
        "type": "message",
        "position": {"x": 320, "y": 220},
        "data": {"text": "Welcome"},
    },
]

DEFAULT_STARTER_EDGES: list[dict] = [
    {"id": "edge-1", "source": "start-1", "target": "message-1"},
]
