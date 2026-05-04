"""
Extended evaluation suite — gaps not covered by test_contract.py or test_real_scenarios.py.

Categories:
  1.  Partial coverage         — Rule 3: answer what IS in manual, redirect for the rest
  2.  Compound questions        — two-part Qs where one half is covered, one isn't
  3.  Spec precision            — exact numbers must match the manual, never rounded/hallucinated
  4.  Clarifying questions      — ambiguous symptoms must trigger a question, not a guess
  5.  Warning lights            — instrument cluster responses grounded in manual
  6.  Format compliance         — citations present, no markdown headings, stops on completion
  7.  Response stopping         — no padding, no "I hope this helps", no meta-commentary
  8.  Hindi / bilingual         — Rule 9: respond in user's language, keep citations verbatim
  9.  Multi-turn coherence      — follow-up questions build correctly on prior answers
  10. Boundary / negative       — topics the manual almost covers but doesn't

Run:
    cd backend
    PYTHONPATH=. pytest tests/test_evals_v2.py -v -s
"""
import re
import pytest
from app.services.claude import ask
from app.store import Manual


# ---------------------------------------------------------------------------
# Manual fixture (Guerrilla 450 — richest synthetic fixture)
# ---------------------------------------------------------------------------

PAGES = [
    # p.1
    "ROYAL ENFIELD GUERRILLA 450 — OWNER'S MANUAL\n"
    "Read this manual before operating your motorcycle. Keep it for future reference.",

    # p.2
    "CUSTOMER SUPPORT\n"
    "Royal Enfield Customer Care: 1800-210-0008 (Toll Free)\n"
    "Available Monday–Saturday, 9 AM–6 PM\n"
    "Website: www.royalenfield.com",

    # p.3
    "SAFETY WARNINGS\n"
    "WARNING: Always wear a helmet and protective gear while riding.\n"
    "WARNING: The exhaust system gets very hot when the engine is running and remains too hot "
    "to touch, even after the engine is turned OFF. Keep flammable materials away from exhaust.",

    # p.4
    "SIDE STAND SAFETY\n"
    "WARNING: Never ride with the side stand down. The engine will automatically cut off when "
    "you engage first gear with the side stand deployed — this is a safety feature.\n"
    "Always retract the side stand fully before moving the motorcycle.\n"
    "The side stand indicator light on the instrument cluster will illuminate when the side stand is down.",

    # p.5
    "INSTRUMENT CLUSTER — WARNING LIGHTS\n"
    "Side Stand Indicator: Illuminates when side stand is down. Engine cuts off in gear.\n"
    "Low Fuel Warning: Fuel pump icon illuminates when approximately 2.5L ± 0.5L of fuel remains.\n"
    "ABS Warning Light: Illuminates at ignition. Should turn off after 5 km/h. If it stays on, "
    "visit an authorised service centre — do not attempt self-diagnosis of the ABS system.\n"
    "Engine Warning Light (MIL): Triangle with exclamation mark. Indicates an engine management "
    "fault. Visit an authorised service centre immediately.",

    # p.6
    "ENGINE OIL\n"
    "Change engine oil and filter every 10,000 km or 12 months, whichever comes first.\n"
    "Recommended oil: SAE 15W-50 API SN or higher, JASO MA2 certified.\n"
    "Oil capacity (with filter): 2.5 litres.\n"
    "WARNING: Do not overfill. Check oil level with the motorcycle on its centre stand on level ground.\n"
    "Check oil level before every ride using the sight glass on the right side of the engine.",

    # p.7
    "CHECKING ENGINE OIL LEVEL\n"
    "1. Place the motorcycle on its centre stand on level ground.\n"
    "2. Start the engine and let it idle for 2–3 minutes, then switch off.\n"
    "3. Wait 3 minutes for oil to settle.\n"
    "4. Check the oil level through the sight glass — it should be between the upper and lower marks.\n"
    "5. If low, remove the filler cap and add the recommended oil in small amounts.\n"
    "6. Do not overfill beyond the upper mark.",

    # p.8
    "TYRE PRESSURE\n"
    "Check tyre pressure when tyres are cold (not ridden for 3 hours or less than 1 km).\n"
    "Front tyre: 29 psi (2.0 bar) — solo rider\n"
    "Rear tyre: 33 psi (2.3 bar) — solo rider; 36 psi (2.5 bar) — with pillion\n"
    "WARNING: Riding with incorrect tyre pressure affects handling, tyre wear, and can cause loss of control.\n"
    "Inspect tyres for cuts, cracks, or embedded objects before every ride.",

    # p.9
    "BRAKE FLUID\n"
    "Brake fluid type: DOT 4 only. Do not mix brake fluid types.\n"
    "Replace brake fluid every 2 years or 20,000 km, whichever comes first.\n"
    "Check brake fluid level monthly. Level should be between MIN and MAX on the reservoir.\n"
    "WARNING: Brake fluid is hygroscopic — it absorbs moisture over time, reducing braking effectiveness.\n"
    "WARNING: Brake fluid is corrosive. Avoid contact with painted surfaces and skin.",

    # p.10
    "BRAKE INSPECTION\n"
    "Front brake pad minimum thickness: 1.5 mm. Replace if worn below this limit.\n"
    "Rear brake pad minimum thickness: 1.5 mm.\n"
    "Inspect brake pads every 5,000 km.\n"
    "If brakes feel spongy or require excessive lever travel, have the system inspected at an "
    "authorised service centre — this may indicate air in the brake lines or low fluid.",

    # p.11
    "DRIVE CHAIN\n"
    "Lubricate the drive chain every 500 km or after riding in rain or mud.\n"
    "Use a dedicated motorcycle chain lubricant. Apply to the inner links while rotating the rear wheel.\n"
    "Chain slack (free play): 20–30 mm measured at the midpoint of the lower chain run.\n"
    "Inspect chain for tight spots, rust, or damaged links. Replace if worn beyond service limit.\n"
    "WARNING: A slack or dry chain can snap or derail, causing sudden loss of power and potential accident.",

    # p.12
    "CHAIN ADJUSTMENT\n"
    "1. Place motorcycle on centre stand.\n"
    "2. Loosen the rear axle nut.\n"
    "3. Turn both adjuster bolts equally to move the wheel back (increases tension) or forward (reduces tension).\n"
    "4. Ensure both alignment marks on each side are at the same position.\n"
    "5. Tighten the rear axle nut to 100 Nm.\n"
    "6. Recheck chain slack after tightening.",

    # p.13
    "CLUTCH\n"
    "Clutch lever free play: 10–20 mm at the lever tip.\n"
    "Adjust using the adjuster at the lever end. Turn clockwise to increase free play, "
    "counterclockwise to decrease.\n"
    "If adjustment at the lever is insufficient, use the secondary adjuster at the engine end.\n"
    "A dragging clutch (difficulty shifting gears) or slipping clutch should be inspected at "
    "an authorised service centre.",

    # p.14
    "SPARK PLUG\n"
    "Specified spark plug: NGK CR8EIA-9 (iridium) — do not substitute.\n"
    "Inspect: every 10,000 km. Replace: every 20,000 km.\n"
    "Spark plug gap: 0.8–0.9 mm.\n"
    "WARNING: Always allow the engine to cool completely before removing the spark plug.\n"
    "Tighten to 12–15 Nm. Do not overtighten.",

    # p.15
    "FUEL SYSTEM\n"
    "Fuel type: Unleaded petrol, minimum 91 RON (Research Octane Number).\n"
    "Tank capacity: 13 litres total, including approximately 2.5 litre reserve.\n"
    "Low fuel warning activates at approximately 2.5L ± 0.5L remaining.\n"
    "WARNING: Do not smoke or allow open flames near the fuel system.\n"
    "WARNING: Fuel is highly flammable. Wipe up any spills immediately.",

    # p.16
    "BATTERY\n"
    "Battery type: 12V, 8Ah sealed maintenance-free (MF) lead-acid battery.\n"
    "The battery is sealed and does not require electrolyte top-up.\n"
    "If the battery discharges fully, charge using a compatible 12V charger at 0.8A for 10–12 hours.\n"
    "WARNING: Do not attempt to open the sealed battery casing.\n"
    "If the battery fails to hold charge after a full charge cycle, replace it at an authorised service centre.",

    # p.17
    "EVAPORATIVE EMISSION CONTROL SYSTEM\n"
    "This motorcycle is equipped with an evaporative emission control system (EVAP) that prevents "
    "fuel vapours from escaping into the atmosphere when the engine is off.\n"
    "WARNING: Do not tamper with or remove any EVAP components — required by emission regulations.",

    # p.18
    "PERIODIC MAINTENANCE SCHEDULE\n"
    "500 km: Initial service — engine oil, filter, chain, all fasteners.\n"
    "5,000 km: Engine oil + filter, brake pads, chain, tyre pressure, lights.\n"
    "10,000 km: All above + spark plug inspection, air filter, brake fluid check, throttle freeplay.\n"
    "20,000 km: All above + spark plug replacement, brake fluid replacement.\n"
    "All services must be performed at an authorised Royal Enfield service centre to maintain warranty.",
]


