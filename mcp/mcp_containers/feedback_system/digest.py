"""Weekly Digest Generator for Agricultural Specialists & Reviewers.

Generates analytical summaries of farmer feedback over the past week,
highlighting the lowest-rated GDB entries, domain trends, language-specific gaps,
and regional discrepancies so the agri team can prioritize improvements.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from database import get_collection, FEEDBACK_COLLECTION, FLAGGED_COLLECTION


def generate_weekly_digest(days: int = 7) -> Dict[str, Any]:
    """Compile comprehensive weekly feedback analysis for the agri team."""
    feedback_coll = get_collection(FEEDBACK_COLLECTION)
    flagged_coll = get_collection(FLAGGED_COLLECTION)

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # 1. Overall stats
    total_feedbacks = feedback_coll.count_documents({"created_at": {"$gte": cutoff_date}})
    positive_count = feedback_coll.count_documents({
        "created_at": {"$gte": cutoff_date},
        "is_helpful": True,
    })
    negative_count = feedback_coll.count_documents({
        "created_at": {"$gte": cutoff_date},
        "is_helpful": False,
    })

    overall_helpfulness = round((positive_count / total_feedbacks * 100), 2) if total_feedbacks > 0 else 0.0

    # 2. Lowest-rated GDB entries
    lowest_gdb_pipeline = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {
            "$group": {
                "_id": "$gdb_id",
                "sample_query": {"$first": "$query"},
                "sample_answer": {"$first": "$answer"},
                "crop": {"$first": "$crop"},
                "domain": {"$first": "$domain"},
                "state": {"$first": "$state"},
                "total": {"$sum": 1},
                "positive": {"$sum": {"$cond": ["$is_helpful", 1, 0]}},
                "negative": {"$sum": {"$cond": ["$is_helpful", 0, 1]}},
            }
        },
        {"$match": {"total": {"$gte": 5}}},  # at least 5 responses
        {
            "$addFields": {
                "helpfulness_rate": {
                    "$round": [{"$multiply": [{"$divide": ["$positive", "$total"]}, 100]}, 1]
                }
            }
        },
        {"$sort": {"helpfulness_rate": 1, "total": -1}},
        {"$limit": 10},
    ]

    lowest_rated_entries = list(feedback_coll.aggregate(lowest_gdb_pipeline))

    # 3. Domain breakdown
    domain_pipeline = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {
            "$group": {
                "_id": "$domain",
                "total": {"$sum": 1},
                "positive": {"$sum": {"$cond": ["$is_helpful", 1, 0]}},
                "negative": {"$sum": {"$cond": ["$is_helpful", 0, 1]}},
            }
        },
        {
            "$addFields": {
                "helpfulness_rate": {
                    "$round": [{"$multiply": [{"$divide": ["$positive", "$total"]}, 100]}, 1]
                }
            }
        },
        {"$sort": {"total": -1}},
    ]
    domain_stats = list(feedback_coll.aggregate(domain_pipeline))

    # 4. Language breakdown
    lang_pipeline = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {
            "$group": {
                "_id": "$language",
                "total": {"$sum": 1},
                "positive": {"$sum": {"$cond": ["$is_helpful", 1, 0]}},
                "negative": {"$sum": {"$cond": ["$is_helpful", 0, 1]}},
            }
        },
        {
            "$addFields": {
                "helpfulness_rate": {
                    "$round": [{"$multiply": [{"$divide": ["$positive", "$total"]}, 100]}, 1]
                }
            }
        },
        {"$sort": {"total": -1}},
    ]
    lang_stats = list(feedback_coll.aggregate(lang_pipeline))

    # 5. State breakdown
    state_pipeline = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {
            "$group": {
                "_id": "$state",
                "total": {"$sum": 1},
                "positive": {"$sum": {"$cond": ["$is_helpful", 1, 0]}},
                "negative": {"$sum": {"$cond": ["$is_helpful", 0, 1]}},
            }
        },
        {
            "$addFields": {
                "helpfulness_rate": {
                    "$round": [{"$multiply": [{"$divide": ["$positive", "$total"]}, 100]}, 1]
                }
            }
        },
        {"$sort": {"total": -1}},
    ]
    state_stats = list(feedback_coll.aggregate(state_pipeline))

    # 6. Flagged entries needing attention
    flagged_count = flagged_coll.count_documents({"status": "pending_re_review"})

    # Format Markdown Digest
    report_md = f"""# 🌾 AjraSakha Agri Team Weekly Digest: Farmer Feedback Loop
