# Dian QQ Bot Frontend

Vue 3 + TypeScript + Vite frontend for Dian QQ Bot.

This app is used to:
- run first-time setup wizard
- login with admin/user account
- manage QQ Bot instances (create/start/stop/restart/delete)
- view instance logs (incremental realtime mode)
- customize UI preferences (log refresh interval, default log lines, delete confirmation)

## Tech Stack

- Vue 3 (`<script setup>`)
- TypeScript
- Vite
- Pinia
- Vue Router
- Axios
- Tailwind CSS

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Default local dev URL:
- `http://127.0.0.1:5173`

## Environment Variables

Copy `.env.example` to `.env` and adjust values.

```bash
cp .env.example .env
```

Important variable:
- `VITE_API_BASE_URL`: backend API base URL

Recommended (dev + docker proxy):

```env
VITE_API_BASE_URL=/api/v1
```

If you want direct backend access, use:

```env
VITE_API_BASE_URL=http://127.0.0.1:18080/api/v1
```

## Scripts

- `npm run dev`: start dev server
- `npm run build`: type-check and build production bundle
- `npm run preview`: preview production build locally

## Main Routes

- `/setup`: first-time initialization wizard
- `/login`: login page
- `/`: instance list dashboard
- `/instance/:id`: instance detail and operations
- `/logs`: centralized log viewer
- `/settings`: UI preferences

## Auth Flow

- frontend stores access token in local storage
- axios request interceptor injects `Authorization: Bearer <token>`
- router guard checks setup status first, then auth status
- `401` responses clear session and redirect to `/login`

## Docker Deployment Notes

Current default ports in this project:
- frontend: `16788`
- backend: `18080`

When running via Docker Compose, open:
- `http://127.0.0.1:16788`

Frontend Nginx proxies `/api/*` to backend container at `api:18080`.

## Build Output

Production artifacts are generated in:
- `frontend/dist/`

## Troubleshooting

- blank page or API errors:
  - verify `VITE_API_BASE_URL`
  - verify backend health: `GET /health`
- login loop:
  - clear browser local storage and retry
  - make sure backend JWT settings are valid
- setup blocked:
  - check `GET /api/v1/setup/status` response

---

For overall project docs, see repository root `README.md`.
