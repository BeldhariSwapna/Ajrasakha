"""MongoDB Database connection and data access layer for Farmer Feedback System.

Features:
- Automatic discovery of .env across project subdirectories.
- Resilient connection to MongoDB Atlas or local MongoDB.
- Built-in In-Memory Fallback if MongoDB is unreachable (ensures testing/demo stability).
"""

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Search for .env files in common locations
for candidate in [
    Path(__file__).parent / ".env",
    Path(__file__).resolve().parents[2] / "backend" / ".env",
    Path(__file__).resolve().parents[3] / ".env",
]:
    if candidate.exists():
        load_dotenv(candidate)

MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("DB_URL") or "mongodb://localhost:27017"
DB_NAME = os.getenv("DB_NAME", "agriai")

FEEDBACK_COLLECTION = "farmer_feedback"
SESSIONS_COLLECTION = "farmer_feedback_sessions"
FLAGGED_COLLECTION = "flagged_gdb_entries"

_client = None
_use_in_memory = False
_in_memory_store: Dict[str, List[Dict[str, Any]]] = {
    FEEDBACK_COLLECTION: [],
    SESSIONS_COLLECTION: [],
    FLAGGED_COLLECTION: [],
}


class MockCollection:
    """In-memory collection mock for offline testing and fallback."""

    def __init__(self, name: str):
        self.name = name

    def insert_one(self, doc: Dict[str, Any]):
        doc_copy = dict(doc)
        if "_id" not in doc_copy:
            doc_copy["_id"] = str(uuid.uuid4())
        _in_memory_store[self.name].append(doc_copy)
        
        class Result:
            inserted_id = doc_copy["_id"]
        return Result()

    def find_one(self, filter_dict: Dict[str, Any]):
        for doc in _in_memory_store[self.name]:
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    def find(self, filter_dict: Optional[Dict[str, Any]] = None):
        filter_dict = filter_dict or {}
        results = []
        for doc in _in_memory_store[self.name]:
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(dict(doc))

        class Cursor(list):
            def sort(self, key, order=1):
                return self
        return Cursor(results)

    def count_documents(self, filter_dict: Optional[Dict[str, Any]] = None):
        filter_dict = filter_dict or {}
        if not filter_dict:
            return len(_in_memory_store[self.name])
        count = 0
        for doc in _in_memory_store[self.name]:
            match = True
            for k, v in filter_dict.items():
                if k == "created_at" and isinstance(v, dict):
                    # date comparison
                    if "$gte" in v and doc.get("created_at") < v["$gte"]:
                        match = False
                elif doc.get(k) != v:
                    match = False
                    break
            if match:
                count += 1
        return count

    def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any], upsert: bool = False):
        found = False
        class UpdateResult:
            modified_count = 1

        for doc in _in_memory_store[self.name]:
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                if "$set" in update_dict:
                    doc.update(update_dict["$set"])
                found = True
                return UpdateResult()

        if not found and upsert:
            new_doc = dict(filter_dict)
            if "$set" in update_dict:
                new_doc.update(update_dict["$set"])
            new_doc["_id"] = str(uuid.uuid4())
            _in_memory_store[self.name].append(new_doc)
            return UpdateResult()

        res = UpdateResult()
        res.modified_count = 0 if not found else 1
        return res

    def delete_many(self, filter_dict: Dict[str, Any]):
        _in_memory_store[self.name] = []

    def distinct(self, key: str, filter_dict: Optional[Dict[str, Any]] = None):
        values = set()
        for doc in _in_memory_store[self.name]:
            if key in doc:
                values.add(doc[key])
        return list(values)

    def aggregate(self, pipeline: List[Dict[str, Any]]):
        """Basic aggregation implementation for fallback."""
        docs = list(_in_memory_store[self.name])
        
        # Simple grouping by _id field for common pipeline
        for stage in pipeline:
            if "$match" in stage:
                cond = stage["$match"]
                if cond:
                    filtered = []
                    for d in docs:
                        m = True
                        for k, v in cond.items():
                            if k == "$or" and isinstance(v, list):
                                submatch = False
                                for clause in v:
                                    for ck, cv in clause.items():
                                        if isinstance(cv, dict) and "$regex" in cv:
                                            import re
                                            pattern = cv["$regex"]
                                            if re.search(pattern, str(d.get(ck, "")), re.IGNORECASE):
                                                submatch = True
                                if not submatch:
                                    m = False
                            elif k == "created_at" and isinstance(v, dict):
                                if "$gte" in v and d.get("created_at") < v["$gte"]:
                                    m = False
                            elif k == "total_responses" and isinstance(v, dict):
                                if "$gte" in v and d.get("total_responses", 0) < v["$gte"]:
                                    m = False
                            elif k == "total" and isinstance(v, dict):
                                val = d.get("total", d.get("total_responses", 0))
                                if "$gte" in v and val < v["$gte"]:
                                    m = False
                            elif k == "helpfulness_rate" and isinstance(v, dict):
                                if "$lt" in v and d.get("helpfulness_rate", 1.0) >= v["$lt"]:
                                    m = False
                            elif d.get(k) != v and d.get(k) is not None:
                                m = False
                        if m:
                            filtered.append(d)
                    docs = filtered
            elif "$group" in stage:
                group_key = stage["$group"]["_id"]
                grouped = {}
                for d in docs:
                    key_val = d.get(group_key.replace("$", "")) if isinstance(group_key, str) and group_key.startswith("$") else "all"
                    if key_val not in grouped:
                        grouped[key_val] = {
                            "_id": key_val,
                            "total": 0,
                            "total_responses": 0,
                            "positive": 0,
                            "positive_count": 0,
                            "negative": 0,
                            "negative_count": 0,
                            "sample_query": d.get("query", ""),
                            "sample_answer": d.get("answer", ""),
                            "crop": d.get("crop", "General"),
                            "domain": d.get("domain", "General"),
                            "state": d.get("state", "All"),
                            "language": d.get("language", "en"),
                        }
                    grouped[key_val]["total"] += 1
                    grouped[key_val]["total_responses"] += 1
                    if d.get("is_helpful") is True:
                        grouped[key_val]["positive"] += 1
                        grouped[key_val]["positive_count"] += 1
                    else:
                        grouped[key_val]["negative"] += 1
                        grouped[key_val]["negative_count"] += 1
                
                # Add helpfulness_rate (decimal 0.0 - 1.0)
                for g in grouped.values():
                    tot = g["total_responses"]
                    pos = g["positive_count"]
                    g["helpfulness_rate"] = round(pos / tot, 4) if tot > 0 else 0.0

                docs = list(grouped.values())

            elif "$sort" in stage:
                sort_dict = stage["$sort"]
                for k, order in reversed(list(sort_dict.items())):
                    reverse = (order == -1)
                    docs.sort(key=lambda x: x.get(k, 0), reverse=reverse)

            elif "$limit" in stage:
                docs = docs[:stage["$limit"]]

        return docs