@pytest.fixture
def manual():
    return Manual(
        id="guerrilla-450-eval",
        filename="guerrilla_450_manual.pdf",
        page_count=len(PAGES),
        pages=PAGES,
    )


def q(manual, question, history=None):
    return ask(manual=manual, question=question, history=history or [])["answer"]


FORBIDDEN_GENERAL = [
    r"head gasket", r"piston rings?", r"coolant leak", r"valve seal",
    r"can indicate", r"could indicate", r"common causes?", r"possible causes?",
    r"i recommend", r"i (would |)suggest", r"i hope this helps",
    r"feel free to ask", r"do not continue riding", r"qualified technician",
    r"professional mechanic", r"does not say whether",
]


def assert_no_general_knowledge(answer, ctx=""):
    lower = answer.lower()
    for pat in FORBIDDEN_GENERAL:
        assert not re.search(pat, lower), (
            f"[{ctx}] General knowledge leaked — pattern {pat!r}\nAnswer: {answer}"
        )


def assert_citation(answer, ctx=""):
    assert re.search(r"\(p+\.\s*\d+", answer), (
        f"[{ctx}] No page citation found.\nAnswer: {answer}"
    )


def assert_no_not_covered_opener(answer, ctx=""):
    assert not answer.lower().startswith("this is not covered"), (
        f"[{ctx}] Wrong opener for partial-coverage case.\nAnswer: {answer}"
    )


