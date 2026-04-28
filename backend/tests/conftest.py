"""Shared fixtures for contract tests."""
import pytest
from app.store import Manual


PAGES = [
    # p.1
    "OWNER'S MANUAL — TEST BIKE 200\nThank you for choosing Test Bike. Read this manual carefully before riding.",
    # p.2
    "CUSTOMER SUPPORT\nTest Bike Customer Care: 1800-123-4567 (Toll Free, Mon–Sat 9am–6pm)\nWebsite: www.testbike.com",
    # p.3
    "ENGINE OIL\nChange engine oil and filter every 5,000 km or 6 months, whichever comes first.\nUse SAE 10W-40 API SL grade engine oil.\nOil capacity: 1.2 litres (with filter change).\nWARNING: Do not overfill. Check oil level on the centre stand on level ground.",
    # p.4
    "CHECKING ENGINE OIL LEVEL\n1. Place the motorcycle on its centre stand on level ground.\n2. Remove the oil filler cap/dipstick and wipe it clean.\n3. Reinsert the dipstick without screwing it in.\n4. Remove and check: the oil level should be between the upper and lower marks.\n5. Add oil if required. Do not overfill.",
    # p.5
    "TYRE PRESSURE\nFront tyre: 29 psi (2.0 bar) — rider only\nRear tyre: 33 psi (2.3 bar) — rider only; 36 psi (2.5 bar) — with pillion\nCheck tyre pressure when tyres are cold.\nIncorrect tyre pressure will affect handling and tyre life.",
    # p.6
    "BRAKE FLUID\nUse DOT 4 brake fluid only.\nReplace brake fluid every 2 years regardless of mileage.\nWARNING: Brake fluid is corrosive. Avoid contact with painted surfaces.\nCheck brake fluid level monthly. The level should be between MIN and MAX marks on the reservoir.",
    # p.7
    "CHAIN MAINTENANCE\nLubricate the drive chain every 500 km or after riding in rain.\nUse a dedicated chain lubricant spray.\nChain slack: 20–30 mm measured at the midpoint of the lower chain run.\nWARNING: A loose or dry chain can cause loss of control.",
    # p.8
    "CLUTCH ADJUSTMENT\nFree play at the clutch lever tip: 10–20 mm.\nAdjust using the adjuster at the lever end. If adjustment is insufficient, use the secondary adjuster at the engine end.",
    # p.9
    "EXHAUST SYSTEM\nWARNING: The exhaust system gets very hot when the engine is running and remains too hot to touch, even after the engine is turned OFF. Keep all flammable materials away from the exhaust system.",
    # p.10
    "EVAPORATIVE EMISSION CONTROL SYSTEM\nThis motorcycle is equipped with an evaporative emission control system that prevents fuel vapours from escaping into the atmosphere when the engine is off.",
    # p.11
    "SPARK PLUG\nInspect spark plug every 5,000 km. Replace every 10,000 km.\nSpecified spark plug: NGK CR8E or equivalent.\nGap: 0.8–0.9 mm.\nWARNING: Never run the engine with a fouled or damaged spark plug.",
    # p.12
    "FUEL SYSTEM\nUse unleaded petrol with minimum octane rating of 91 RON.\nFuel tank capacity: 13 litres (including 2 litre reserve).\nWARNING: Do not smoke or allow open flames near the fuel system.",
]


@pytest.fixture
def test_manual() -> Manual:
    return Manual(
        id="test-manual-001",
        filename="test_bike_manual.pdf",
        page_count=len(PAGES),
        pages=PAGES,
    )
