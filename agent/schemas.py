"""
Pydantic schemas for restaurant AI agent tool inputs and outputs.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Greet User
# ============================================================================


class GreetUserInput(BaseModel):
    """Input schema for greeting the user."""

    pass  # No input needed


class GreetUserOutput(BaseModel):
    """Output schema for greeting."""

    message: str = Field(..., description="Greeting message to show user")


# ============================================================================
# Ask For Details
# ============================================================================


class AskForDetailsInput(BaseModel):
    """Input schema for asking user for missing details."""

    tool_name: str = Field(..., description="The tool that needs more information")
    missing_fields: List[str] = Field(..., description="List of missing field names")


class AskForDetailsOutput(BaseModel):
    """Output schema for asking for details."""

    message: str = Field(..., description="Message asking user for missing information")


# ============================================================================
# Restaurant Model
# ============================================================================


class Restaurant(BaseModel):
    """Restaurant data model."""

    id: int
    name: str
    city: str
    area: str
    cuisine: List[str]
    capacity: int
    price_range: str
    price_per_person: int = Field(..., description="Average price per person in INR")
    rating: float
    features: List[str]
    opening_hours: str


# ============================================================================
# Search Restaurants
# ============================================================================


class SearchRestaurantsInput(BaseModel):
    """Input schema for searching restaurants."""

    city: Optional[str] = Field(None, description="City to search in")
    area: Optional[str] = Field(None, description="Area/locality within the city")
    cuisine: Optional[str] = Field(
        None, description="Cuisine type (e.g., South Indian, Continental)"
    )
    price_range: Optional[str] = Field(None, description="Price range: ₹, ₹₹, or ₹₹₹")
    min_rating: Optional[float] = Field(
        None, description="Minimum rating (e.g., 4.0, 4.5)"
    )
    features: Optional[List[str]] = Field(
        None, description="Desired features (e.g., Rooftop, Fine Dining)"
    )
    max_results: int = Field(10, description="Maximum number of results to return")


class SearchRestaurantsOutput(BaseModel):
    """Output schema for search restaurants."""

    restaurants: List[Restaurant]
    total_count: int
    message: str


# ============================================================================
# Recommend Restaurants
# ============================================================================


class RecommendRestaurantsInput(BaseModel):
    """Input schema for getting restaurant recommendations."""

    user_preferences: str = Field(
        ..., description="User's dining preferences in natural language"
    )
    city: str = Field(..., description="City to recommend restaurants in")
    occasion: Optional[str] = Field(
        None, description="Special occasion (e.g., birthday, anniversary)"
    )
    max_results: int = Field(5, description="Maximum number of recommendations")


class RecommendRestaurantsOutput(BaseModel):
    """Output schema for restaurant recommendations."""

    recommendations: List[Restaurant]
    reasoning: str
    message: str


# ============================================================================
# Check Availability
# ============================================================================


class CheckAvailabilityInput(BaseModel):
    """Input schema for checking restaurant availability."""

    restaurant_id: int = Field(
        ...,
        description="Restaurant ID NUMBER from search results (e.g., 1 for #1, 2 for #2). NEVER use restaurant name.",
    )
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: str = Field(..., description="Time in HH:MM format (24-hour)")
    party_size: int = Field(..., description="Number of people")


class CheckAvailabilityOutput(BaseModel):
    """Output schema for availability check."""

    available: bool
    restaurant_name: str
    date: str
    time: str
    party_size: int
    alternative_times: Optional[List[str]] = Field(
        None, description="Alternative time slots if not available"
    )
    message: str


# ============================================================================
# Create Reservation
# ============================================================================


class CreateReservationInput(BaseModel):
    """Input schema for creating a reservation."""

    restaurant_id: int = Field(
        ...,
        description="Restaurant ID NUMBER from search results (e.g., 1 for #1, 2 for #2). NEVER use restaurant name.",
    )
    customer_name: str = Field(..., description="Customer's full name")
    phone: str = Field(..., description="Customer's phone number")
    date: str = Field(..., description="Reservation date in YYYY-MM-DD format")
    time: str = Field(..., description="Reservation time in HH:MM format (24-hour)")
    party_size: int = Field(..., description="Number of people")
    special_requests: Optional[str] = Field(
        None, description="Any special requests or notes"
    )


class CreateReservationOutput(BaseModel):
    """Output schema for reservation creation."""

    success: bool
    reservation_id: Optional[str] = Field(
        None, description="Unique reservation ID if successful"
    )
    restaurant_name: str
    customer_name: str
    date: str
    time: str
    party_size: int
    special_requests: Optional[str]
    message: str
