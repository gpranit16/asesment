from fastapi import APIRouter
from backend.app.tools.booking import booking_service

router = APIRouter(tags=["slots"])

@router.get("/slots")
async def get_slots():
    """Retrieve all available appointment booking slots."""
    available = booking_service.get_available_slots()
    all_slots = booking_service.slots
    return {
        "success": True,
        "available_slots": available,
        "total_slots": len(all_slots)
    }

@router.get("/bookings")
async def get_bookings():
    """Retrieve confirmed bookings list."""
    return {
        "success": True,
        "bookings": booking_service.bookings
    }