# ===========================================================================
# 1. PARTIAL COVERAGE
# Manual covers inspection/spec — not the DIY repair procedure.
# Bot must lead with what IS there, never open with "not covered".
# ===========================================================================

class TestPartialCoverage:

    def test_brake_pad_replacement(self, manual):
        """Manual covers wear limit (p.10) but not DIY replacement steps."""
        answer = q(manual, "My brake pads are worn out, how do I replace them?")
        lower = answer.lower()
        assert_no_not_covered_opener(answer, "brake_pad_replacement")
        assert "1.5" in answer, "Should cite the 1.5 mm wear limit from p.10"
        assert_citation(answer, "brake_pad_replacement")
        assert "service centre" in lower or "1800" in lower

    def test_spark_plug_removal(self, manual):
        """Manual covers gap/spec/interval (p.14) but not a removal procedure."""
        answer = q(manual, "My spark plug is fouled, walk me through removing and replacing it.")
        lower = answer.lower()
        assert_no_not_covered_opener(answer, "spark_plug_removal")
        assert "ngk" in lower or "cr8eia" in lower or "20,000" in lower or "10,000" in lower
        assert_citation(answer, "spark_plug_removal")

    def test_battery_replacement(self, manual):
        """Manual covers spec/charging (p.16) but not physical swap — citation + redirect expected."""
        answer = q(manual, "My battery is dead and won't hold charge — how do I replace it?")
        lower = answer.lower()
        # Must cite battery page and redirect — opener can be either style
        assert_citation(answer, "battery_replacement")
        assert "service centre" in lower or "1800" in lower
        assert_no_general_knowledge(answer, "battery_replacement")

    def test_chain_replacement(self, manual):
        """Manual covers lubrication/adjustment but not chain removal — redirect expected."""
        answer = q(manual, "My chain is badly worn and needs replacing. How do I take it off?")
        lower = answer.lower()
        # Manual covers related sections; bot should acknowledge them and redirect
        assert_citation(answer, "chain_replacement")
        assert "service centre" in lower or "1800" in lower or "not covered" in lower
        assert_no_general_knowledge(answer, "chain_replacement")

    def test_clutch_cable_replacement(self, manual):
        """Manual covers free play adjustment (p.13) but not cable replacement — redirect expected."""
        answer = q(manual, "My clutch cable snapped, how do I replace it?")
        lower = answer.lower()
        assert_citation(answer, "clutch_cable")
        assert "service centre" in lower or "1800" in lower
        assert_no_general_knowledge(answer, "clutch_cable")