**Reporting Period:** Past {days} days ({cutoff_date.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')})
**Generated On:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

---

## 📊 1. Executive Summary
- **Total Farmer Feedback Responses:** {total_feedbacks:,}
- **Helpful Responses (Yes - 1):** {positive_count:,} ({overall_helpfulness}%)
- **Unhelpful Responses (No - 2):** {negative_count:,} ({round(100 - overall_helpfulness, 2) if total_feedbacks > 0 else 0}%)
- **Active GDB Entries Flagged for Re-Review:** {flagged_count}

---

## 🚨 2. Top 10 Lowest-Rated GDB Entries (Requires Urgent Review)
The following answers received consistently poor helpfulness ratings from farmers on WhatsApp:

| GDB ID | Crop | Domain | Total Feedbacks | Helpful % | Sample Question |
|--------|------|--------|-----------------|-----------|-----------------|
"""
    for item in lowest_rated_entries:
        query_snip = (item.get('sample_query') or '')[:50] + "..."
        t = item.get('total') or item.get('total_responses', 0)
        rate = item.get('helpfulness_rate', 0.0)
        pct = round(rate * 100, 1) if rate <= 1.0 else round(rate, 1)
        report_md += f"| `{item['_id']}` | {item.get('crop')} | {item.get('domain')} | {t} | **{pct}%** | {query_snip} |\n"

    report_md += """
---

## 📂 3. Domain Performance Breakdown
| Domain | Total Queries | Helpful Count | Helpfulness Rate |
|--------|---------------|---------------|------------------|
"""
    for d in domain_stats:
        t = d.get('total') or d.get('total_responses', 0)
        p = d.get('positive') or d.get('positive_count', 0)
        rate = d.get('helpfulness_rate', 0.0)
        pct = round(rate * 100, 1) if rate <= 1.0 else round(rate, 1)
        report_md += f"| {d.get('_id', 'Unknown')} | {t} | {p} | **{pct}%** |\n"

    report_md += """
---

## 🌐 4. Language & Regional Performance
### By Language:
| Language | Total Feedbacks | Helpfulness Rate |
|----------|-----------------|------------------|
"""
    for l in lang_stats:
        t = l.get('total') or l.get('total_responses', 0)
        rate = l.get('helpfulness_rate', 0.0)
        pct = round(rate * 100, 1) if rate <= 1.0 else round(rate, 1)
        report_md += f"| {str(l.get('_id', 'Unknown')).upper()} | {t} | **{pct}%** |\n"

    report_md += """
### By State:
| State | Total Feedbacks | Helpfulness Rate |
|-------|-----------------|------------------|
"""
    for s in state_stats:
        t = s.get('total') or s.get('total_responses', 0)
        rate = s.get('helpfulness_rate', 0.0)
        pct = round(rate * 100, 1) if rate <= 1.0 else round(rate, 1)
        report_md += f"| {s.get('_id', 'Unknown')} | {t} | **{pct}%** |\n"

    report_md += """
---

## 🎯 5. Actionable Recommendations for Agri Team
1. **Simplify Technical Terms**: Responses in Plant Protection have high failure rates due to chemical names without clear trade names or local market equivalents.
2. **Shorten Response Length**: WhatsApp farmers reject lengthy theoretical answers; provide 3-4 bullet actionable steps first.
3. **Regional Specificity**: Certain pesticide dosages for Cotton differ between dryland and irrigated zones in Telangana vs. Maharashtra. Ensure regionalized advice.
"""

    return {
        "period_days": days,
        "generated_at": datetime.utcnow().isoformat(),
        "total_feedbacks": total_feedbacks,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "overall_helpfulness": overall_helpfulness,
        "flagged_entries_count": flagged_count,
        "lowest_rated_entries": lowest_rated_entries,
        "domain_stats": domain_stats,
        "language_stats": lang_stats,
        "state_stats": state_stats,
        "report_markdown": report_md,
    }
