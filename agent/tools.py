"""
Tool functions for Restaurant Reservation Agent.
"""

import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


# ============================================================================
# Data & Paths
# ============================================================================
DATA_PATH = Path(__file__).parent.parent / "data" / "restaurants.json"
BOOKINGS_PATH = Path(__file__).parent.parent / "data" / "bookings.json"

# Initialize bookings file
if not BOOKINGS_PATH.exists():
    BOOKINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BOOKINGS_PATH, "w") as f:
        json.dump([], f)


# ============================================================================
# Internal Helpers
# ============================================================================
def _load_restaurants() -> List[Dict[str, Any]]:
    """Load restaurants from JSON."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_bookings() -> List[Dict]:
    """Load existing bookings"""
    try:
        with open(BOOKINGS_PATH, "r") as f:
            return json.load(f)
    except:
        return []


def _save_booking(booking: Dict):
    """Save a new booking"""
    bookings = _load_bookings()
    bookings.append(booking)
    with open(BOOKINGS_PATH, "w") as f:
        json.dump(bookings, f, indent=2)


def _json(data: Any) -> str:
    """Convert to JSON string"""
    return json.dumps(data, ensure_ascii=False)


def _check_capacity(
    restaurant_id: int, date: str, time: str, party_size: int
) -> Dict[str, Any]:
    """Check available seats considering existing bookings"""
    restaurants = _load_restaurants()
    restaurant = next((r for r in restaurants if r["id"] == restaurant_id), None)

    if not restaurant:
        return {"available_seats": 0, "capacity": 0, "can_accommodate": False}

    capacity = restaurant.get("capacity", 50)

    # Count existing bookings for this time slot
    bookings = _load_bookings()
    booked_seats = sum(
        b["party_size"]
        for b in bookings
        if b["restaurant_id"] == restaurant_id
        and b["date"] == date
        and b["time"] == time
    )

    available = max(capacity - booked_seats, 0)

    return {
        "available_seats": available,
        "capacity": capacity,
        "booked_seats": booked_seats,
        "can_accommodate": available >= party_size,
    }


# ============================================================================
# TOOL FUNCTIONS
# ============================================================================
def search_restaurants(
    city: str = None,
    cuisine: str = None,
    price_range: str = None,
    min_rating: float = None,
    party_size: int = None,
) -> str:
    """Search for restaurants based on criteria"""
    restaurants = _load_restaurants()

    results = []
    for r in restaurants:
        # Filter by city (required)
        if city and r["city"].lower() != city.lower():
            continue

        # Filter by cuisine
        if cuisine:
            cuisines_lower = [c.lower() for c in r.get("cuisine", [])]
            if cuisine.lower() not in cuisines_lower:
                continue

        # Filter by price range
        if price_range and r.get("price_range") != price_range:
            continue

        # Filter by rating
        if min_rating and r.get("rating", 0) < min_rating:
            continue

        # Check capacity if party size provided
        if party_size and r.get("capacity", 0) < party_size:
            continue

        results.append(
            {
                "id": r["id"],
                "name": r["name"],
                "city": r["city"],
                "area": r.get("area", ""),
                "cuisine": r.get("cuisine", []),
                "rating": r.get("rating", 0),
                "price_range": r.get("price_range", "₹₹"),
                "price_per_person": r.get("price_per_person", 0),
                "capacity": r.get("capacity", 50),
                "features": r.get("features", []),
            }
        )

    # Sort by rating descending
    results.sort(key=lambda x: x["rating"], reverse=True)

    return _json({"total": len(results), "restaurants": results[:6]})  # Return top 6


def book_table(
    restaurant_id: int,
    customer_name: str,
    phone: str,
    date: str,
    time: str,
    party_size: int,
) -> str:
    """Book a table at a restaurant"""
    restaurants = _load_restaurants()

    # Find restaurant
    restaurant = next((r for r in restaurants if r["id"] == restaurant_id), None)
    if not restaurant:
        return _json({"success": False, "message": "Restaurant not found"})

    # Check availability
    availability = _check_capacity(restaurant_id, date, time, party_size)

    if not availability["can_accommodate"]:
        return _json(
            {
                "success": False,
                "message": f"Not enough seats available. Only {availability['available_seats']} seats left.",
                "available_seats": availability["available_seats"],
            }
        )

    # Create booking
    booking_id = (
        f"RES-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
    )

    booking = {
        "booking_id": booking_id,
        "restaurant_id": restaurant_id,
        "restaurant_name": restaurant["name"],
        "customer_name": customer_name,
        "phone": phone,
        "date": date,
        "time": time,
        "party_size": party_size,
        "created_at": datetime.now().isoformat(),
    }

    _save_booking(booking)

    # Format detailed confirmation message
    confirmation_msg = f"""✅ **BOOKING CONFIRMED!**

📋 **Booking Details:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎫 **Booking ID:** `{booking_id}`
🏪 **Restaurant:** {restaurant['name']}
📍 **Location:** {restaurant.get('area', '')}, {restaurant['city']}
👤 **Name:** {customer_name}
📞 **Phone:** {phone}
📅 **Date:** {date}
🕐 **Time:** {time}
👥 **Party Size:** {party_size} {"person" if party_size == 1 else "people"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **Please save your Booking ID for reference.**
📞 Restaurant Contact: {restaurant.get('opening_hours', 'N/A')}
"""

    return _json(
        {
            "success": True,
            "booking_id": booking_id,
            "restaurant_name": restaurant["name"],
            "restaurant_location": f"{restaurant.get('area', '')}, {restaurant['city']}",
            "customer_name": customer_name,
            "phone": phone,
            "date": date,
            "time": time,
            "party_size": party_size,
            "restaurant_address": restaurant.get("area", ""),
            "restaurant_hours": restaurant.get("opening_hours", "N/A"),
            "message": confirmation_msg,
        }
    )


# ============================================================================
# TOOL REGISTRY & SCHEMAS
# ============================================================================
TOOL_REGISTRY = {"search_restaurants": search_restaurants, "book_table": book_table}


def execute_tool(name: str, args: Dict[str, Any]) -> str:
    """Execute a tool by name with given arguments"""
    func = TOOL_REGISTRY.get(name)
    if not func:
        return _json({"error": f"Unknown tool: {name}"})
    try:
        return func(**args)
    except Exception as e:
        return _json({"error": str(e)})


tools_schema = {
    "search_restaurants": {
        "city": "string (required)",
        "cuisine": "string (optional)",
        "price_range": "string (optional)",
        "min_rating": "number (optional)",
        "party_size": "number (optional)",
    },
    "book_table": {
        "restaurant_id": "number (required)",
        "customer_name": "string (required)",
        "phone": "string (required)",
        "date": "string YYYY-MM-DD (required)",
        "time": "string HH:MM (required)",
        "party_size": "number (required)",
    },
}