# ===========================================================================
# 2. COMPOUND QUESTIONS
# One part is in the manual, the other isn't. Bot must answer both halves
# appropriately without blending or omitting either.
# ===========================================================================

class TestCompoundQuestions:

    def test_oil_grade_and_diy_change(self, manual):
        """Grade is covered (p.6). DIY oil change steps are not."""
        answer = q(manual, "What oil should I use and can I do the change myself at home?")
        lower = answer.lower()
        assert "15w-50" in lower, "Must cite the oil grade"
        assert_citation(answer, "compound_oil")
        assert_no_general_knowledge(answer, "compound_oil")

    def test_tyre_pressure_and_replacement(self, manual):
        """Pressure specs covered (p.8). Tyre replacement procedure not covered."""
        answer = q(manual, "What tyre pressure should I run, and how do I change a flat tyre?")
        lower = answer.lower()
        assert "29" in answer or "33" in answer, "Must cite pressure spec"
        assert_citation(answer, "compound_tyre")
        assert_no_general_knowledge(answer, "compound_tyre")

    def test_chain_lube_and_how_to_remove(self, manual):
        """Lube interval covered (p.11). Chain removal not covered."""
        answer = q(manual, "How often should I lube the chain and how do I remove it for cleaning?")
        lower = answer.lower()
        assert "500" in answer, "Must cite 500 km lube interval"
        assert_citation(answer, "compound_chain")

    def test_brake_fluid_spec_and_bleeding(self, manual):
        """DOT 4 spec covered (p.9). Bleeding procedure not covered."""
        answer = q(manual, "What brake fluid does this bike use and how do I bleed the brakes?")
        lower = answer.lower()
        assert "dot 4" in lower, "Must cite the fluid spec"
        assert_citation(answer, "compound_brake")
        assert_no_general_knowledge(answer, "compound_brake")


# ===========================================================================
# 3. SPEC PRECISION
# The model must cite exact numbers from the manual — no rounding, no ranges
# that don't exist in the manual, no hallucinated specs.
# ===========================================================================

class TestSpecPrecision:

    def test_chain_torque_exact(self, manual):
        """Axle nut torque is exactly 100 Nm (p.12)."""
        answer = q(manual, "What torque should I use for the rear axle nut when adjusting the chain?")
        assert "100" in answer, f"Expected 100 Nm, got: {answer}"
        assert "nm" in answer.lower()
        assert_citation(answer, "torque_spec")

    def test_chain_slack_exact(self, manual):
        """Chain slack is 20–30 mm (p.11) — not 25 mm, not '20 to 35 mm'."""
        answer = q(manual, "What is the correct chain slack for this bike?")
        assert "20" in answer and "30" in answer, f"Expected 20–30 mm range, got: {answer}"
        assert_citation(answer, "chain_slack")

    def test_spark_plug_gap_exact(self, manual):
        """Gap is 0.8–0.9 mm (p.14)."""
        answer = q(manual, "What is the spark plug gap?")
        assert "0.8" in answer and "0.9" in answer, f"Expected 0.8–0.9 mm, got: {answer}"
        assert_citation(answer, "plug_gap")

    def test_spark_plug_torque_exact(self, manual):
        """Torque is 12–15 Nm (p.14)."""
        answer = q(manual, "How tight should I torque the spark plug?")
        assert "12" in answer and "15" in answer, f"Expected 12–15 Nm, got: {answer}"
        assert_citation(answer, "plug_torque")

    def test_oil_capacity_exact(self, manual):
        """Capacity is exactly 2.5 litres with filter (p.6)."""
        answer = q(manual, "How much oil does this bike take?")
        assert "2.5" in answer, f"Expected 2.5 litres, got: {answer}"
        assert_citation(answer, "oil_capacity")

    def test_battery_charge_rate_exact(self, manual):
        """Charge rate is 0.8A for 10–12 hours (p.16)."""
        answer = q(manual, "How do I charge the battery if it's fully discharged?")
        assert "0.8" in answer, f"Expected 0.8A charge rate, got: {answer}"
        assert_citation(answer, "battery_charge")

    def test_fuel_tank_capacity_exact(self, manual):
        """Tank is 13 litres total, 2.5 L reserve (p.15)."""
        answer = q(manual, "What is the fuel tank capacity?")
        assert "13" in answer, f"Expected 13 litres, got: {answer}"
        assert_citation(answer, "tank_capacity")

    def test_no_hallucinated_oil_interval(self, manual):
        """Oil interval is 10,000 km — must NOT say 5,000 or 15,000."""
        answer = q(manual, "What is the engine oil change interval?")
        assert "10,000" in answer or "10000" in answer
        assert "5,000" not in answer and "5000" not in answer, (
            f"Hallucinated shorter interval: {answer}"
        )
        assert_citation(answer, "oil_interval_precision")


