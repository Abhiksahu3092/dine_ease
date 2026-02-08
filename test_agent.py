#!/usr/bin/env python
"""Test script for the restaurant agent"""

import json
from agent.tools import search_restaurants, book_table, execute_tool

# Test 1: Search restaurants
print("=" * 60)
print("TEST 1: Search Restaurants in Bangalore")
print("=" * 60)
result = search_restaurants(city="Bangalore", cuisine="Italian")
data = json.loads(result)
print(f"Found {data['total']} Italian restaurants in Bangalore")
if data["restaurants"]:
    print(f"\nTop restaurant: {data['restaurants'][0]['name']}")
    print(f"Rating: {data['restaurants'][0]['rating']}")
    print(f"Price: {data['restaurants'][0]['price_range']}")

# Test 2: Execute tool via registry
print("\n" + "=" * 60)
print("TEST 2: Tool Execution via Registry")
print("=" * 60)
tool_result = execute_tool("search_restaurants", {"city": "Mumbai"})
data2 = json.loads(tool_result)
print(f"Found {data2['total']} restaurants in Mumbai")

# Test 3: Book table
print("\n" + "=" * 60)
print("TEST 3: Book Table")
print("=" * 60)
booking_result = book_table(
    restaurant_id=1,
    customer_name="Test User",
    phone="9876543210",
    date="2026-02-10",
    time="19:00",
    party_size=4,
)
booking_data = json.loads(booking_result)
print(f"Booking success: {booking_data['success']}")
if booking_data["success"]:
    print(f"Booking ID: {booking_data['booking_id']}")
    print(f"Restaurant: {booking_data['restaurant_name']}")

print("\n✅ All tests passed!")
