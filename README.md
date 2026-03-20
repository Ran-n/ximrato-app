[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/03/19 13:06:17.162346 )
[//]: # (+ Revised: 	2026/03/20 18:35:17.032508 )
[//]: # ( ---------------------------------------------------------------------- )

# ximrato-app

Cross-platform (desktop/mobile/web) fitness logger built with [Flet](https://flet.dev) (Python). Frontend counterpart to [ximrato-server](../ximrato-server).

## Repos

| Repo | Role |
|------|------|
| [`ximrato-app`](https://github.com/Ran-n/ximrato-app) | This repo — Flet frontend |
| [`ximrato-server`](https://github.com/Ran-n/ximrato-server) | FastAPI backend |

## Configuration

Copy `.env.example` to `.env` and set the values:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `XIMRATO_API_URL` | `http://127.0.0.1:8000` | Backend base URL |

## Running

Desktop:
```bash
uv run python main.py
```

Web:
```bash
uv run flet run --web --port 8080 main.py
```

## Testing

Unit tests (no services needed):
```bash
uv run pytest tests/ -m "not gui"
```

GUI smoke tests (requires both services running):
```bash
# terminal 1 — backend
cd ../ximrato-server && uv run uvicorn main:app --reload

# terminal 2 — frontend
uv run flet run --web --port 8080 main.py

# terminal 3 — tests
uv run pytest tests/ -v
```

## v1 Progress

### Done
- Auth — login and register screens, JWT tokens stored in session, auth guard on all routes
- Profile screen — view and edit username, email, password, display name, sex, date of birth, height; only sends changed fields
- Unit config screen (`/settings`) — weight (kg/lb), distance (km/mi), height (cm/in); reachable from profile AppBar
- Keyboard controls — Enter submits forms on all screens, Escape navigates back where applicable, Tab moves between fields
- Structured logging — route changes, API requests and responses
- GUI smoke tests — 12 Playwright tests covering auth, profile, account, settings, session, and unauthenticated redirect
- Unit tests — sessions API client and session screen helpers (formatting, label generation)
- Home screen — launchpad with Session, Cardio, Body metrics buttons
- Session logging — start session, log sets (exercise dropdown, reps, weight, bodyweight/to_failure flags, RPE), end session, view past sessions

### To Do
- Cardio quick log — duration, distance, type (running/cycling/rowing), optional fields
- Body metrics log — weight, waist, chest, hips, neck, arms, thighs
- History views — past sessions, cardio logs, body metric trends
- Token refresh on 401 — auto-retry with refresh token, redirect to login on expiry
- i18n — multiple language support

## v1 Scope

### Auth
- Self-registration
- JWT-based login against the backend

### User Profile & Config
- Static profile: display name, sex, date of birth, height
- Units config screen: weight (kg/lb), distance (km/mi), height (cm/in)

### Logging Flows

| Flow | What it logs | Session wrapper |
|------|-------------|-----------------|
| Session | Strength exercises | Yes — start / end |
| Quick log | Cardio | No |
| Body metrics | Body measurements | No |

### Strength Set Fields
- reps, weight (decimal; 0 for bodyweight)
- bodyweight_counted (boolean)
- RPE (qualitative labels — no numbers shown to user):
  - No reps left / Could do 1 more / Could do 2 more / Could do 3 more / Could do 4–5 more / Very light
- to_failure (boolean)
- logged_at — used to derive rest time between sets

### Cardio Fields
- duration, distance
- avg_heart_rate (optional)
- elevation_gain (optional)
- stroke_rate (optional, rowing only)

Cardio types v1: running, cycling, rowing.

### Body Metrics (time-series)
weight, waist, chest, hips, neck, arms, thighs

## v2 (deferred)
- HIIT / circuit training
- Sports logging
- Additional exercise categories (swimming, jump rope, etc.)
- Additional body measurements beyond the v1 set
