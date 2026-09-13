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

Bindings live in `wrangler.template.jsonc`. `npm run deploy` generates `wrangler.jsonc` from env vars (file is gitignored):

```bash
export CLOUDFLARE_D1_DATABASE_ID=4c451cd2-c3f3-4b3e-b64a-4dd8f49f664f
export CLOUDFLARE_D1_DATABASE_NAME=bot-builder
export CLOUDFLARE_R2_BUCKET_NAME=bot-builder-kb
export CLOUDFLARE_VECTORIZE_INDEX=bot-builder-kb

npx wrangler login
npm run cf:inject           # optional locally; deploy does this with --strict
npm run db:migrate:remote   # apply schema once
npx wrangler secret put AUTH_SECRET
npm run deploy
```

### GitHub Actions

Workflow: `.github/workflows/cloudflare-deploy.yml`  
Runs on push to `main` when `cloudflare/**` changes, or via **Actions → Deploy Cloudflare → Run workflow**.

**Repository secrets**

| Name | Purpose |
|---|---|
| `CLOUDFLARE_ACCOUNT_ID` | Wrangler account |
| `CLOUDFLARE_API_TOKEN` | Wrangler auth |
| `AUTH_SECRET` | Auth.js session secret (synced to Worker) |

**Repository variables**

| Name | Example |
|---|---|
| `CLOUDFLARE_D1_DATABASE_ID` | D1 UUID |
| `CLOUDFLARE_D1_DATABASE_NAME` | `bot-builder` |
| `CLOUDFLARE_R2_BUCKET_NAME` | `bot-builder-kb` |
| `CLOUDFLARE_VECTORIZE_INDEX` | `bot-builder-kb` |

The workflow maps all of these into job `env` for inject + deploy. Add `AUTH_SECRET` under **Settings → Secrets** if it is not there yet.

