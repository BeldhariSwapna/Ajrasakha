"""Seed realistic Week 1 Farmer Feedback Data for Testing & Demonstration.

Generates ~200 farmer feedback records across diverse states, crops, and domains,
including answers with high and low ratings, to demonstrate:
1. End-to-end feedback storage in MongoDB
2. Real-time Dashboard Analytics (per GDB, domain, language, state)
3. Automated Flagging Pipeline identifying <60% low-rated entries
4. Generation of the Agri Team's First Week Analysis Digest
"""

import random
from datetime import datetime, timedelta
from database import (
    get_collection,
    FEEDBACK_COLLECTION,
    FLAGGED_COLLECTION,
    SESSIONS_COLLECTION,
    save_feedback,
)
from pipeline import run_flagging_pipeline
from digest import generate_weekly_digest

SAMPLE_GDB_ENTRIES = [
    {
        "gdb_id": "gdb_entry_101",
        "crop": "Cotton",
        "domain": "Plant Protection",
        "state": "Telangana",
        "language": "te",
        "query": "పత్తిలో గులాబీ రంగు పురుగు నివారణ ఏమిటి?",
        "answer": "గులాబీ రంగు పురుగు నివారణకు ప్రొఫెనోఫాస్ 50% EC 2 మి.లీ లేదా ఇమామెక్టిన్ బెంజోయేట్ 5% SG 0.4 గ్రాములు ఒక లీటరు నీటికి కలిపి పిచికారీ చేయాలి. లింగాకర్షక బుట్టలు ఎకరాకు 8 అమర్చాలి.",
        "target_helpful_rate": 0.40,  # LOW -> Should be flagged!
        "num_feedbacks": 15,
    },
    {
        "gdb_id": "gdb_entry_102",
        "crop": "Paddy",
        "domain": "Plant Protection",
        "state": "Telangana",
        "language": "te",
        "query": "వరిలో కాండం తొలుచు పురుగు లక్షణాలు మరియు నివారణ?",
        "answer": "వరిలో కాండం తొలుచు పురుగు ఆశించినప్పుడు మొవ్వు ఎండిపోయి తెల్లకంకులు వస్తాయి. కార్టాప్ హైడ్రోక్లోరైడ్ 50% SP 2 గ్రాములు లీటరు నీటికి కలిపి పిచికారీ చేయాలి.",
        "target_helpful_rate": 0.90,  # HIGH
        "num_feedbacks": 20,
    },
    {
        "gdb_id": "gdb_entry_103",
        "crop": "Chilli",
        "domain": "Plant Protection",
        "state": "Andhra Pradesh",
        "language": "te",
        "query": "మిరపలో ఆకు ముడత నివారణ చర్యలు ఏమిటి?",
        "answer": "తామర పురుగుల వల్ల వచ్చే ఆకు ముడత నివారణకు స్పైనోసాడ్ 45% SC 0.3 మి.లీ లేదా ఫిప్రోనిల్ 5% SC 2 మి.లీ లీటరు నీటికి కలిపి పిచికారీ చేయాలి. నీలి రంగు జిగురు అట్టలు పెట్టాలి.",
        "target_helpful_rate": 0.35,  # LOW -> Should be flagged!
        "num_feedbacks": 14,
    },
    {
        "gdb_id": "gdb_entry_104",
        "crop": "Wheat",
        "domain": "Disease Management",
        "state": "Punjab",
        "language": "hi",
        "query": "गेहूं में पीला रतुआ (Yellow Rust) के लक्षण और उपचार क्या है?",
        "answer": "पीला रतुआ में पत्तियों पर पीले रंग की धारियाँ बनती हैं। प्रोपिकोनाजोल 25% EC का 1 मिली प्रति लीटर पानी में मिलाकर तुरंत छिड़काव करें।",
        "target_helpful_rate": 0.92,  # HIGH
        "num_feedbacks": 25,
    },
    {
        "gdb_id": "gdb_entry_105",
        "crop": "Sugarcane",
        "domain": "Cultural Practices",
        "state": "Maharashtra",
        "language": "mr",
        "query": "ऊस पिकात लाल कुजव्या (Red Rot) रोगाचा प्रादुर्भाव कसा रोखावा?",
        "answer": "लाल कुजव्या रोगासाठी निरोगी बेणे वापरावे, ट्रायकोडरमा विरिडी 2.5 किलो शेणखतात मिसळून एकरी द्यावे आणि पाण्याचा निचरा योग्य ठेवावा.",
        "target_helpful_rate": 0.45,  # LOW -> Should be flagged!
        "num_feedbacks": 11,
    },
    {
        "gdb_id": "gdb_entry_106",
        "crop": "Tomato",
        "domain": "Nutrient Management",
        "state": "Karnataka",
        "language": "kn",
        "query": "ಟೊಮೆಟೊ ಹಣ್ಣುಗಳಲ್ಲಿ ಕ್ಯಾಲ್ಸಿಯಂ ಕೊರತೆ ತಡೆಯುವುದು ಹೇಗೆ?",
        "answer": "ಕ್ಯಾಲ್ಸಿಯಂ ನೈಟ್ರೇಟ್ 5 ಗ್ರಾಂ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಹೂ ಬಿಡುವ ಮತ್ತು ಕಾಯಿ ಕಟ್ಟುವ ಹಂತದಲ್ಲಿ ಸಿಂಪಡಿಸಿ.",
        "target_helpful_rate": 0.85,  # HIGH
        "num_feedbacks": 18,
    },
    {
        "gdb_id": "gdb_entry_107",
        "crop": "Maize",
        "domain": "Fertilizer Management",
        "state": "Madhya Pradesh",
        "language": "hi",
        "query": "मक्के की फसल में यूरिया की सही मात्रा और देने का समय क्या है?",
        "answer": "मक्के में कुल यूरिया को तीन भागों में दें: एक तिहाई बुवाई के समय, एक तिहाई घुटने की ऊंचाई पर और शेष एक तिहाई नर मंजरी आने पर डालें।",
        "target_helpful_rate": 0.88,  # HIGH
        "num_feedbacks": 16,
    },
    {
        "gdb_id": "gdb_entry_108",
        "crop": "Soybean",
        "domain": "Weed Management",
        "state": "Maharashtra",
        "language": "mr",
        "query": "सोयाबीन पिकातील तण नियंत्रणासाठी कोणते तणनाशक वापरावे?",
        "answer": "सोयाबीनमध्ये पेरणीनंतर 15 ते 20 दिवसांनी इमेझाथापीर 10% SL 400 मिली प्रति एकर फवारावे.",
        "target_helpful_rate": 0.50,  # LOW -> Borderline / Should be flagged!
        "num_feedbacks": 12,
    },
    {
        "gdb_id": "gdb_entry_109",
        "crop": "Groundnut",
        "domain": "Plant Protection",
        "state": "Andhra Pradesh",
        "language": "te",
        "query": "వేరుశనగలో తిక్క తెగులు నివారణ మందులు?",
        "answer": "తిక్క తెగులు నివారణకు కార్బెండజిమ్ 12% + మాంకోజెబ్ 63% WP 2 గ్రాములు లీటరు నీటికి కలిపి 15 రోజుల వ్యవధిలో రెండు సార్లు పిచికారీ చేయాలి.",
        "target_helpful_rate": 0.95,  # HIGH
        "num_feedbacks": 20,
    },
]


