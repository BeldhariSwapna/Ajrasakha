"""WhatsApp Bot Feedback Handler for AjraSakha.

Handles:
1. Delivering follow-up prompt ("Was this helpful? Reply 1 for Yes, 2 for No")
2. Capturing farmer's reply ('1' or '2')
3. Linking feedback to specific GDB entry
4. Sending multilingual acknowledgment
"""

import os
import re
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
import httpx

from database import (
    create_or_update_session,
    get_pending_session,
    close_session,
    save_feedback,
)

logger = logging.getLogger(__name__)

# Multilingual Feedback Prompts
PROMPT_TEMPLATES = {
    "en": "Was this helpful? Reply 1 for Yes, 2 for No",
    "te": "ఈ సమాధానం మీకు ఉపయోగపడిందా?\nఅవును అయితే 1, కాదు అయితే 2 అని రిప్లై ఇవ్వండి.",
    "hi": "क्या यह उत्तर आपके लिए मददगार था?\nहाँ के लिए 1, नहीं के लिए 2 लिखकर भेजें।",
    "kn": "ಈ ಉತ್ತರವು ನಿಮಗೆ ಉಪಯುಕ್ತವಾಗಿದೆಯೇ?\nಹೌದು ಎಂದರೆ 1, ಇಲ್ಲ ಎಂದರೆ 2 ಎಂದು ಉತ್ತರಿಸಿ.",
    "ta": "இந்த பதில் உங்களுக்கு பயனுள்ளதாக இருந்ததா?\nஆம் எனில் 1, இல்லை எனில் 2 என பதிலளிக்கவும்.",
    "mr": "हे उत्तर आपल्यासाठी उपयुक्त होते का?\nहोय असल्यास 1, नाही असल्यास 2 पाठवा.",
}

# Multilingual Thank You Acknowledgments
ACK_TEMPLATES = {
    "en": "Thank you for your feedback! It helps AjraSakha give better answers to all farmers.",
    "te": "మీ ఫీడ్‌బ్యాక్‌కు ధన్యవాదాలు! ఇది అజ్రసఖను రైతులకు మరింత మెరుగ్గా తీర్చిదిద్దడానికి సహాయపడుతుంది.",
    "hi": "आपकी प्रतिक्रिया के लिए धन्यवाद! इससे अजरसखा को और बेहतर बनाने में मदद मिलती है।",
    "kn": "ನಿಮ್ಮ ಪ್ರತಿಕ್ರಿಯೆಗೆ ಧನ್ಯವಾದಗಳು!",
    "ta": "உங்கள் கருத்துக்கு நன்றி!",
    "mr": "आपल्या अभिप्रायाबद्दल धन्यवाद!",
}

WHATSAPP_SEND_URL = os.getenv("WA_SEND_MESSAGE_WEBHOOK_API_URL") or os.getenv("WHATSAPP_SERVER_URL")
WHATSAPP_API_KEY = os.getenv("WA_WEBHOOK_API_KEY", "")


def get_prompt_text(language: str = "te") -> str:
    """Return localized feedback prompt."""
    lang_key = (language or "en").lower()[:2]
    return PROMPT_TEMPLATES.get(lang_key, PROMPT_TEMPLATES["en"])


def get_ack_text(language: str = "te") -> str:
    """Return localized thank you acknowledgment."""
    lang_key = (language or "en").lower()[:2]
    return ACK_TEMPLATES.get(lang_key, ACK_TEMPLATES["en"])


async def send_whatsapp_message(phone_number: str, text: str) -> bool:
    """Send message via WhatsApp webhook or service."""
    if not WHATSAPP_SEND_URL:
        logger.info(f"[Mock WhatsApp] To: {phone_number} | Message: {text}")
        return True

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "Content-Type": "application/json",
                "x-internal-api-key": WHATSAPP_API_KEY,
            }
            payload = {
                "phoneNumber": phone_number,
                "messageText": text,
                "sendBy": "AjraSakha Bot",
            }
            response = await client.post(WHATSAPP_SEND_URL, json=payload, headers=headers)
            return response.is_success
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {phone_number}: {e}")
        return False


