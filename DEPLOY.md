# Deploying Weakspot

Everything in the repository is ready. What remains needs your accounts, so the steps
below are written to be followed in order, with the checks that catch the mistakes that
are easy to make.

Two images are built and verified locally:

| image | target | verified |
|---|---|---|
| `api/Dockerfile` | single stage | builds from the repo root, migrates on boot, serves `/healthz` |
| `web/Dockerfile` | `production` | builds the bundle, serves it under nginx with SPA routing |

The web image defaults to the production target. Docker compose pins `target: dev` so
local work keeps hot reload.

---

## 1. Provision the two data services

Postgres has to have **pgvector** available. Neon and Supabase both do. Redis can be
Upstash or any managed instance.

Collect two values:

- `DATABASE_URL`, in the form `postgresql+psycopg://user:pass@host/db`. Note the
  `+psycopg` driver prefix, which SQLAlchemy needs and which most providers omit from
  the string they hand you.
- `REDIS_URL`

## 2. Register the GitHub OAuth app

<https://github.com/settings/developers> then New OAuth App.

- Homepage: the web URL from step 4
- Callback: `https://<api-host>/api/v1/auth/github/callback`

There is no other way in once deployed. The local bypass refuses to start when
`ENV=production`, which is deliberate.

## 3. Deploy the API

### Fly

Run from the repository root, because the image needs both `api/` and `taxonomy/`.

```bash
fly launch --no-deploy -c deploy/fly.api.toml
fly secrets set \
  ANTHROPIC_API_KEY=... VOYAGE_API_KEY=... \
  SESSION_SECRET="$(openssl rand -base64 32)" \
  DATABASE_URL=... REDIS_URL=... \
  WEB_ORIGIN=https://<web-host> \
  GITHUB_CLIENT_ID=... GITHUB_CLIENT_SECRET=... \
  GITHUB_CALLBACK_URL=https://<api-host>/api/v1/auth/github/callback
fly deploy -c deploy/fly.api.toml
```

### Render

Point a Blueprint at `deploy/render.yaml`, then fill the `sync: false` values in the
dashboard. `SESSION_SECRET` is generated for you.

The container runs `alembic upgrade head` before serving, so the schema comes up on
first boot. Failing that step stops the container rather than serving against a
mismatched schema.

## 4. Deploy the web app

`VITE_API_BASE` is inlined into the bundle **at build time**, so it has to be set for
the build command rather than as a runtime variable. Setting it afterwards changes
nothing.

Render's blueprint already declares the static site. For a container host, build with:

```bash
docker build --target production \
  --build-arg VITE_API_BASE=https://<api-host> \
  -t weakspot-web web/
```

## 5. Seed the index

The database is empty until this runs. Without a Voyage key, pass `--no-embed` and the
retriever falls back to its keyword arm.

```bash
fly ssh console -C "python -m weakspot.ingest.seed"
```

## 6. Check it

```bash
curl https://<api-host>/healthz
```

Expect `"database": true`, `"redis": true`, `"schema_current": true`, and
`"taxonomy_entries": 51`. Then sign in through GitHub on the web app and submit one
failed attempt end to end.

---

## The two settings that decide whether auth works

**`WEB_ORIGIN` must be the full origin, scheme included.** The CORS check compares it
against the browser's `Origin` header, which always carries a scheme, so a bare
hostname never matches. On Render, do not wire this with
`fromService ... property: host`, because that returns a hostname only.

**`SESSION_SECRET` must be set to a generated value.** It signs session cookies, and
its development default is committed to this repository, so a deploy that inherited it
would let anyone who can read the repo forge a session for any user. The app refuses to
start in production while the default is in place, or if the value is under 32
characters. Render generates one for you; on Fly, pass
`SESSION_SECRET="$(openssl rand -base64 32)"`.

**`SESSION_COOKIE_SAMESITE` must be `none` when the API and the web app are on
different hosts.** They are on Fly, and on Render's default domains, because
`onrender.com` is on the Public Suffix List. A `SameSite=Lax` cookie is not attached to
cross-site fetches, so sign-in appears to succeed through the OAuth redirect and then
every call the frontend makes returns 401. The deploy configs set `none` already.
Change it to `lax` only if both services end up on one registrable domain.

`none` requires `Secure`, which requires HTTPS. Both hosts provide it. The app refuses
to start on an invalid combination rather than issuing a cookie the browser discards
silently.

## Cost

Suite A measured **$0.00343 per diagnosis** on Haiku 4.5, with the taxonomy prefix
cached. The free tier is 10 diagnoses per user per day, enforced in Redis, and a repeat
submission of identical code is served from cache without consuming quota.

## After it is live

Paste the web URL into <https://www.opengraph.xyz> to confirm the social card renders.
That check needs a real domain, so it could not be done locally.
