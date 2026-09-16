# CSC 648 Section 06 Team 03

## Project Overview

This repository contains Team 03's CSC 648 Software Engineering project. Milestone 0 establishes the team's GitHub workflow, software stack, remote deployment, database connection, About page, and documentation. The specific Career Path application concept has not been finalized; product-specific and AI features are planned for later milestones.

## Team

| Member | Role |
|---|---|
| Rohit Vennelakanti | Team Lead |
| Fanta Phommachith | Scrum Master |
| Nuradil Kumarov | GitHub Master |
| Obaidullah Darwishi | AI Master |
| Ali Coklu | Backend |
| Ian Ayala | Frontend |

## Software Stack

- **Frontend:** React with Vite
- **Backend:** Python with FastAPI
- **Database:** PostgreSQL hosted through Supabase
- **Frontend Hosting:** Vercel
- **Backend Hosting:** Render
- **Version Control:** Git and GitHub
- **AI:** LLM API integration planned for later milestones

## Repository Structure

```text
SFSU-csc648-06-Fall26-team03/
├── app/
│   ├── frontend/       # React/Vite frontend
│   └── backend/        # Python/FastAPI backend
├── milestones/
│   └── m0/             # Milestone 0 documentation
├── README.md
├── render.yaml
└── .gitignore
```

## Deployment

- **Frontend:** https://sfsu-csc648-06-fall26-team03.vercel.app/
- **Backend:** https://careergps-backend-n1uj.onrender.com/
- **API documentation:** https://careergps-backend-n1uj.onrender.com/docs
- **Health endpoint:** https://careergps-backend-n1uj.onrender.com/health

## Local Setup

### Frontend

```bash
cd app/frontend
npm ci
npm run dev
```

Additional available commands:

```bash
npm run lint
npm run build
npm run preview
```

### Backend

```bash
cd app/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The local backend defaults to SQLite. The deployed backend uses PostgreSQL through the `DATABASE_URL` environment variable.

## Environment Variables

Frontend:

- `VITE_API_URL`

Backend:

- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `ALLOWED_ORIGINS`

Environment-specific values and secrets must be configured outside source control. Do not commit API keys, database credentials, JWT secrets, tokens, or populated `.env` files.