async def initiate_feedback_prompt(
    farmer_phone: str,
    gdb_id: str,
    query: str,
    answer: str,
    domain: str = "General Agriculture",
    crop: str = "General",
    language: str = "te",
    state: str = "Telangana",
    district: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Called after AjraSakha delivers an answer to the farmer.
    Registers a pending session and delivers the follow-up prompt.
    """
    session_data = {
        "farmer_phone": farmer_phone,
        "gdb_id": gdb_id,
        "query": query,
        "answer": answer,
        "domain": domain,
        "crop": crop,
        "language": language,
        "state": state,
        "district": district,
        "status": "pending",
        "created_at": datetime.utcnow(),
    }
    create_or_update_session(farmer_phone, session_data)

    prompt_message = get_prompt_text(language)
    sent_successfully = await send_whatsapp_message(farmer_phone, prompt_message)

    return {
        "status": "prompt_sent",
        "farmer_phone": farmer_phone,
        "gdb_id": gdb_id,
        "prompt": prompt_message,
        "delivered": sent_successfully,
    }


def parse_feedback_input(text: str) -> Tuple[bool, Optional[bool], Optional[int]]:
    """
    Parse farmer's input to determine if it is a feedback reply.
    Handles '1', '1. Yes', 'yes', 'అవును', '2', '2. No', 'no', 'కాదు', etc.
    Returns: (is_feedback, is_helpful, feedback_value)
    """
    clean_text = text.strip().lower()

    # Reply 1: Yes / Helpful
    if (
        clean_text in ["1", "y", "yes", "helpful", "అవును", "हाँ", "ho"]
        or clean_text.startswith("1")
        or "yes" in clean_text
        or "అవును" in clean_text
        or "हाँ" in clean_text
    ):
        return True, True, 1

    # Reply 2: No / Not Helpful
    if (
        clean_text in ["2", "n", "no", "not helpful", "కాదు", "नहीं", "nahi"]
        or clean_text.startswith("2")
        or "not helpful" in clean_text
        or "కాదు" in clean_text
        or "नहीं" in clean_text
    ):
        return True, False, 2

    return False, None, None


async def handle_incoming_message(from_phone: str, message_text: str) -> Dict[str, Any]:
    """
    Evaluates incoming WhatsApp message.
    If farmer has a pending feedback prompt and replies with 1 or 2,
    captures feedback and closes the session.
    """
    session = get_pending_session(from_phone)

    if not session:
        return {
            "is_feedback": False,
            "message": "No pending feedback session found. Normal query flow.",
        }

    is_feedback, is_helpful, feedback_value = parse_feedback_input(message_text)

    if not is_feedback:
        # Not a 1/2 response. Farmer might be asking a new question.
        return {
            "is_feedback": False,
            "message": "Incoming message is not a feedback answer. Proceed with normal NLP processing.",
        }

    # Record feedback in MongoDB
    feedback_doc = {
        "gdb_id": session.get("gdb_id"),
        "farmer_phone": from_phone,
        "query": session.get("query"),
        "answer": session.get("answer"),
        "is_helpful": is_helpful,
        "feedback_value": feedback_value,
        "domain": session.get("domain", "General Agriculture"),
        "crop": session.get("crop", "General"),
        "language": session.get("language", "te"),
        "state": session.get("state", "Telangana"),
        "district": session.get("district"),
        "created_at": datetime.utcnow(),
    }

    inserted_id = save_feedback(feedback_doc)
    close_session(from_phone)

    # Send thank you acknowledgment
    ack_message = get_ack_text(session.get("language", "te"))
    await send_whatsapp_message(from_phone, ack_message)

    return {
        "is_feedback": True,
        "feedback_id": inserted_id,
        "gdb_id": session.get("gdb_id"),
        "is_helpful": is_helpful,
        "feedback_value": feedback_value,
        "ack_sent": ack_message,
    }