def seed_database():
    """Populate MongoDB with Week 1 data."""
    feedback_coll = get_collection(FEEDBACK_COLLECTION)
    flagged_coll = get_collection(FLAGGED_COLLECTION)
    sessions_coll = get_collection(SESSIONS_COLLECTION)

    print("[INFO] Clearing previous test feedback data...")
    feedback_coll.delete_many({})
    flagged_coll.delete_many({})
    sessions_coll.delete_many({})

    print("[INFO] Seeding Week 1 Farmer Feedback records...")
    total_created = 0

    now = datetime.utcnow()

    for item in SAMPLE_GDB_ENTRIES:
        count = item["num_feedbacks"]
        target_rate = item["target_helpful_rate"]

        for i in range(count):
            # Stagger timestamps across past 7 days
            days_ago = random.uniform(0.1, 6.8)
            created_at = now - timedelta(days=days_ago)

            # Determine helpful based on target rate
            is_helpful = (random.random() < target_rate)
            feedback_val = 1 if is_helpful else 2

            phone_number = f"+9198{random.randint(10000000, 99999999)}"

            feedback_doc = {
                "gdb_id": item["gdb_id"],
                "farmer_phone": phone_number,
                "query": item["query"],
                "answer": item["answer"],
                "is_helpful": is_helpful,
                "feedback_value": feedback_val,
                "domain": item["domain"],
                "crop": item["crop"],
                "language": item["language"],
                "state": item["state"],
                "created_at": created_at,
            }
            save_feedback(feedback_doc)
            total_created += 1

    print(f"[SUCCESS] Seeded {total_created} feedback records across {len(SAMPLE_GDB_ENTRIES)} GDB entries!")

    print("\n[PIPELINE] Running Automated Flagging Pipeline (Threshold: < 60% over 10+ responses)...")
    flag_result = run_flagging_pipeline(min_responses=10, min_positive_rate=0.60)
    print(f"[FLAGGED] Total entries flagged for re-review: {flag_result['total_flagged_in_system']}")
    for f in flag_result["flagged_entries"]:
        print(f"   * {f['gdb_id']} ({f['crop']} - {f['domain']}): {round(f['helpfulness_rate']*100, 1)}% helpful [{f['flag_reason']}]")

    print("\n[REPORT] Generating Weekly Digest for Agri Team...")
    digest = generate_weekly_digest(days=7)
    with open("WEEK_1_FEEDBACK_ANALYSIS_REPORT.md", "w", encoding="utf-8") as f:
        f.write(digest["report_markdown"])
    print("[OUTPUT] Written 'WEEK_1_FEEDBACK_ANALYSIS_REPORT.md' successfully!")

    return total_created


if __name__ == "__main__":
    seed_database()