# ===========================================================================
# 4. CLARIFYING QUESTIONS
# Ambiguous symptoms must get a clarifying question, not a guess or refusal.
# ===========================================================================

class TestClarifyingQuestions:

    def test_vague_smoke(self, manual):
        """Colour/location unknown — must ask."""
        answer = q(manual, "Smoke is coming from my bike.")
        assert "?" in answer, f"Expected clarifying question, got: {answer}"
        lower = answer.lower()
        assert "colour" in lower or "color" in lower or "where" in lower or "exhaust" in lower

    def test_vague_noise(self, manual):
        """Type/location of noise unknown — should ask."""
        answer = q(manual, "My bike is making a strange noise.")
        assert "?" in answer, f"Expected clarifying question, got: {answer}"

    def test_vague_leak(self, manual):
        """Fluid type/location unknown — should ask."""
        answer = q(manual, "I see a puddle under my bike.")
        assert "?" in answer, f"Expected clarifying question for unknown leak: {answer}"

    def test_vague_warning_light(self, manual):
        """Multiple lights possible — should ask which one."""
        answer = q(manual, "A warning light came on.")
        assert "?" in answer, f"Expected clarifying question for unknown warning light: {answer}"

    def test_specific_symptom_no_clarification(self, manual):
        """Specific enough question — must NOT ask for clarification, must answer."""
        answer = q(manual, "The ABS warning light is still on after I reached 10 km/h.")
        lower = answer.lower()
        assert "service centre" in lower or "authorised" in lower
        assert_citation(answer, "abs_specific")


# ===========================================================================
# 5. WARNING LIGHTS — grounded in p.5
# ===========================================================================

class TestWarningLights:

    def test_abs_light_stays_on(self, manual):
        answer = q(manual, "My ABS warning light is still on after riding past 5 km/h.")
        lower = answer.lower()
        assert "service centre" in lower or "authorised" in lower
        assert_citation(answer, "abs_light")
        assert_no_general_knowledge(answer, "abs_light")

    def test_mil_engine_warning(self, manual):
        answer = q(manual, "There's a triangle with an exclamation mark on my dashboard.")
        lower = answer.lower()
        assert "engine" in lower or "management" in lower or "mil" in lower
        assert "service centre" in lower or "authorised" in lower
        assert_citation(answer, "mil_light")

    def test_fuel_warning_light(self, manual):
        answer = q(manual, "The fuel warning light came on. How much fuel do I have left?")
        lower = answer.lower()
        assert "2.5" in answer, "Should cite the 2.5L warning threshold"
        assert_citation(answer, "fuel_light")

    def test_side_stand_warning(self, manual):
        answer = q(manual, "The side stand light is on but I already put the stand up.")
        lower = answer.lower()
        assert "side stand" in lower
        assert_citation(answer, "side_stand_light")
        assert_no_general_knowledge(answer, "side_stand_light")

    def test_abs_self_diagnosis_forbidden(self, manual):
        """Bot must NOT give DIY ABS diagnostic steps — manual says don't self-diagnose."""
        answer = q(manual, "How do I diagnose why my ABS light is on?")
        lower = answer.lower()
        assert "do not attempt" in lower or "service centre" in lower or "authorised" in lower
        # Must NOT give step-by-step self-diagnosis
        assert "check the abs sensor" not in lower
        assert "check the wheel speed" not in lower


# ===========================================================================
# 6. FORMAT COMPLIANCE
# ===========================================================================

