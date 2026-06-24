[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/03/19 13:06:17.162346 )
[//]: # (+ Revised: 	2026/06/23 14:23:15.602709 )
[//]: # ( ---------------------------------------------------------------------- )

# ximrato-app

Cross-platform (desktop/mobile/web) fitness logger built with [Flet](https://flet.dev) (Python). Frontend counterpart to [ximrato-server](../ximrato-server/README.md).

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
| `XIMRATO_API_URL` | `http://127.0.0.1:8000` | Backend base URL. Port must match the server's `PORT` env variable. |

## Running

Desktop:
```bash
uv run flet run main.py --port 8080 --host 0.0.0.0
```

Web:
```bash
uv run flet run main.py --port 8080 --host 0.0.0.0 --web
```

Build (Windows exe / Android APK):
```bash
uv run flet build windows --clear-cache
uv run flet build apk --clear-cache
```

> `--clear-cache` is required on first build after dependency changes or icon updates. Subsequent incremental builds can omit it.

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
- Profile picture — upload (JPEG/PNG/WebP) and remove avatar from profile screen
- Unit config screen (`/settings`) — weight (kg/lb), distance (km/mi), height (cm/in); reachable from profile AppBar
- Keyboard controls — Enter submits forms on all screens, Escape navigates back where applicable, Tab moves between fields
- Structured logging — route changes, API requests and responses
- GUI smoke tests — 15 Playwright tests covering auth, profile, account, settings, session, cardio/metrics navigation, unauthenticated redirect, and avatar button visibility
- Unit tests — 192 tests across auth API, users API, sessions API (incl. exercise progress and localized names), cardio API, i18n (Translator + catalog completeness), error parsing, session screen helpers, cardio screen helpers, metrics screen helpers, and progress screen helpers
- Home screen — launchpad with Session, Cardio, Body metrics buttons
- Session logging — start session, log sets (exercise dropdown, reps, weight, bodyweight/to_failure flags, RPE), end session, view past sessions
- Cardio quick log — select type, live timer, end → type-specific fields (Running/Cycling: distance, HR, elevation; Rowing: distance, HR, stroke rate); past logs listed below
- Login history — `/auth-history` screen listing login/logout/register events with timestamps; logout button on account screen
- App logo — SVG mascot (`assets/logo.svg`); shown on login, register, and home screens; PNG rendition used as desktop window icon and web favicon
- i18n — flag-button language switcher in every screen's AppBar; supported languages: English (`en`), Galician (`gl`), Spanish (`es`); selection persisted locally via `SharedPreferences` and synced server-side on login/register; async view loading — screens render immediately, data fills in without blocking navigation
- Body metrics — log individual measurements (weight, waist, chest, hips, neck, arms, thighs) as independent per-type records; any combination can be submitted in one form; past entries grouped by type with ↑/↓ delta from the previous entry; all entries listed inside a collapsible tile per type
- Token refresh on 401 — all screens auto-retry once with the stored refresh token on a 401; redirects to login if the refresh token is also expired or missing; both async and sync handlers covered
- History views — `/session-history` and `/cardio-history` dedicated screens; accessible via the history (🕐) button in each screen's AppBar; session history lists past sessions as collapsible tiles with set details; cardio history lists past logs with type, duration, and optional stats
- Progress screen — `/progress` with Strength and Body tabs; line charts for max weight per session (strength) and body metric history; exercise and metric dropdowns with saved state across navigations; localized exercise names
- Session screen — equipment filter chip bar to narrow the exercise dropdown; exercise info panel showing muscles, equipment, and description for the selected exercise

## v1 Scope

### Auth
- Self-registration
- JWT-based login against the backend
- Login and logout timestamps recorded per user

### User Profile & Config
- Static profile: display name, sex, date of birth, height
- Profile picture: upload (JPEG/PNG/WebP, max 5 MB), remove
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

## Known Issues

### Avatar not displayed on Firefox-based browsers (web)

Profile and home-screen avatars show the placeholder icon instead of the uploaded image when running the web build on Firefox or any Gecko-based browser. Desktop and Chromium-based browsers are unaffected.

**Root cause:** Flet 0.82 compiles the Flutter frontend to WebAssembly (CanvasKit renderer). In this mode, every image source — including in-memory byte arrays and plain base64 strings — ultimately passes through Flutter web's `MemoryImage` codec, which has a known decoding defect on the Gecko/SpiderMonkey runtime. There is no encoding of the image data on the Python side that bypasses this; the issue is inside Flet's compiled Dart/Flutter layer.

**Workaround:** none at the current Flet version. The placeholder icon is shown as a fallback. Monitor Flet release notes for a fix.

---

## v2 (deferred)
- HIIT / circuit training
- Sports logging
- Additional exercise categories (swimming, jump rope, etc.)
- Additional body measurements beyond the v1 set

## License

[PayBack License (PBL)](LICENSE)
