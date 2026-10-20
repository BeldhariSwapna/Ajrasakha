"""FastAPI REST Service for Farmer Answer Feedback Loop.

Exposes endpoints for:
- WhatsApp bot feedback capture & webhook
- Real-time feedback analytics (per GDB, domain, language, state)
- Automated flagging pipeline triggering re-review
- Weekly digest reports for the agriculture team
"""

import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Body, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models import (
    FarmerFeedbackCreate,
    FeedbackPromptRequest,
    WhatsAppWebhookPayload,
    FlaggingConfig,
    FeedbackSummary,
    GDBEntryHelpfulness,
    BreakdownItem,
)
from database import (
    save_feedback,
    get_collection,
    FEEDBACK_COLLECTION,
    FLAGGED_COLLECTION,
)
from bot_handler import initiate_feedback_prompt, handle_incoming_message
from pipeline import run_flagging_pipeline, get_all_flagged_entries, update_flag_status
from digest import generate_weekly_digest

app = FastAPI(
    title="AjraSakha Farmer Feedback API",
    version="1.0.0",
    description="Captures farmer feedback from WhatsApp, provides analytics, and flags low-rated GDB entries.",
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "farmer-feedback-system", "version": "1.0.0"}


# ==========================================
# 1. WhatsApp Feedback Capture Endpoints
# ==========================================

@app.post("/api/feedback/prompt", tags=["WhatsApp Bot"])
async def trigger_feedback_prompt(payload: FeedbackPromptRequest):
    """
    Trigger post-answer follow-up message on WhatsApp.
    Sends: 'Was this helpful? Reply 1 for Yes, 2 for No'
    """
    result = await initiate_feedback_prompt(
        farmer_phone=payload.farmer_phone,
        gdb_id=payload.gdb_id,
        query=payload.query,
        answer=payload.answer,
        domain=payload.domain or "General Agriculture",
        crop=payload.crop or "General",
        language=payload.language or "te",
        state=payload.state or "Telangana",
        district=payload.district,
    )
    return result


@app.post("/api/feedback/whatsapp-webhook", tags=["WhatsApp Bot"])
async def whatsapp_webhook(payload: WhatsAppWebhookPayload):
    """
    Webhook handler for incoming WhatsApp replies.
    Captures '1' (Yes) or '2' (No) from farmer and links to GDB entry.
    """
    result = await handle_incoming_message(
        from_phone=payload.from_phone,
        message_text=payload.message_text,
    )
    return result


@app.post("/api/feedback/submit", tags=["Feedback"])
def submit_direct_feedback(feedback: FarmerFeedbackCreate):
    """Directly insert a farmer feedback record."""
    data = feedback.model_dump()
    inserted_id = save_feedback(data)
    return {
        "status": "success",
        "feedback_id": inserted_id,
        "is_helpful": feedback.is_helpful,
    }


# ==========================================
# 2. Analytics Dashboard Endpoints
# ==========================================

@app.get("/api/feedback/analytics/summary", response_model=FeedbackSummary, tags=["Analytics"])
def get_feedback_summary():
    """Overall summary KPIs (total feedbacks, positive, negative, helpfulness %)."""
    feedback_coll = get_collection(FEEDBACK_COLLECTION)
    flagged_coll = get_collection(FLAGGED_COLLECTION)

    total = feedback_coll.count_documents({})
    positive = feedback_coll.count_documents({"is_helpful": True})
    negative = feedback_coll.count_documents({"is_helpful": False})
    rate = round(positive / total, 4) if total > 0 else 0.0

    unique_gdb = len(feedback_coll.distinct("gdb_id"))
    total_flagged = flagged_coll.count_documents({"status": "pending_re_review"})

    return FeedbackSummary(
        total_feedbacks=total,
        positive_count=positive,
        negative_count=negative,
        overall_helpfulness_rate=rate,
        total_unique_gdb_entries=unique_gdb,
        total_flagged_entries=total_flagged,
    )