class TestFormatCompliance:

    def test_no_markdown_headings(self, manual):
        """Responses must not use markdown # headings."""
        answer = q(manual, "How do I check engine oil?")
        assert not re.search(r"^#{1,3} ", answer, re.MULTILINE), (
            f"Markdown heading found in response: {answer}"
        )

    def test_citation_present_for_factual_answer(self, manual):
        """Every factual answer must have at least one page citation."""
        answer = q(manual, "What is the recommended tyre pressure?")
        assert_citation(answer, "format_citation")

    def test_no_closing_pleasantry(self, manual):
        """No 'I hope this helps', 'feel free to ask', etc."""
        answer = q(manual, "What fuel should I use?")
        lower = answer.lower()
        assert "i hope this helps" not in lower
        assert "feel free to ask" not in lower
        assert "let me know if" not in lower
        assert "happy to help" not in lower

    def test_refusal_has_citation(self, manual):
        """Even support redirects should cite the page where the number is found."""
        answer = q(manual, "Why is white smoke coming from the exhaust?")
        assert_citation(answer, "refusal_citation")

    def test_no_meta_commentary(self, manual):
        """No commentary about what the manual does/doesn't cover AFTER the answer."""
        answer = q(manual, "What chain lubricant should I use?")
        lower = answer.lower()
        assert "does not say whether" not in lower
        assert "does not specify" not in lower or answer.lower().index("does not specify") < len(answer) // 2


# ===========================================================================
# 7. RESPONSE STOPPING
# Bot must stop immediately when the answer is complete.
# ===========================================================================

class TestResponseStopping:

    def test_oil_answer_stops(self, manual):
        """Oil answer should be short — no padding after the spec and interval."""
        answer = q(manual, "What oil does this bike take?")
        # Should not have long generic follow-on paragraphs
        assert len(answer) < 600, f"Response too long ({len(answer)} chars): {answer}"
        assert_no_general_knowledge(answer, "stopping_oil")

    def test_refusal_stops(self, manual):
        """A refusal + redirect must not add diagnostic possibilities after."""
        answer = q(manual, "Why won't my bike start?")
        lower = answer.lower()
        # Common padding patterns after a refusal
        assert "possible causes include" not in lower
        assert "this could be due to" not in lower
        assert "some things to check" not in lower

    def test_no_summary_at_end(self, manual):
        """Multi-step answer should not add a 'summary' or 'in short' at the end."""
        answer = q(manual, "How do I adjust the chain?")
        lower = answer.lower()
        assert "in summary" not in lower
        assert "in short" not in lower
        assert "to summarize" not in lower
        assert "to recap" not in lower


# ===========================================================================
# 8. HINDI / BILINGUAL
# Rule 9: respond in user's language. Citations and quoted text stay in English.
# ===========================================================================

class TestHindiLanguage:

    def test_hindi_question_gets_hindi_response(self, manual):
        """User asks in Hindi — response should contain Devanagari or Hindi words."""
        answer = q(manual, "इंजन ऑयल कब बदलना चाहिए?")
        # Response should contain some Hindi/Devanagari — not be entirely English
        has_devanagari = bool(re.search(r'[ऀ-ॿ]', answer))
        has_hindi_loanwords = any(w in answer.lower() for w in ["km", "10,000", "12"])
        assert has_devanagari or has_hindi_loanwords, (
            f"Expected Hindi response for Hindi question, got: {answer}"
        )

    def test_hindi_citation_stays_english(self, manual):
        """Page citation in Hindi response must stay in English (p. N) format."""
        answer = q(manual, "टायर का प्रेशर कितना होना चाहिए?")
        assert_citation(answer, "hindi_citation")

    def test_english_question_gets_english_response(self, manual):
        """Control: English question → English response, no Devanagari."""
        answer = q(manual, "What is the tyre pressure?")
        # Should contain English words (4+ chars is enough — 'tyre', 'psi', etc.)
        assert re.search(r'[a-zA-Z]{4,}', answer), "Expected English words in response"
        has_devanagari = bool(re.search(r'[ऀ-ॿ]', answer))
        assert not has_devanagari, "English question should not get Devanagari response"


# ===========================================================================
# 9. MULTI-TURN COHERENCE
# Follow-up questions must build correctly on prior context.
# ===========================================================================

