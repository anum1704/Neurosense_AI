# Deploying NeuroSense AI

The frontend and backend deploy to **two different places** — Netlify only
serves static files, it can't run the Python ML backend.

## 1. Backend first (Render — free tier works)

1. Push this `project/` folder to a GitHub repo (or use Render's manual deploy).
2. On [render.com](https://render.com): **New → Blueprint**, point it at your repo.
   It will read `render.yaml` at the repo root and configure everything
   automatically (root dir `backend/`, install, start command).
   - No Blueprint? Do it manually: **New → Web Service** → root directory
     `backend` → build command `pip install -r requirements.txt` → start
     command `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
3. Make sure `backend/artifacts/` (the trained model files) are committed to
   the repo — Render's free tier has no persistent disk, so if artifacts
   aren't in the repo itself, the API will 503 with "artifacts not found."
4. Once deployed, note your API URL, e.g. `https://neurosense-api.onrender.com`.
5. (Recommended) On Render, set an environment variable
   `ALLOWED_ORIGINS=https://your-site.netlify.app` to lock down CORS instead
   of allowing every origin.

Free-tier Render web services spin down after inactivity — the first request
after idling can take ~30-50s to wake up. That's a platform behavior, not a
bug in the app.

## 2. Frontend (Netlify)

1. Edit `frontend/index.html` — near the very top of `<head>`, change:
   ```html
   <script>window.NEUROSENSE_API_BASE_URL = 'http://localhost:8000';</script>
   ```
   to your real backend URL from step 1:
   ```html
   <script>window.NEUROSENSE_API_BASE_URL = 'https://neurosense-api.onrender.com';</script>
   ```
2. On [netlify.com](https://app.netlify.com): **Add new site → Deploy manually**,
   drag in the `frontend/` folder (or connect the repo — `netlify.toml` at the
   repo root already tells Netlify to publish the `frontend/` directory, so
   you can point it at the whole repo too).
3. Done — Netlify gives you a URL like `https://neurosense-ai.netlify.app`.

## 3. Wire CORS back to the real frontend URL

Once you know your Netlify URL, go back to Render and set
`ALLOWED_ORIGINS=https://neurosense-ai.netlify.app` (comma-separate multiple
origins if needed) so only your deployed frontend can call the API.

## Alternatives to Render

Railway and Fly.io work the same way — Python web service, `backend/` as
root, `pip install -r requirements.txt`, then
`uvicorn api.main:app --host 0.0.0.0 --port $PORT`. `backend/Procfile` is
already set up for Railway/Heroku-style platforms.
