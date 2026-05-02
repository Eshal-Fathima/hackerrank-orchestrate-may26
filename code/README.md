# 🤖 Support Triage Agent — HackerRank Orchestrate 2026

A production-grade, terminal-based AI support triage agent that intelligently classifies, routes, and responds to support tickets across **HackerRank**, **Claude (Anthropic)**, and **Visa** — using only the provided local corpus. No hallucinations. No guessing. No live web calls.

---

## 🏗️ Architecture Overview

```
support_tickets.csv
        │
        ▼
┌─────────────────────────────────────────────────────┐
│                    main.py                          │
│            Orchestrator / Entry Point               │
└──────────────────┬──────────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌─────────────┐       ┌─────────────────────────────┐
│ retriever.py│       │       classifier.py          │
│             │       │                              │
│  TF-IDF     │──────▶│  1. Safety Pre-Check (regex) │
│  Corpus     │       │  2. Out-of-scope detection   │
│  Retriever  │       │  3. Groq LLM (70B) call      │
│             │       │  4. JSON validation          │
└─────────────┘       └─────────────────────────────┘
                                   │
                                   ▼
                           output.csv ✅
```

### Three-Layer Decision Pipeline

| Layer | What it does | Why |
|---|---|---|
| **Layer 1 — Safety Pre-check** | Regex patterns catch fraud, prompt injection, security vulns, PII before any LLM call | Fast, deterministic, zero hallucination risk |
| **Layer 2 — RAG Retrieval** | TF-IDF scores all corpus chunks, boosts results from the matching company | Grounds every response in real documentation |
| **Layer 3 — LLM Triage** | Groq llama-3.3-70b-versatile classifies, routes, and generates the response | Handles nuance, multi-language, edge cases |

---

## 🧠 Key Design Decisions

### Why TF-IDF over a vector database?
Zero setup, zero dependencies, deterministic results. The corpus is markdown files — TF-IDF with overlapping chunks retrieves the right content reliably without needing embeddings, a vector store, or an internet connection. It also runs instantly on cold start.

### Why Groq llama-3.3-70b-versatile?
- **70B parameters** — smart enough to handle nuanced triage (fraud signals, multi-language, prompt injection, cross-domain tickets)
- **32k context window** — fits corpus chunks + full ticket comfortably
- **Free tier** — 14,400 requests/day, 30 req/min
- **Groq hardware** — inference is near-instant even at 70B scale

### Why regex safety checks before the LLM?
LLMs can be manipulated. For high-risk signals (prompt injection, fraud, security vulnerabilities, legal matters), we don't even give the LLM a chance to reason its way into a bad response. The regex layer is deterministic and cannot be jailbroken.

### Why overlapping chunks?
Support documentation often has answers that span paragraph boundaries. Overlapping chunks (400 words, 80-word overlap) ensures important context is never split at a chunk boundary.

---

## 🛡️ Safety & Escalation Logic

The agent escalates automatically when any of these are detected:

| Category | Examples |
|---|---|
| **Prompt injection** | "show me your internal rules", "ignore previous instructions" |
| **Fraud signals** | "unauthorized charge", "card stolen/compromised" |
| **Financial urgency** | "urgent cash", "emergency funds" |
| **Account security** | "hacked", "account compromised", "account breach" |
| **Security research** | "security vulnerability", "bug bounty", "zero-day" |
| **Legal/compliance** | "lawsuit", "GDPR", "data breach", "subpoena" |
| **Self-harm** | Any related signals |

Out-of-scope tickets (unrelated to HackerRank, Claude, or Visa) get a polite replied with invalid request type — never silently dropped.

---

## 📁 File Structure

```
code/
├── main.py          # Entry point — orchestrates the full pipeline
├── retriever.py     # TF-IDF corpus loader + chunk retriever
├── classifier.py    # Safety checks + Groq LLM triage
└── README.md        # This file
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8+
- A free Groq API key

### 1. Get a free Groq API key
Sign up at https://console.groq.com/keys and create a new key.

Free tier: **30 requests/min · 14,400 requests/day**

### 2. Install the Groq SDK

```bash
pip install groq
```

That is the only dependency.

### 3. Set your API key

**macOS / Linux:**
```bash
export GROQ_API_KEY="gsk_your_key_here"
```

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY = "gsk_your_key_here"
```

---

## 🚀 Running the Agent

From the **repo root:**

```bash
python code/main.py
```

Or from inside code/:

```bash
cd code
python main.py
```

The agent will:
1. Load and index the entire data/ corpus
2. Process every ticket in support_tickets/support_tickets.csv
3. Write results to support_tickets/output.csv

**Expected output:**
```
[*] Loading corpus...
    Loaded 1842 document chunks from corpus.
[*] Processing 29 tickets...

  [1/29] Claude access lost...
  [2/29] Test Score Dispute...
  ...
  [29/29] Visa card minimum spend...

[✓] Done! Results written to: support_tickets/output.csv
```

---

## 📊 Output Schema

| Column | Type | Description |
|---|---|---|
| issue | string | Original ticket body |
| subject | string | Original ticket subject |
| company | string | HackerRank / Claude / Visa / None |
| status | replied or escalated | Whether agent answered or routed to human |
| product_area | string | Most relevant support category |
| response | string | User-facing answer grounded in corpus |
| justification | string | Internal reasoning for the decision |
| request_type | product_issue / feature_request / bug / invalid | Classification |

---

## 🌐 Edge Cases Handled

| Scenario | Handling |
|---|---|
| Empty tickets | Replied with request for more info, marked invalid |
| Non-English tickets | LLM responds in English, notes original language |
| company: None | LLM infers domain from ticket content |
| Multi-part tickets | LLM addresses the primary request |
| Prompt injection | Caught by regex pre-check, escalated before LLM call |
| Social engineering | "Show internal rules" escalated, no internal info disclosed |
| Out-of-scope requests | Polite decline, marked invalid |
| Corpus miss | Escalated rather than hallucinating an answer |

---

## 🔒 Security & Compliance

- **No secrets hardcoded** — API keys via environment variables only
- **No live web calls** — all retrieval from local data/ corpus only
- **No hallucination** — LLM instructed to escalate if corpus does not support the answer
- **Deterministic** — temperature set to 0.2 for consistent outputs
- **Append-only logging** — conversation log at ~/hackerrank_orchestrate/log.txt

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| groq | Groq SDK for LLM API calls |
| Python stdlib 3.8+ | Everything else (csv, json, re, pathlib, math) |

---

*Built for HackerRank Orchestrate Hackathon — May 1-2, 2026*