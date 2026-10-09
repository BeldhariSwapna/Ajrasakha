# 🌾 Project 5: Farmer Answer Feedback Loop System

A feedback loop mechanism connecting farmer experience directly to the **Golden Database (GDB)** and the **Reviewer Pipeline** in AjraSakha.

---

## 📌 Problem Addressed
ACE has 20,000+ expert-validated answers in the GDB, but previously had no structured channel to capture whether farmers actually found answers helpful on WhatsApp. An answer can be scientifically accurate but still too technical, lengthy, or missing regional specificity.

This system closes the loop:
1. Captures farmer feedback immediately after answer delivery on WhatsApp.
2. Links feedback directly to the retrieved GDB entry ID.
3. Automatically flags consistently underperforming entries (< 60% helpful over 10+ replies) and pushes them to the Reviewer Pipeline.
4. Generates weekly analytical digests for agricultural specialists.

---

## 🏗️ Architecture & Component Overview

```
                      [ Farmer on WhatsApp ]
                               │
            1. Asks Query      │  2. Delivers GDB Answer
                               ▼
                        [ AjraSakha Bot ]
                               │
            3. Follow-up: "Was this helpful?
               Reply 1 for Yes, 2 for No"
                               │
            4. Farmer Replies: "1" or "2"
                               ▼
        ┌──────────────────────────────────────────────┐
        │        FastAPI Feedback Microservice         │
        │             (Port: 9020)                     │
        └──────────────────────┬───────────────────────┘
                               │
                 Stores in MongoDB Collections:
        • farmer_feedback
        • farmer_feedback_sessions
        • flagged_gdb_entries
                               │
          ┌────────────────────┴─────────────────────┐
          ▼                                          ▼
   [ Automated Flagging Pipeline ]           [ Analytics API ]
   Threshold: < 60% over 10+ reviews                  │
          │                                          ▼
          ▼                                [ React Feedback Dashboard ]
   [ Expert Reviewer Queue ]               • GDB Performance Table
   (desk.vicharanashala.ai)                • Domain, State, Language Breakdown
                                           • Agri Team Weekly Digest
```

---

## 🚀 Quickstart & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python test_feedback.py
```

### 3. Seed Week 1 Feedback Data & Generate Report
```bash
python seed_data.py
```
This populates realistic sample feedback across diverse crops, domains, states, and languages, evaluates the automated flagging pipeline, and writes `WEEK_1_FEEDBACK_ANALYSIS_REPORT.md`.

### 4. Start FastAPI Service
```bash
python api.py
# Or with uvicorn:
uvicorn api:app --host 0.0.0.0 --port 9020 --reload
```
Interactive API docs available at: `http://localhost:9020/docs`

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/feedback/prompt` | Triggers post-answer WhatsApp follow-up message |
| `POST` | `/api/feedback/whatsapp-webhook` | Ingests incoming WhatsApp replies ('1' or '2') |
| `POST` | `/api/feedback/submit` | Direct feedback creation (for UI / testing) |
| `GET` | `/api/feedback/analytics/summary` | Overall KPI summary (helpful/not helpful ratio) |
| `GET` | `/api/feedback/analytics/by-gdb` | Helpfulness scores per specific GDB entry |
| `GET` | `/api/feedback/analytics/by-domain` | Helpfulness breakdown per agricultural domain |
| `GET` | `/api/feedback/analytics/by-language` | Helpfulness breakdown per language |
| `GET` | `/api/feedback/analytics/by-state` | Helpfulness breakdown per state |
| `POST` | `/api/feedback/run-flagging` | Runs automated flagging pipeline on configurable threshold |
| `GET` | `/api/feedback/flagged` | Returns queue of flagged entries for re-review |
| `GET` | `/api/feedback/weekly-digest` | Generates weekly analytical digest for the Agri team |

---

## 🐳 Docker Deployment
Add to docker-compose:
```bash
docker compose -f ../docker-compose.yml up -d feedback-system
```
