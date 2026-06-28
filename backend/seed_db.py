"""
SmartCity AI — Database seeder.

Populates the database with realistic Alexandria data so the
DB-backed API has something to work with out of the box.

Usage:
    python seed_db.py                    # seeds SQLite (default)
    python seed_db.py "postgresql+psycopg2://..."   # custom URL
"""

import sys
import numpy as np
from db import DATABASE_URL, init_db, get_engine, Base
from sqlalchemy.orm import Session

# ── Alexandria districts ──
AREAS = [
    {"id": 1,  "name": "Smouha",       "latitude": 31.2100, "longitude": 29.9400, "population": 45000, "avg_rent": 320, "traffic": 8.0, "access": 7.5},
    {"id": 2,  "name": "Sidi Gaber",   "latitude": 31.2200, "longitude": 29.9500, "population": 38000, "avg_rent": 280, "traffic": 7.5, "access": 8.0},
    {"id": 3,  "name": "Stanley",      "latitude": 31.2300, "longitude": 29.9600, "population": 25000, "avg_rent": 450, "traffic": 6.5, "access": 6.0},
    {"id": 4,  "name": "Louran",       "latitude": 31.2150, "longitude": 29.9300, "population": 32000, "avg_rent": 350, "traffic": 7.0, "access": 7.0},
    {"id": 5,  "name": "Cleopatra",    "latitude": 31.2250, "longitude": 29.9450, "population": 35000, "avg_rent": 260, "traffic": 6.0, "access": 6.5},
    {"id": 6,  "name": "Sports City",  "latitude": 31.2050, "longitude": 29.9200, "population": 22000, "avg_rent": 190, "traffic": 9.0, "access": 8.5},
    {"id": 7,  "name": "Rushdy",       "latitude": 31.2350, "longitude": 29.9650, "population": 29000, "avg_rent": 300, "traffic": 7.0, "access": 7.5},
    {"id": 8,  "name": "Shatby",       "latitude": 31.2400, "longitude": 29.9700, "population": 18000, "avg_rent": 220, "traffic": 6.5, "access": 6.0},
    {"id": 9,  "name": "Ibrahimia",    "latitude": 31.2170, "longitude": 29.9350, "population": 26000, "avg_rent": 240, "traffic": 5.5, "access": 5.0},
    {"id": 10, "name": "Moharam Bek",  "latitude": 31.2070, "longitude": 29.9150, "population": 31000, "avg_rent": 210, "traffic": 5.0, "access": 4.5},
    {"id": 11, "name": "Kafr Abdu",    "latitude": 31.2120, "longitude": 29.9250, "population": 27000, "avg_rent": 250, "traffic": 6.0, "access": 6.5},
    {"id": 12, "name": "El-Attarin",   "latitude": 31.2000, "longitude": 29.9000, "population": 15000, "avg_rent": 180, "traffic": 4.5, "access": 4.0},
]

# ── Alexandria place names per category ──
PLACES_BY_CATEGORY = {
    "Food & Beverage": [
        "Cafe Naguib", "Brew House", "Costa Stanley", "Cilantro Smouha",
        "KFC Sidi Gaber", "Pizza Hut Louran", "McDonald's Cleopatra",
        "Buffalo Burger", "Elite Cafe", "Roastery Rushdy",
    ],
    "Retail": [
        "Mega Mart Smouha", "Carrefour Sidi Gaber", "Metro Market Stanley",
        "Kheir Zaman", "B.Tech Louran", "Ragab Sons", "Mobil 1 Shop",
        "Fathalla Store", "Electro Misr", "Alfa Market",
    ],
    "Healthcare": [
        "El-Salam Pharmacy", "El-Ezaby Pharmacy Smouha", "Cleopatra Pharmacy",
        "Dr. Magdy Clinic", "Al-Moalimin Pharmacy", "Seif Pharmacy",
        "Alex Medical Center", "Mobrad Pharmacy", "Al-Ahly Pharmacy",
        "Royal Clinic Louran",
    ],
    "Education": [
        "Oxford Center", "Apex Tutoring", "Smart Kids Academy",
        "Al-Lisan Institute", "Future Language School", "STEM Center Alex",
        "El-Madar Center", "Nahda Tutoring", "Eagle Academy",
        "Al-Hewar Center",
    ],
    "Fitness": [
        "Gold's Gym Smouha", "Fitness Time Sidi Gaber", "Body Masters",
        "FitZone Stanley", "Iron GYM Louran", "CrossFit Alex",
        "Power House Gym", "Yoga Oasis Cleopatra", "Pulse Fitness",
        "Shape Up Studio",
    ],
    "Entertainment": [
        "Game Over Arcade", "Sky Zone Alex", "San Stefano Cinema",
        "Cineplex Smouha", "Bowling Center", "Escape Room Alex",
        "Fun City Louran", "Green Plaza Games", "City Center Arcade",
        "Sun & Sand Sports",
    ],
}

np.random.seed(42)


def seed(engine=None):
    """Main seed function."""
    if engine is None:
        engine = get_engine()

    init_db()
    from db import Area as AreaModel, Place as PlaceModel, AreaMetric as MetricModel

    session = Session(engine)

    try:
        # ── Clear existing ──
        session.query(MetricModel).delete()
        session.query(PlaceModel).delete()
        session.query(AreaModel).delete()
        session.flush()

        # ── Insert areas ──
        area_map = {}
        for a in AREAS:
            area = AreaModel(id=a["id"], name=a["name"],
                             latitude=a["latitude"], longitude=a["longitude"])
            session.add(area)
            area_map[a["id"]] = a
        session.flush()

        # ── Insert metrics ──
        for a in AREAS:
            metric = MetricModel(
                area_id=a["id"],
                population=a["population"],
                avg_rent=a["avg_rent"],
                competitor_count=np.random.randint(3, 12),
                traffic_score=a["traffic"],
                accessibility_score=a["access"],
            )
            session.add(metric)
        session.flush()

        # ── Insert places ──
        place_id = 1
        for category, names in PLACES_BY_CATEGORY.items():
            for name in names:
                area_id = np.random.choice([a["id"] for a in AREAS])
                area_lat = area_map[area_id]["latitude"] + np.random.uniform(-0.005, 0.005)
                area_lng = area_map[area_id]["longitude"] + np.random.uniform(-0.005, 0.005)
                place = PlaceModel(
                    id=place_id,
                    name=name,
                    category=category,
                    latitude=round(area_lat, 4),
                    longitude=round(area_lng, 4),
                    area_id=area_id,
                )
                session.add(place)
                place_id += 1

        session.commit()
        print(f"[OK] Seeded {len(AREAS)} areas, {len(AREAS)} metrics, {place_id - 1} places.")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Seed failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        import os
        os.environ["DATABASE_URL"] = sys.argv[1]

    print(f"Seeding database: {DATABASE_URL}")
    seed()
    print("Done.")
