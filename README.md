[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/03/19 13:06:17.162346 )
[//]: # (+ Revised: 	2026/03/19 14:15:24.246111 )
[//]: # ( ---------------------------------------------------------------------- )

# ximrato-app

Cross-platform (desktop/mobile/web) fitness logger built with [Flet](https://flet.dev) (Python). Frontend counterpart to [ximrato-server](../ximrato-server).

## Repos

| Repo | Role |
|------|------|
| `ximrato-app` | This repo — Flet frontend |
| `ximrato-server` | FastAPI backend |

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
