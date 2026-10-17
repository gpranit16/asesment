import json
import re
import random
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from backend.app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_SLOTS = [
    {"id": "slot_1", "display": "Tomorrow 11:00 AM", "time": "Tomorrow 11:00 AM IST", "available": True},
    {"id": "slot_2", "display": "Tomorrow 3:00 PM", "time": "Tomorrow 3:00 PM IST", "available": True},
    {"id": "slot_3", "display": "Friday 10:30 AM", "time": "Friday 10:30 AM IST", "available": True},
    {"id": "slot_4", "display": "Monday 2:00 PM", "time": "Monday 2:00 PM IST", "available": True},
    {"id": "slot_5", "display": "Next Tuesday 4:00 PM", "time": "Next Tuesday 4:00 PM IST", "available": True},
]

class BookingService:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or settings.BOOKINGS_PATH
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.slots = data.get("slots", DEFAULT_SLOTS)
                    self.bookings = data.get("bookings", [])
                    return
            except Exception as e:
                logger.error(f"Error reading bookings storage: {e}")
        
        self.slots = [dict(s) for s in DEFAULT_SLOTS]
        self.bookings = []
        self._save()

    def _save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"slots": self.slots, "bookings": self.bookings}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving bookings storage: {e}")

    def reset(self):
        """Resets slots to default available state for fresh sessions and testing."""
        self.slots = [dict(s) for s in DEFAULT_SLOTS]
        self.bookings = []
        self._save()

    def get_available_slots(self) -> List[Dict[str, Any]]:
        return [s for s in self.slots if s.get("available", True)]

    @staticmethod
    def validate_email(email: str) -> bool:
        if not email:
            return False
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email.strip()))

    @staticmethod
    def validate_name(name: str) -> bool:
        if not name:
            return False
        cleaned = name.strip()
        return len(cleaned) >= 2 and any(c.isalpha() for c in cleaned)

    def match_slot(self, user_slot_input: str) -> Optional[Dict[str, Any]]:
        """
        Intelligently matches user slot text (e.g. '1', 'Tomorrow 11', 'Friday at 10:30 AM')
        to an available slot.
        """
        text = user_slot_input.strip().lower()
        available = self.get_available_slots()

        # If all slots were booked in previous runs, use all slots
        candidates = available if available else self.slots

        # Check by numbered option: "1", "slot 1", "first slot"
        num_match = re.search(r"\b([1-5])\b", text)
        if num_match:
            idx = int(num_match.group(1)) - 1
            if 0 <= idx < len(candidates):
                return candidates[idx]

        # Keyword matching
        for slot in candidates:
            disp = slot["display"].lower()
            if disp in text or text in disp:
                return slot
            # Day + time check (e.g. 'friday' and '10:30')
            parts = [p.strip().lower() for p in disp.split()]
            if any(day in text for day in ("friday", "tomorrow", "monday", "tuesday")) and any(tm in text for tm in ("11:00", "3:00", "10:30", "2:00", "4:00", "11", "3", "10", "2", "4")):
                if parts[0] in text and (parts[1] in text or parts[1].replace(":00", "") in text):
                    return slot

        return None

    def create_booking(self, name: str, email: str, slot_text: str, service_type: str = "Performance Review") -> Dict[str, Any]:
        """
        Validates details, locks the slot, and generates an official Reference ID.
        """
        if not self.validate_name(name):
            return {"success": False, "error": "Invalid name provided. Please provide your full name."}

        if not self.validate_email(email):
            return {"success": False, "error": "Invalid email address format."}

        matched_slot = self.match_slot(slot_text)
        if not matched_slot:
            # If slot_text was already confirmed or contains a time string
            slot_display = slot_text.strip()
        else:
            slot_display = matched_slot["display"]
            # Mark slot as booked
            for s in self.slots:
                if s["id"] == matched_slot["id"]:
                    s["available"] = False

        ref_id = f"#REV-{random.randint(4000, 4999)}"
        booking_record = {
            "ref_id": ref_id,
            "name": name.strip(),
            "email": email.strip(),
            "slot": slot_display,
            "service_type": service_type,
            "status": "confirmed"
        }

        self.bookings.append(booking_record)
        self._save()

        return {
            "success": True,
            "booking": booking_record,
            "ref_id": ref_id,
            "slot": slot_display,
            "message": f"Confirmed! Your {service_type} is scheduled for {slot_display} for {name.strip()}. Reference ID: {ref_id}."
        }

booking_service = BookingService()
