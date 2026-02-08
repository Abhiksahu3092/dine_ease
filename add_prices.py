"""
Script to add price_per_person field to all restaurants in the JSON file.
"""

import json
import random

# Price ranges based on price_range symbol
PRICE_MAP = {"₹": (200, 400), "₹₹": (600, 1200), "₹₹₹": (1500, 3000)}

# Read existing data
with open("data/restaurants.json", "r", encoding="utf-8") as f:
    restaurants = json.load(f)

# Add price_per_person to each restaurant
for restaurant in restaurants:
    price_range = restaurant["price_range"]
    min_price, max_price = PRICE_MAP[price_range]

    # Generate a price within the range (rounded to nearest 50)
    random.seed(restaurant["id"])  # Consistent prices for same restaurant
    price = random.randint(min_price, max_price)
    price = round(price / 50) * 50  # Round to nearest 50

    restaurant["price_per_person"] = price

# Write back to file with proper formatting
with open("data/restaurants.json", "w", encoding="utf-8") as f:
    json.dump(restaurants, f, indent=2, ensure_ascii=False)

print("✅ Successfully added price_per_person to all 100 restaurants!")
