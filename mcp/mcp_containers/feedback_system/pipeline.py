"""Automated Flagging Pipeline for Low-Rated GDB Entries.

Monitors farmer feedback across all GDB answers and flags entries
with consistently low helpfulness scores (e.g., < 60% positive across 10+ responses)
so they are returned to the expert reviewer pipeline for re-evaluation.
"""

import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

from database import get_collection, FLAGGED_COLLECTION, FEEDBACK_COLLECTION

logger = logging.getLogger(__name__)

REVIEWER_API_URL = os.getenv("REVIEWER_API_URL", "http://localhost:9010/reviewer/upload")


def run_flagging_pipeline(
    min_responses: int = 10,
    min_positive_rate: float = 0.60,
    notify_reviewer_system: bool = True,
) -> Dict[str, Any]:
    """
    Evaluates all GDB entries in MongoDB and flags entries below the threshold.
    Condition: total_responses >= min_responses AND helpfulness_rate < min_positive_rate
    """
    feedback_coll = get_collection(FEEDBACK_COLLECTION)
    flagged_coll = get_collection(FLAGGED_COLLECTION)

    # MongoDB aggregation pipeline grouped by gdb_id
    pipeline = [
        {
            "$group": {
                "_id": "$gdb_id",
                "total_responses": {"$sum": 1},
                "positive_count": {
                    "$sum": {"$cond": [{"$eq": ["$is_helpful", True]}, 1, 0]}
                },
                "negative_count": {
                    "$sum": {"$cond": [{"$eq": ["$is_helpful", False]}, 1, 0]}
                },
                "sample_query": {"$first": "$query"},
                "sample_answer": {"$first": "$answer"},
                "domain": {"$first": "$domain"},
                "crop": {"$first": "$crop"},
                "state": {"$first": "$state"},
                "language": {"$first": "$language"},
                "last_feedback_at": {"$max": "$created_at"},
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
        {
            "$match": {
                "total_responses": {"$gte": min_responses},
                "helpfulness_rate": {"$lt": min_positive_rate},
            }
        },
    ]

    low_rated_entries = list(feedback_coll.aggregate(pipeline))
    newly_flagged_count = 0
    flagged_results = []

    for entry in low_rated_entries:
        gdb_id = str(entry["_id"])
        positive = entry["positive_count"]
        total = entry["total_responses"]
        rate = entry["helpfulness_rate"]
        pct = round(rate * 100, 1)

        flag_reason = (
            f"Consistently low farmer helpfulness: {pct}% positive "
            f"({positive}/{total} helpful) below {round(min_positive_rate * 100)}% threshold."
        )

        doc = {
            "gdb_id": gdb_id,
            "query": entry.get("sample_query", ""),
            "answer": entry.get("sample_answer", ""),
            "domain": entry.get("domain", "General Agriculture"),
            "crop": entry.get("crop", "General"),
            "state": entry.get("state", "All"),
            "language": entry.get("language", "en"),
            "total_responses": total,
            "positive_count": positive,
            "negative_count": entry["negative_count"],
            "helpfulness_rate": rate,
            "threshold": min_positive_rate,
            "flag_reason": flag_reason,
            "status": "pending_re_review",
            "last_evaluated_at": datetime.utcnow(),
        }

        # Check if already flagged
        existing = flagged_coll.find_one({"gdb_id": gdb_id})
        if not existing:
            doc["flagged_at"] = datetime.utcnow()
            flagged_coll.insert_one(doc)
            newly_flagged_count += 1
            logger.info(f"🚨 Flagged GDB Entry {gdb_id} for re-review! (Score: {pct}%)")
        else:
            flagged_coll.update_one(
                {"gdb_id": gdb_id},
                {"$set": {
                    "total_responses": total,
                    "positive_count": positive,
                    "negative_count": entry["negative_count"],
                    "helpfulness_rate": rate,
                    "flag_reason": flag_reason,
                    "last_evaluated_at": datetime.utcnow(),
                }}
            )

        flagged_results.append({
            "gdb_id": gdb_id,
            "crop": entry.get("crop"),
            "domain": entry.get("domain"),
            "total_responses": total,
            "helpfulness_rate": rate,
            "flag_reason": flag_reason,
        })

    return {
        "status": "pipeline_completed",
        "evaluated_at": datetime.utcnow().isoformat(),
        "thresholds_used": {
            "min_responses": min_responses,
            "min_positive_rate": min_positive_rate,
        },
        "total_flagged_in_system": flagged_coll.count_documents({"status": "pending_re_review"}),
        "newly_flagged_count": newly_flagged_count,
        "flagged_entries": flagged_results,
    }


def get_all_flagged_entries(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve flagged entries from the database."""
    coll = get_collection(FLAGGED_COLLECTION)
    query = {}
    if status:
        query["status"] = status
    cursor = coll.find(query).sort("helpfulness_rate", 1)
    
    entries = []
    for item in cursor:
        item["_id"] = str(item["_id"])
        entries.append(item)
    return entries


def update_flag_status(gdb_id: str, new_status: str, notes: Optional[str] = None) -> bool:
    """Update review status of a flagged entry (e.g. 'in_review', 'resolved')."""
    coll = get_collection(FLAGGED_COLLECTION)
    res = coll.update_one(
        {"gdb_id": gdb_id},
        {
            "$set": {
                "status": new_status,
                "reviewer_notes": notes,
                "updated_at": datetime.utcnow(),
            }
        },
    )
    return res.modified_count > 0
