[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/03/19 13:06:17.162346 )
[//]: # (+ Revised: 	2026/03/20 09:55:10.773216 )
[//]: # ( ---------------------------------------------------------------------- )

# ximrato-app

Cross-platform (desktop/mobile/web) fitness logger built with [Flet](https://flet.dev) (Python). Frontend counterpart to [ximrato-server](../ximrato-server).

## Repos

| Repo | Role |
|------|------|
| [`ximrato-app`](https://github.com/Ran-n/ximrato-app) | This repo — Flet frontend |
| [`ximrato-server`](https://github.com/Ran-n/ximrato-server) | FastAPI backend |

## Running

```bash
uv run python main.py
```

Auto-restart on file changes (dev):
```bash
uv run watchmedo auto-restart --patterns="*.py" --recursive -- python main.py
```

## v1 Progress

### Done
- Auth — login and register screens, JWT tokens stored in session, auth guard on all routes
- Profile screen — view and edit username, email, password; only sends changed fields
- Keyboard controls — Enter submits forms on all screens, Escape navigates back where applicable, Tab moves between fields
- Structured logging — route changes, API requests and responses

### To Do
- Extended profile fields — display name, sex, date of birth, height
- Unit config screen — weight (kg/lb), distance (km/mi), height (cm/in)
- Home screen — meaningful content (dashboard or quick-action buttons)
- Session logging — start session, log sets (exercise, reps, weight, RPE, to_failure), end session
- Cardio quick log — duration, distance, type (running/cycling/rowing), optional fields
- Body metrics log — weight, waist, chest, hips, neck, arms, thighs
- History views — past sessions, cardio logs, body metric trends
- Token refresh on 401 — auto-retry with refresh token, redirect to login on expiry

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
