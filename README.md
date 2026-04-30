# Bike Troubleshooting Bot

A web app that lets a bike owner upload the official Owner's / Service Manual for their bike and ask troubleshooting questions in plain English — with optional photo input. The bot answers **strictly from the manual**. If the manual doesn't cover the question, it says so instead of guessing.

Built as an interview project. Stack: **FastAPI + React (Vite) + Claude (vision)**.

---

## What it does

- **Upload any bike's PDF manual** (Royal Enfield, TVS, Honda, Yamaha…) and start chatting.
- **Ask questions in natural language** — "Why is my bike making a clicking sound when I press the starter?"
- **Attach a photo** (warning light, leak, smoke) and the bot will identify the symptom and look it up.
- **Page-cited answers** — every claim is tied to a specific page from the uploaded manual.
- **Refuses to hallucinate** — if it's not in the manual, it tells you that, and offers the closest related section.

---

## Architecture

```
┌──────────────────┐         ┌────────────────────┐         ┌────────────────┐
│  React (Vite)    │ ──────▶ │   FastAPI backend  │ ──────▶ │  Claude API    │
│  - Upload UI     │  HTTPS  │   - PDF extract    │  HTTPS  │  (vision +     │
│  - Chat UI       │         │   - Manual store   │         │   prompt cache)│
│  - Image attach  │         │   - Grounded prompt│         │                │
└──────────────────┘         └────────────────────┘         └────────────────┘
```

### Why no traditional RAG (chunking + embeddings + vector DB)?

This is the most interesting design decision in the project, so let me explain.

A typical "chat with my PDF" tutorial builds a RAG pipeline: chunk the PDF into ~500-token pieces, embed each chunk, store in a vector DB, retrieve the top-k for each query, and stuff them into the prompt.

For **bounded technical documents like bike manuals**, that's the wrong tool:

| Concern | Traditional RAG | This app (full-context + cache) |
|---|---|---|
| Retrieval misses | Common — relevant chunk may not be top-k | Impossible — entire manual is in context |
| Cross-page reasoning ("symptom on p. 30, fix on p. 80") | Often broken | Works naturally |
| Citations | Approximate (chunk → page mapping is fuzzy) | Exact — pages are tagged in the prompt |
| Cost | Embedding API + vector DB + per-query LLM | One full read, then cached at ~10% cost |
| Operational complexity | Embeddings, vector DB, sync, eviction | A `dict` |
| Best for | Corpora >> 200K tokens | Single bounded documents (manuals, policies, contracts) |

The Royal Enfield Guerrilla 450 manual used during development is **142 pages, ~28K tokens** — well inside Claude's 200K context window. The first question pays for the full manual; every subsequent question pays only for the cached read (≈10% of the input cost).

**Fallback**: if a manual exceeds ~150K tokens (very thick service manuals), the right next move is to chunk by section and add BM25 retrieval on top — keeping Claude as the answering layer. Hooks for this are already there (`store.Manual.pages` is a list of pages), but it isn't implemented in this build.

### How hallucination is prevented

Three layers:

1. **System prompt** (`backend/app/prompts.py`) defines a strict contract: only use the manual; cite pages for every claim; explicitly say "this is not covered in the manual" otherwise; never invent page numbers.
2. **The manual itself is in the prompt**, wrapped in `<page number="N">` XML tags so the model can produce real citations.
3. **The UI surfaces page citations as visible chips** — if the model invents a page number, you'll catch it instantly.

### How images work

When the user attaches a photo, it's sent in the same Claude message as the text question. Claude's vision component identifies what's in the image (e.g. "white smoke from the exhaust", "ABS warning light", "oil pooling under engine"), then the same grounded contract kicks in: look it up in the manual, answer from the manual, refuse if not present.

---

## Project layout

```
bike project/
├── README.md
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS
│   │   ├── config.py            # env-var loading
│   │   ├── prompts.py           # the grounded system prompt
│   │   ├── store.py             # in-memory manual store
│   │   ├── routes/
│   │   │   ├── manuals.py       # POST /api/manuals (upload)
│   │   │   └── chat.py          # POST /api/chat
│   │   └── services/
│   │       ├── pdf.py           # pypdf text extraction
│   │       └── claude.py        # Anthropic client + prompt caching
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── render.yaml              # Render blueprint
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   └── components/
    │       ├── ManualUpload.jsx
    │       └── ChatScreen.jsx
    ├── index.html
    ├── package.json
    ├── tailwind.config.js
    ├── vite.config.js
    ├── vercel.json
    └── .env.example
```

---

## Running locally

### 1. Get an Anthropic API key
Create one at https://console.anthropic.com/. Add some credit (a few dollars covers heavy testing).

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set ANTHROPIC_API_KEY=sk-ant-...

uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for the interactive API docs.

### 3. Frontend

```bash
cd frontend
npm install

cp .env.example .env
# default VITE_API_URL=http://localhost:8000 is fine for local dev

npm run dev
```

Open http://localhost:5173 in your browser.

---

## Deploying to a hosted demo URL

### Backend → Render (free tier)

1. Push this repo to GitHub.
2. In Render: **New +** → **Blueprint** → pick the repo. It will detect `backend/render.yaml`.
3. After the service is created, open it in the dashboard and set:
   - `ANTHROPIC_API_KEY` = your key
   - `ALLOWED_ORIGINS` = your Vercel frontend URL (set this *after* the frontend is deployed)
4. Wait for the first deploy. Hit `https://<your-service>.onrender.com/api/health` to confirm.

> Render's free tier sleeps after inactivity. The first request after a sleep takes ~30s. Mention this to your interviewer or warm it up before the demo.

### Frontend → Vercel

1. In Vercel: **Add New** → **Project** → import the repo.
2. Set **Root Directory** to `frontend`. Vercel will pick up `vercel.json` automatically.
3. Add an env var: `VITE_API_URL` = your Render URL (no trailing slash).
4. Deploy. Copy the resulting URL and put it back into Render's `ALLOWED_ORIGINS`.

### Wrap-up
Visit the Vercel URL, upload a manual, ask a question.

---

## Demo script (3 minutes)

Use these to show off the bot in an interview:

1. **In-manual question (text only)**
   *"How often should I change the engine oil?"*
   → Bot quotes the service interval and cites the page.

2. **Out-of-manual question**
   *"Can I install a turbocharger on this bike?"*
   → Bot says it's not covered, optionally points to the closest related section (e.g., recommended modifications / warranty).

3. **Image-based question**
   Attach a stock photo of a motorcycle dashboard with the ABS warning lit. Ask: *"What does this light mean and what should I do?"*
   → Bot identifies the warning light, looks up the section in the manual, and explains.

4. **Safety question**
   *"My bike won't start and I smell fuel — what should I do?"*
   → Bot leads with safety warnings from the manual before any diagnostic steps.

---

## Trade-offs and what I'd do next

- **In-memory store** — fine for a single-instance demo, dies on restart. For production: Postgres + S3 for the original PDFs, with Redis for the parsed-text cache.
- **No streaming** — the chat endpoint waits for the full Claude response. Adding streaming (`stream=True`) would feel snappier on long answers.
- **No conversation memory** — each question is stateless. Threading prior turns into the prompt is a 10-line change but I left it out to keep the grounding tight (multi-turn makes hallucination harder to control).
- **No OCR** — scanned PDFs (image-only) won't extract any text. Adding Tesseract or Anthropic's PDF support to the upload pipeline would handle this.
- **Eval harness** — for production I'd build a small eval set ("questions that should be answered", "questions that should be refused", "questions that need citations") and gate prompt changes on it.

