# Tunnel Vision

> **Map your mind. Explore the unknown.**

Tunnel Vision is a B2C SaaS application that ingests your exported social media data, uses AI to extract your interests, and visualises your "knowledge bubble" as an interactive WebGL graph overlaid on the broader scope of human knowledge.

---

## Tech Stack (Zero-Cost)

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15 (App Router), React, TypeScript, Tailwind CSS, Framer Motion |
| **Graph Visualisation** | react-force-graph (WebGL / Three.js) |
| **Authentication** | Supabase Auth |
| **Backend API** | Python + FastAPI (Render Free Web Service) |
| **Knowledge Graph DB** | Neo4j AuraDB Free (200 k nodes / 400 k edges) |
| **Relational DB** | Supabase (PostgreSQL) |
| **AI / NLP** | LangChain + Google Gemini 1.5 Flash |
| **Frontend Hosting** | Cloudflare Pages |

---

## Repository Structure

```
Tunnel-Vision/
├── frontend/          # Next.js 14 App Router project
│   ├── app/           # Pages & layouts
│   │   ├── page.tsx             # Landing page
│   │   ├── auth/login/          # Login
│   │   ├── auth/signup/         # Sign up
│   │   └── dashboard/           # Protected dashboard
│   │       ├── page.tsx         # Dashboard home
│   │       ├── upload/          # Data upload
│   │       └── graph/           # Knowledge graph view
│   ├── components/    # Reusable React components
│   │   ├── ui/        # GlassCard, Button, ParticleBackground
│   │   ├── landing/   # HeroSection
│   │   ├── dashboard/ # DashboardShell, UploadClient, GraphPageClient
│   │   └── graph/     # KnowledgeGraph (WebGL), LearnNextPanel
│   ├── lib/           # Supabase helpers, API client
│   ├── middleware.ts  # Auth middleware (protects /dashboard)
│   └── types/         # Shared TypeScript types
│
├── backend/           # FastAPI Python service
│   └── app/
│       ├── main.py              # App factory & lifespan
│       ├── core/                # Config, security, Neo4j driver
│       ├── api/routes/          # health, ingest, graph, recommendations
│       ├── models/              # Pydantic v2 models
│       └── services/
│           ├── ingestion/       # Parser + PII scrubber
│           ├── ai/              # LangChain extractor + async queue
│           └── graph/           # Neo4j ingestion + recommendations
│
└── database/
    ├── supabase/schema.sql      # Postgres schema + RLS policies
    └── neo4j/
        ├── constraints.cypher         # Uniqueness constraints & indexes
        ├── seed_master_nodes.cypher   # Seed ~70 human-knowledge topic nodes
        └── idempotent_ingestion.cypher  # Annotated MERGE-based ingestion example
```

---

## Quick Start

### 1. Clone & configure environment

```bash
# Frontend
cp frontend/.env.example frontend/.env.local
# Fill in NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY

# Backend
cp backend/.env.example backend/.env
# Fill in all keys (Supabase, Neo4j, Gemini)
```

### 2. Set up databases

**Supabase**: Run `database/supabase/schema.sql` in the SQL editor of your Supabase project.

**Neo4j AuraDB**: Connect to your AuraDB instance and run:
1. `database/neo4j/constraints.cypher` — creates uniqueness constraints & indexes
2. `database/neo4j/seed_master_nodes.cypher` — seeds the master human-knowledge graph

### 3. Run the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Health check: `GET /health` | Keep-alive ping: `GET /health/ping`

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

---

## Core Architecture

### Shared Master Node (Neo4j)

To stay within the AuraDB Free tier's 200 k node limit, entity nodes are **shared globally** across all users.  
When two users both mention "Python", they point to the **same** `Entity {name: "Python", type: "TECH"}` node — no duplicates.

```cypher
// ✅ Idempotent — safe to call multiple times
MERGE (u:User {id: $user_id})
MERGE (e:Entity {name: $name, type: $type})
MERGE (u)-[r:INTERESTED_IN]->(e)
SET r.weight = $weight, r.updated = datetime()
```

### Ingestion Pipeline

```
Upload (.zip / .json)
  └─► Parser          (extract text from known export formats)
       └─► PII Scrubber (regex-based — no heavy ML deps)
            └─► AI Extractor  (LangChain + Gemini, batched + rate-limited)
                 └─► Neo4j Ingestion (MERGE-only, idempotent)
                      └─► Supabase job status update
```

### Rate Limiting (Free Tier Safe)

An `asyncio.Semaphore(3)` ensures a maximum of **3 concurrent Gemini API calls** at any time, with a 1-second delay between job submissions — keeping the app within Gemini's free-tier RPM limits even under concurrent user load.

---

## Deployment

| Service | Platform | Notes |
|---------|----------|-------|
| Frontend | Cloudflare Pages | `npm run build` → `out/` directory |
| Backend | Render Free Web Service | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Postgres | Supabase Free | 500 MB limit |
| Knowledge Graph | Neo4j AuraDB Free | 200 k nodes / 400 k edges |

### Preventing Render cold starts

Set up a cron-job (e.g., cron-job.org — free) to ping `GET /health/ping` every 14 minutes.

---

## UI Theme — "Elegant Glass & Tech Lines"

- **Background**: Deep obsidian black (`#0a0a0f`) + midnight blue (`#0d1117`)  
- **Panels**: Glassmorphism — `backdrop-blur`, `bg-white/5`, `border-white/10`  
- **Accents**: Neon blue (`#3b82f6`) and neon purple (`#8b5cf6`) glows  
- **Motion**: Framer Motion stagger animations, smooth camera zoom-out on the graph  
- **Typography**: Inter / Geist sans-serif