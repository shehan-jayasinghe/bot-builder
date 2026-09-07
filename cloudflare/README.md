# Bot Builder (Cloudflare)

Next.js app deployed to Cloudflare Workers.

## Setup

```bash
cd cloudflare
npm install
npm run dev
```

- UI: http://localhost:3000
- Health: http://localhost:3000/api/health

## Deploy

```bash
npx wrangler login
npm run deploy
```
