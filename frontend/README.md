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
├── pages/             # One folder per section (stubs for now)
└── routes/            # Route definitions
```

## Pages (placeholders)

| Route | Page |
|-------|------|
| `/` | Home (workflow canvas shell) |
| `/agent` | Agent |
| `/workflows` | Workflows |
| `/data-sources` | Data Sources |
| `/channels` | Channels |
| `/conversations` | Conversations |
| `/analytics` | Analytics |
| `/schedulers` | Schedulers |
| `/settings` | Settings |
