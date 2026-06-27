# Ops Runbook (Render + Docker)

## Service shape
- Deploy backend as a Docker service on Render using `backend/Dockerfile` (entrypoint runs migrations then uvicorn with workers=1).
- Health check: `GET /v1/health` (returns `status`, `environment`, `storage_backend`, optional `git_sha`).
- Request tracing: every request gets `X-Request-Id`; logs include `request_id` (format `%(...request_id...)`).

## Required environment variables
- `OPENAI_API_KEY`
- `STORAGE_BACKEND=r2` (for durability) or `local` (dev only)
- `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, optional `S3_PREFIX`
- `TMP_DIR=/tmp/qn_tmp` (safe temp space for downloads)
- `DATABASE_URL=sqlite:////var/data/quran_notes.db` when using a Render persistent disk (recommended for MVP)
- `PORT` is provided by Render; uvicorn reads `${PORT}` automatically
- Optional: `GIT_SHA` for health metadata; `CORS_ORIGINS` if you customize web origins

## Render configuration
- Type: Web Service (Docker)
- Docker context: repo root
- Dockerfile: `backend/Dockerfile`
- Start command: leave blank (Dockerfile ENTRYPOINT handles it)
- Persistent disk (if using SQLite): mount to `/var/data`, read/write
- Health check path: `/v1/health`

## Operational tasks
- **Deploy**: push to main; Render rebuilds via Dockerfile.
- **Restart**: use Render dashboard; app will re-run migrations at startup.
- **Logs**: include `request_id`; surface `X-Request-Id` in user reports to correlate.
- **Validate storage**: `STORAGE_BACKEND` reported by `/v1/health`; uploads stored as `s3://...` when using R2/S3.
- **Rotate keys**: update `OPENAI_API_KEY` or S3 creds in Render env and redeploy/restart.

## Common issues
- 500 on processing start: verify `OPENAI_API_KEY` set.
- Uploads failing: check `MAX_UPLOAD_MB` and R2 credentials; inspect logs with `request_id`.
- Stuck “Uploaded”: restart backend (restarts sweeper) and tap “Start Processing” in app.