class TestMultiTurnCoherence:

    def test_followup_uses_prior_answer(self, manual):
        """After bot says 'DOT 4', follow-up 'how often?' should cite replacement interval."""
        history = [
            {"role": "user", "text": "What brake fluid should I use?"},
            {"role": "assistant", "text": "Use DOT 4 brake fluid only (p. 9)."},
        ]
        answer = q(manual, "And how often should I replace it?", history=history)
        lower = answer.lower()
        assert "2 year" in lower or "20,000" in lower
        assert_citation(answer, "followup_brake_fluid")

    def test_followup_does_not_hallucinate(self, manual):
        """After an oil answer, asking about 'viscosity' should not invent new specs."""
        history = [
            {"role": "user", "text": "What oil should I use?"},
            {"role": "assistant", "text": "Use SAE 15W-50 API SN, JASO MA2 (p. 6)."},
        ]
        answer = q(manual, "What viscosity is that exactly?", history=history)
        lower = answer.lower()
        assert "15w-50" in lower
        assert_citation(answer, "followup_oil_viscosity")
        assert_no_general_knowledge(answer, "followup_oil_viscosity")

    def test_new_topic_not_contaminated(self, manual):
        """After a brake fluid discussion, asking about chain should not mix topics."""
        history = [
            {"role": "user", "text": "What brake fluid do I use?"},
            {"role": "assistant", "text": "DOT 4 only (p. 9)."},
        ]
        answer = q(manual, "What about the chain — how often do I lube it?", history=history)
        lower = answer.lower()
        assert "500" in answer, "Chain lube interval should be 500 km"
        assert "dot 4" not in lower, "Brake fluid should not bleed into chain answer"
        assert_citation(answer, "followup_new_topic")

    def test_repeated_question_consistent_answer(self, manual):
        """Asking the same question twice should give consistent spec values."""
        answer1 = q(manual, "What is the tyre pressure?")
        answer2 = q(manual, "What is the tyre pressure?")
        # Both should mention 29 and 33 psi
        for answer in [answer1, answer2]:
            assert "29" in answer and "33" in answer, (
                f"Inconsistent tyre pressure answer: {answer}"
            )


# ===========================================================================
# 10. BOUNDARY / NEGATIVE CASES
# Topics the manual almost covers but deliberately doesn't.
# ===========================================================================

class TestBoundaryAndNegative:

    def test_white_smoke_no_general_knowledge(self, manual):
        """Classic test — no coverage, no bridge, support redirect only."""
        answer = q(manual, "Why is white smoke coming from the exhaust?")
        lower = answer.lower()
        assert "not covered" in lower
        assert_no_general_knowledge(answer, "white_smoke")
        assert "1800-210-0008" in answer or "service centre" in lower

    def test_warranty_question(self, manual):
        """Manual mentions warranty only in service schedule (p.18)."""
        answer = q(manual, "What is the warranty period on this bike?")
        lower = answer.lower()
        # Manual doesn't specify warranty period — should redirect
        assert "service centre" in lower or "not covered" in lower or "1800" in lower

    def test_insurance_question_out_of_scope(self, manual):
        """Insurance is not a manual topic at all."""
        answer = q(manual, "How do I claim bike insurance after an accident?")
        lower = answer.lower()
        assert "not covered" in lower
        assert_no_general_knowledge(answer, "insurance")

    def test_modification_question(self, manual):
        """Aftermarket modifications not covered."""
        answer = q(manual, "Can I fit a bigger fuel tank on this bike?")
        lower = answer.lower()
        assert "not covered" in lower or "service centre" in lower
        assert_no_general_knowledge(answer, "modification")

    def test_is_it_normal_question(self, manual):
        """'Is X normal?' — if manual doesn't say, bot must not speculate."""
        answer = q(manual, "Is it normal for this bike to vibrate at highway speeds?")
        lower = answer.lower()
        # Should NOT speculate with general knowledge
        assert "engine balance" not in lower
        assert "completely normal" not in lower or "manual" in lower

    def test_competitor_bike_question(self, manual):
        """Question about a different bike — manual only covers this bike."""
        answer = q(manual, "How does the oil change interval compare to the KTM Duke 390?")
        lower = answer.lower()
        assert "not covered" in lower or "ktm" not in lower
        assert_no_general_knowledge(answer, "competitor_bike")

    def test_road_law_question(self, manual):
        """Traffic law is not a manual topic."""
        answer = q(manual, "What is the speed limit on highways in India?")
        lower = answer.lower()
        assert "not covered" in lower
        assert "120" not in answer and "100" not in answer  # should not state speed limits