def get_collection(collection_name: str):
    """Retrieve collection instance with transparent fallback."""
    global _client, _use_in_memory
    if _use_in_memory:
        return MockCollection(collection_name)

    try:
        from pymongo import MongoClient
        if _client is None:
            _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
            _client.admin.command('ping')
        return _client[DB_NAME][collection_name]
    except Exception as e:
        # Fallback to in-memory store
        _use_in_memory = True
        return MockCollection(collection_name)


def save_feedback(feedback_data: Dict[str, Any]) -> str:
    """Insert a feedback document and return string ID."""
    coll = get_collection(FEEDBACK_COLLECTION)
    if "created_at" not in feedback_data:
        feedback_data["created_at"] = datetime.utcnow()
    res = coll.insert_one(feedback_data)
    return str(res.inserted_id)


def create_or_update_session(farmer_phone: str, session_data: Dict[str, Any]) -> None:
    """Store or update pending prompt session for a farmer phone number."""
    coll = get_collection(SESSIONS_COLLECTION)
    coll.update_one(
        {"farmer_phone": farmer_phone},
        {"$set": {**session_data, "updated_at": datetime.utcnow()}},
        upsert=True,
    )


def get_pending_session(farmer_phone: str) -> Optional[Dict[str, Any]]:
    """Get active pending session waiting for response from this farmer."""
    coll = get_collection(SESSIONS_COLLECTION)
    session = coll.find_one({"farmer_phone": farmer_phone, "status": "pending"})
    if session is None:
        session = coll.find_one({"farmer_phone": farmer_phone, "status": "awaiting_reason"})
    return session


def update_session(farmer_phone: str, updates: Dict[str, Any]) -> None:
    """Update the active WhatsApp feedback session."""
    coll = get_collection(SESSIONS_COLLECTION)
    coll.update_one({"farmer_phone": farmer_phone}, {"$set": {**updates, "updated_at": datetime.utcnow()}})


def update_feedback_reason(feedback_id: str, reason: str) -> None:
    """Attach a categorized explanation to previously recorded negative feedback."""
    coll = get_collection(FEEDBACK_COLLECTION)
    record_id: Any = feedback_id
    try:
        from bson import ObjectId
        record_id = ObjectId(feedback_id)
    except (ImportError, TypeError, ValueError):
        pass
    coll.update_one({"_id": record_id}, {"$set": {"reason": reason}})


def close_session(farmer_phone: str) -> None:
    """Mark session as completed."""
    coll = get_collection(SESSIONS_COLLECTION)
    coll.update_one(
        {"farmer_phone": farmer_phone},
        {"$set": {"status": "completed", "completed_at": datetime.utcnow()}},
    )