@app.get("/api/feedback/analytics/by-gdb", tags=["Analytics"])
def get_helpfulness_by_gdb(
    search: Optional[str] = Query(None, description="Search by GDB ID or Query"),
    domain: Optional[str] = Query(None, description="Filter by Domain"),
    crop: Optional[str] = Query(None, description="Filter by Crop"),
    sort_by: str = Query("total_responses", description="total_responses | helpfulness_rate"),
    order: int = Query(-1, description="-1 for descending, 1 for ascending"),
    limit: int = Query(50, ge=1, le=200),
):
    """Helpfulness breakdown per specific GDB entry."""
    feedback_coll = get_collection(FEEDBACK_COLLECTION)
    flagged_coll = get_collection(FLAGGED_COLLECTION)

    match_filter: Dict[str, Any] = {}
    if domain:
        match_filter["domain"] = domain
    if crop:
        match_filter["crop"] = crop
    if search:
        match_filter["$or"] = [
            {"gdb_id": {"$regex": search, "$options": "i"}},
            {"query": {"$regex": search, "$options": "i"}},
        ]

    pipeline = [
        {"$match": match_filter} if match_filter else {"$match": {}},
        {
            "$group": {
                "_id": "$gdb_id",
                "sample_query": {"$first": "$query"},
                "sample_answer": {"$first": "$answer"},
                "crop": {"$first": "$crop"},
                "domain": {"$first": "$domain"},
                "state": {"$first": "$state"},
                "total_responses": {"$sum": 1},
                "positive_count": {
                    "$sum": {"$cond": [{"$eq": ["$is_helpful", True]}, 1, 0]}
                },
                "negative_count": {
                    "$sum": {"$cond": [{"$eq": ["$is_helpful", False]}, 1, 0]}
                },
            }
        },
        {
            "$addFields": {
                "helpfulness_rate": {
                    "$round": [
                        {"$divide": ["$positive_count", "$total_responses"]},
                        4,
                    ]
                }
            }
        },
        {"$sort": {sort_by: order}},
        {"$limit": limit},
    ]

    results = list(feedback_coll.aggregate(pipeline))
    flagged_ids = set(flagged_coll.distinct("gdb_id", {"status": "pending_re_review"}))

    formatted = []
    for item in results:
        gdb_id = str(item["_id"])
        formatted.append({
            "gdb_id": gdb_id,
            "sample_query": item.get("sample_query", ""),
            "sample_answer": item.get("sample_answer", ""),
            "crop": item.get("crop", "General"),
            "domain": item.get("domain", "General Agriculture"),
            "state": item.get("state", "All"),
            "total_responses": item["total_responses"],
            "positive_count": item["positive_count"],
            "negative_count": item["negative_count"],
            "helpfulness_rate": item["helpfulness_rate"],
            "is_flagged": gdb_id in flagged_ids,
        })

    return formatted


