# Bot Builder — Frontend

React admin UI for the Bot Builder platform.

## Setup

```bash
cp .env.example .env
# Add your Clerk publishable key from https://dashboard.clerk.com
npm install
npm run dev
```

## Clerk dashboard

- Sign-in URL: `/sign-in`
- After sign-in URL: `/`
- Allowed origins: `http://localhost:5173`

## Structure

```text
src/
├── auth/              # ProtectedRoute
├── components/layout/ # Sidebar, Header
├── config/            # env
├── constants/         # navigation
├── layouts/           # AppShell
├── pages/agent/       # Agent detail, preview, evaluation (Eval Lab)
├── api/               # REST clients (agents, preview, evaluation, …)
├── components/evaluation/  # Metric panels + EvalCaseTable
└── routes/            # Route definitions
```

## Pages

| Route | Page |
|-------|------|
| `/` | Home |
| `/agent` | Agent list |
| `/agent/:agentId` | Agent detail |
| `/agent/:agentId/preview` | Preview chat + trace |
| `/agent/:agentId/evaluation` | **Eval Lab** — RAGAS test cases + metric panels |
| `/workflows` | Workflows |
| `/data-sources` | Data Sources |
| `/channels` | Channels |
| `/conversations` | Conversations |
| `/analytics` | Analytics |
| `/schedulers` | Schedulers |
| `/settings` | Settings |

RAG evaluation docs: [../backend/document/evaluation/00-overview.md](../backend/document/evaluation/00-overview.md). Requires `RAG_EVAL_ENABLED=true` on the backend.