@app.get("/api/feedback/analytics/by-reason", tags=["Analytics"])
def get_negative_feedback_reasons():
    """Summarize why farmers rated answers as not helpful."""
    feedback_coll = get_collection(FEEDBACK_COLLECTION)
    counts: Dict[str, int] = {}
    for record in feedback_coll.find({"is_helpful": False}):
        reason = record.get("reason")
        if reason:
            counts[reason] = counts.get(reason, 0) + 1
    return [
        {"reason": reason, "count": count}
        for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


@app.get("/api/feedback/analytics/by-domain", response_model=List[BreakdownItem], tags=["Analytics"])
def get_helpfulness_by_domain():
    """Helpfulness breakdown per agricultural domain."""
    feedback_coll = get_collection(FEEDBACK_COLLECTION)
    pipeline = [
        {
            "$group": {
                "_id": {"$ifNull": ["$domain", "Unspecified"]},
                "total_responses": {"$sum": 1},
                "positive_count": {"$sum": {"$cond": ["$is_helpful", 1, 0]}},
                "negative_count": {"$sum": {"$cond": ["$is_helpful", 0, 1]}},
            }
        },
        {
            "$addFields": {
                "helpfulness_rate": {
                    "$round": [{"$divide": ["$positive_count", "$total_responses"]}, 4]
                }
            }
        },
        {"$sort": {"total_responses": -1}},
    ]
    data = list(feedback_coll.aggregate(pipeline))
    return [
        BreakdownItem(
            category=str(d["_id"]),
            total_responses=d["total_responses"],
            positive_count=d["positive_count"],
            negative_count=d["negative_count"],
            helpfulness_rate=d["helpfulness_rate"],
        )
        for d in data
    ]


@app.get("/api/feedback/analytics/by-language", response_model=List[BreakdownItem], tags=["Analytics"])
def get_helpfulness_by_language():
    """Helpfulness breakdown per language."""
    feedback_coll = get_collection(FEEDBACK_COLLECTION)
    pipeline = [
        {
            "$group": {
                "_id": {"$ifNull": ["$language", "en"]},
                "total_responses": {"$sum": 1},
                "positive_count": {"$sum": {"$cond": ["$is_helpful", 1, 0]}},
                "negative_count": {"$sum": {"$cond": ["$is_helpful", 0, 1]}},
            }
        },
        {
            "$addFields": {
                "helpfulness_rate": {
                    "$round": [{"$divide": ["$positive_count", "$total_responses"]}, 4]
                }
            }
        },
        {"$sort": {"total_responses": -1}},
    ]
    data = list(feedback_coll.aggregate(pipeline))
    return [
        BreakdownItem(
            category=str(d["_id"]).upper(),
            total_responses=d["total_responses"],
            positive_count=d["positive_count"],
            negative_count=d["negative_count"],
            helpfulness_rate=d["helpfulness_rate"],
        )
        for d in data
    ]


@app.get("/api/feedback/analytics/by-state", response_model=List[BreakdownItem], tags=["Analytics"])
def get_helpfulness_by_state():
    """Helpfulness breakdown per state."""
    feedback_coll = get_collection(FEEDBACK_COLLECTION)
    pipeline = [
        {
            "$group": {
                "_id": {"$ifNull": ["$state", "All"]},
                "total_responses": {"$sum": 1},
                "positive_count": {"$sum": {"$cond": ["$is_helpful", 1, 0]}},
                "negative_count": {"$sum": {"$cond": ["$is_helpful", 0, 1]}},
            }
        },
        {
            "$addFields": {
                "helpfulness_rate": {
                    "$round": [{"$divide": ["$positive_count", "$total_responses"]}, 4]
                }
            }
        },
        {"$sort": {"total_responses": -1}},
    ]
    data = list(feedback_coll.aggregate(pipeline))
    return [
        BreakdownItem(
            category=str(d["_id"]),
            total_responses=d["total_responses"],
            positive_count=d["positive_count"],
            negative_count=d["negative_count"],
            helpfulness_rate=d["helpfulness_rate"],
        )
        for d in data
    ]


# ==========================================
# 3. Automated Flagging Pipeline Endpoints
# ==========================================

@app.post("/api/feedback/run-flagging", tags=["Flagging Pipeline"])
def execute_flagging_pipeline(config: FlaggingConfig = Body(...)):
    """
    Run automated pipeline to flag entries below threshold:
    e.g. less than 60% positive across 10+ responses.
    """
    result = run_flagging_pipeline(
        min_responses=config.min_responses,
        min_positive_rate=config.min_positive_rate,
    )
    return result


@app.get("/api/feedback/flagged", tags=["Flagging Pipeline"])
def list_flagged_entries(status: Optional[str] = Query(None)):
    """Fetch list of low-rated GDB entries flagged for reviewer queue."""
    return get_all_flagged_entries(status=status)


@app.patch("/api/feedback/flagged/{gdb_id}/status", tags=["Flagging Pipeline"])
def update_status(
    gdb_id: str,
    new_status: str = Body(..., embed=True),
    notes: Optional[str] = Body(None, embed=True),
):
    """Update status of a flagged entry after expert re-review."""
    success = update_flag_status(gdb_id, new_status, notes)
    if not success:
        raise HTTPException(status_code=404, detail="Flagged entry not found")
    return {"status": "updated", "gdb_id": gdb_id, "new_status": new_status}


# ==========================================
# 4. Weekly Digest & Agri Team Report
# ==========================================

@app.get("/api/feedback/weekly-digest", tags=["Digest"])
def get_weekly_digest(days: int = Query(7, ge=1, le=30)):
    """Generate weekly feedback digest and analysis report for the Agri team."""
    return generate_weekly_digest(days=days)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=9020, reload=True)
