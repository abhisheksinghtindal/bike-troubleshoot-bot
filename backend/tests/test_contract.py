"""
Contract compliance tests for the bike troubleshooting bot.

Run:
    cd backend
    source .venv/bin/activate
    PYTHONPATH=. pytest tests/test_contract.py -v -s
"""
import re
import pytest
from app.services.claude import ask
from app.store import Manual


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FORBIDDEN_PATTERNS = [
    (r"can indicate",               "used general-knowledge causes list"),
    (r"could indicate",             "used general-knowledge causes list"),
    (r"common causes?",             "listed common causes from general knowledge"),
    (r"possible causes?",           "listed possible causes from general knowledge"),
    (r"do not continue riding",     "added unsolicited generic safety advice"),
    (r"stop riding",                "added unsolicited generic safety advice"),
    (r"pull over",                  "added unsolicited generic safety advice"),
    (r"qualified technician",       "referred to qualified technician (general advice)"),
    (r"professional mechanic",      "referred to professional mechanic (general advice)"),
    (r"what (you should|to) do",   "added 'What to do' section to a refusal"),
    (r"i recommend",                "added a recommendation not from the manual"),
    (r"i (would |)suggest",        "added a suggestion not from the manual"),
    (r"neither of these",           "added editorial closing after quoting manual"),
    (r"does not say whether",       "added meta-commentary after answering"),
    (r"i hope this helps",          "added closing pleasantry"),
    (r"feel free to ask",           "added closing pleasantry"),
]

REFUSAL_OPENER = "this is not covered in the manual you uploaded"


def assert_no_forbidden(response: str, ctx: str = "") -> None:
    lower = response.lower()
    violations = [
        f"  ❌ {desc!r} (pattern: {pat!r})"
        for pat, desc in FORBIDDEN_PATTERNS
        if re.search(pat, lower)
    ]
    if violations:
        pytest.fail(
            f"[{ctx}] Forbidden pattern(s):\n" + "\n".join(violations)
            + f"\n\nFull response:\n{response}"
        )


def assert_clean_refusal(response: str, ctx: str = "") -> None:
    assert REFUSAL_OPENER in response.lower(), (
        f"[{ctx}] Missing required refusal opener.\nResponse: {response}"
    )
    assert_no_forbidden(response, ctx)


def assert_has_citation(response: str, ctx: str = "") -> None:
    assert re.search(r"\(p+\.\s*\d+", response), (
        f"[{ctx}] No page citation found.\nResponse: {response}"
    )


def assert_bridge_present(response: str, ctx: str = "") -> None:
    lower = response.lower()
    has_bridge = (
        "the manual does cover" in lower
        or "would you like me to share" in lower
    )
    assert has_bridge, (
        f"[{ctx}] Expected a bridge to a related section but found none.\n"
        f"Response: {response}"
    )


def assert_support_redirect(response: str, ctx: str = "") -> None:
    lower = response.lower()
    has_redirect = (
        "service centre" in lower
        or "service center" in lower
        or "authorised" in lower
        or "authorized" in lower
        or "1800-123-4567" in lower
    )
    assert has_redirect, (
        f"[{ctx}] Expected support redirect but found none.\nResponse: {response}"
    )


def assert_no_bridge(response: str, ctx: str = "") -> None:
    lower = response.lower()
    assert "the manual does cover" not in lower, (
        f"[{ctx}] Got an unexpected bridge — expected support redirect only.\n"
        f"Response: {response}"
    )


def call(manual: Manual, question: str, history: list | None = None) -> str:
    return ask(manual=manual, question=question, history=history or [])["answer"]


# ---------------------------------------------------------------------------
# 1. IN-MANUAL ANSWERS — must answer with citations, no forbidden patterns
# ---------------------------------------------------------------------------

class TestInManualAnswers:

    def test_oil_change_interval(self, test_manual):
        r = call(test_manual, "How often should I change the engine oil?")
        assert "5,000" in r or "5000" in r
        assert_has_citation(r, "oil_interval")
        assert_no_forbidden(r, "oil_interval")

    def test_oil_grade(self, test_manual):
        r = call(test_manual, "What engine oil grade should I use?")
        assert "10W-40" in r
        assert_has_citation(r, "oil_grade")
        assert_no_forbidden(r, "oil_grade")

    def test_oil_check_steps(self, test_manual):
        r = call(test_manual, "How do I check the engine oil level?")
        assert_has_citation(r, "oil_check_steps")
        assert_no_forbidden(r, "oil_check_steps")

    def test_tyre_pressure_solo(self, test_manual):
        r = call(test_manual, "What should the tyre pressure be?")
        assert "29" in r or "33" in r
        assert_has_citation(r, "tyre_pressure")
        assert_no_forbidden(r, "tyre_pressure")

    def test_tyre_pressure_pillion(self, test_manual):
        r = call(test_manual, "What rear tyre pressure should I use when riding with a pillion?")
        assert "36" in r
        assert_has_citation(r, "tyre_pillion")
        assert_no_forbidden(r, "tyre_pillion")

    def test_brake_fluid_spec(self, test_manual):
        r = call(test_manual, "What brake fluid should I use?")
        assert "DOT 4" in r
        assert_has_citation(r, "brake_fluid")
        assert_no_forbidden(r, "brake_fluid")

    def test_brake_fluid_interval(self, test_manual):
        r = call(test_manual, "How often should I replace brake fluid?")
        assert "2 year" in r.lower() or "two year" in r.lower()
        assert_has_citation(r, "brake_fluid_interval")
        assert_no_forbidden(r, "brake_fluid_interval")

    def test_chain_lubrication_interval(self, test_manual):
        r = call(test_manual, "How often should I lubricate the chain?")
        assert "500" in r
        assert_has_citation(r, "chain_lube")
        assert_no_forbidden(r, "chain_lube")

    def test_chain_slack(self, test_manual):
        r = call(test_manual, "What is the correct chain slack?")
        assert "20" in r and "30" in r
        assert_has_citation(r, "chain_slack")
        assert_no_forbidden(r, "chain_slack")

    def test_clutch_free_play(self, test_manual):
        r = call(test_manual, "How much free play should the clutch lever have?")
        assert "10" in r and "20" in r
        assert_has_citation(r, "clutch_play")
        assert_no_forbidden(r, "clutch_play")

    def test_spark_plug_spec(self, test_manual):
        r = call(test_manual, "What spark plug does this bike use?")
        assert "CR8E" in r or "NGK" in r
        assert_has_citation(r, "spark_plug")
        assert_no_forbidden(r, "spark_plug")

    def test_fuel_octane(self, test_manual):
        r = call(test_manual, "What fuel should I use?")
        assert "91" in r or "RON" in r
        assert_has_citation(r, "fuel_octane")
        assert_no_forbidden(r, "fuel_octane")


# ---------------------------------------------------------------------------
# 2. VALID BRIDGES — not in manual but a functionally related section exists
# ---------------------------------------------------------------------------

class TestValidBridge:

    def test_knocking_engine_bridges_to_oil(self, test_manual):
        """Engine knock → engine oil is a valid functional bridge."""
        r = call(test_manual, "My engine is making a knocking sound.")
        assert_clean_refusal(r, "engine_knock")
        assert_bridge_present(r, "engine_knock")
        assert "p. 3" in r or "p. 4" in r  # oil pages

    def test_spongy_brakes_bridges_to_brake_fluid(self, test_manual):
        """Soft brakes → brake fluid is a valid functional bridge."""
        r = call(test_manual, "My brakes feel spongy and soft.")
        assert_clean_refusal(r, "spongy_brakes")
        assert_bridge_present(r, "spongy_brakes")
        assert "p. 6" in r  # brake fluid page

    def test_chain_jumping_bridges_to_chain_section(self, test_manual):
        """Chain jumping → chain maintenance is a valid functional bridge."""
        r = call(test_manual, "My chain keeps jumping off the sprocket.")
        assert_clean_refusal(r, "chain_jumping")
        assert_bridge_present(r, "chain_jumping")
        assert "p. 7" in r  # chain page

    def test_gear_not_engaging_bridges_to_clutch(self, test_manual):
        """Gear not engaging → clutch adjustment is a valid functional bridge."""
        r = call(test_manual, "My bike won't go into gear properly.")
        assert_clean_refusal(r, "gear_not_engaging")
        assert_bridge_present(r, "gear_not_engaging")
        assert "p. 8" in r  # clutch page

    def test_engine_cutting_out_bridges_to_fuel_or_spark(self, test_manual):
        """Engine cutting out → fuel system or spark plug are valid bridges."""
        r = call(test_manual, "My bike cuts out while riding at speed.")
        assert_clean_refusal(r, "engine_cut_out")
        assert_bridge_present(r, "engine_cut_out")
        lower = r.lower()
        assert "p. 11" in r or "p. 12" in r, (
            f"Expected bridge to spark plug (p.11) or fuel system (p.12).\nResponse: {r}"
        )

    def test_bridge_offer_is_one_sentence(self, test_manual):
        """Bridge must be exactly one sentence — not a paragraph."""
        r = call(test_manual, "My engine is making a knocking sound.")
        lines = [l.strip() for l in r.strip().splitlines() if l.strip()]
        assert len(lines) <= 3, (
            f"Bridge refusal is too long ({len(lines)} lines).\nResponse: {r}"
        )

    def test_bridge_cites_real_page(self, test_manual):
        """Page number in the bridge must actually exist in the manual."""
        r = call(test_manual, "My brakes feel spongy and soft.")
        pages_cited = re.findall(r"p\.\s*(\d+)", r)
        for p in pages_cited:
            assert int(p) <= len(test_manual.pages), (
                f"Cited p.{p} but manual only has {len(test_manual.pages)} pages.\nResponse: {r}"
            )


# ---------------------------------------------------------------------------
# 3. INVALID BRIDGES — keywords match but functionally unrelated
# ---------------------------------------------------------------------------

class TestInvalidBridge:

    def test_white_smoke_does_not_bridge_to_exhaust_heat(self, test_manual):
        """Exhaust heat safety (p.9) is about burn hazard, not smoke diagnosis."""
        r = call(test_manual, "Why is white smoke coming from the exhaust?")
        assert_clean_refusal(r, "white_smoke")
        lower = r.lower()
        assert "heat" not in lower or "p. 9" not in r, (
            f"Incorrectly bridged to exhaust heat section.\nResponse: {r}"
        )

    def test_white_smoke_does_not_bridge_to_evap_emission(self, test_manual):
        """Evaporative emission control (p.10) is about fuel vapour, not exhaust smoke."""
        r = call(test_manual, "Why is white smoke coming from the exhaust?")
        assert_clean_refusal(r, "white_smoke_evap")
        assert "evaporative" not in r.lower(), (
            f"Incorrectly bridged to evaporative emission section.\nResponse: {r}"
        )

    def test_blue_smoke_does_not_bridge_to_exhaust_heat(self, test_manual):
        r = call(test_manual, "Blue smoke is coming from my exhaust pipe.")
        assert_clean_refusal(r, "blue_smoke")
        assert "heat" not in r.lower() or "p. 9" not in r, (
            f"Incorrectly bridged to exhaust heat section.\nResponse: {r}"
        )

    def test_battery_drain_does_not_bridge_to_headlight(self, test_manual):
        """Headlight section (if present) is not a valid bridge for battery drain."""
        r = call(test_manual, "My battery drains overnight.")
        assert_clean_refusal(r, "battery_drain")
        # Should redirect to support, not invent an electrical bridge
        assert_no_forbidden(r, "battery_drain")


# ---------------------------------------------------------------------------
# 4. SUPPORT REDIRECT — no valid bridge, support number must come from manual
# ---------------------------------------------------------------------------

class TestSupportRedirect:

    def test_white_smoke_redirects_to_support(self, test_manual):
        r = call(test_manual, "Why is white smoke coming from my exhaust?")
        assert_clean_refusal(r, "white_smoke_support")
        assert_support_redirect(r, "white_smoke_support")
        assert_no_bridge(r, "white_smoke_support")

    def test_turbocharger_redirects_to_support(self, test_manual):
        r = call(test_manual, "Can I install a turbocharger on this bike?")
        assert_clean_refusal(r, "turbocharger")
        assert_support_redirect(r, "turbocharger")

    def test_overheating_redirects_to_support(self, test_manual):
        r = call(test_manual, "My engine is overheating.")
        assert_clean_refusal(r, "overheating")
        assert_no_forbidden(r, "overheating")

    def test_support_number_is_from_manual(self, test_manual):
        """Support number must be the one in the manual (p.2), not hallucinated."""
        r = call(test_manual, "My bike won't start at all.")
        if "1800" in r:
            assert "1800-123-4567" in r, (
                f"Support number is not the one from this manual.\nResponse: {r}"
            )

    def test_support_number_has_page_citation(self, test_manual):
        """When citing support number, must include page reference."""
        r = call(test_manual, "Why is white smoke coming from my exhaust?")
        if "1800-123-4567" in r:
            assert re.search(r"\(p\.\s*2\)", r), (
                f"Support number cited without page reference.\nResponse: {r}"
            )


# ---------------------------------------------------------------------------
# 5. FORBIDDEN PATTERNS — must never appear in any response
# ---------------------------------------------------------------------------

class TestForbiddenPatterns:

    def test_no_general_knowledge_in_smoke_refusal(self, test_manual):
        r = call(test_manual, "White smoke from exhaust — what does it mean?")
        forbidden_terms = ["coolant", "condensation", "head gasket", "water vapor", "rich fuel", "burning oil"]
        leaked = [t for t in forbidden_terms if t in r.lower()]
        assert not leaked, (
            f"General knowledge leaked: {leaked}\nResponse: {r}"
        )

    def test_no_general_knowledge_in_electrical_refusal(self, test_manual):
        r = call(test_manual, "Why does my bike cut out randomly?")
        forbidden_terms = ["fuel pump", "ignition coil", "cdi", "ecu", "short circuit", "regulator rectifier"]
        leaked = [t for t in forbidden_terms if t in r.lower()]
        assert not leaked, (
            f"General knowledge leaked: {leaked}\nResponse: {r}"
        )

    def test_no_meta_commentary_after_in_manual_answer(self, test_manual):
        r = call(test_manual, "How do I check the engine oil?")
        lower = r.lower()
        assert "does not say whether" not in lower
        assert "neither of these" not in lower
        assert "does not cover" not in lower or REFUSAL_OPENER in lower

    def test_no_closing_pleasantry(self, test_manual):
        r = call(test_manual, "What tyre pressure should I use?")
        lower = r.lower()
        assert "i hope" not in lower
        assert "feel free" not in lower
        assert "let me know" not in lower

    def test_no_unsolicited_safety_advice_in_refusal(self, test_manual):
        r = call(test_manual, "Why does my engine feel weak?")
        lower = r.lower()
        assert "do not ride" not in lower
        assert "stop riding" not in lower
        assert "do not continue" not in lower

    def test_refusal_has_no_what_to_do_section(self, test_manual):
        r = call(test_manual, "My headlight is flickering.")
        lower = r.lower()
        assert "what to do" not in lower
        assert "what you should do" not in lower
        assert "here is what" not in lower


# ---------------------------------------------------------------------------
# 6. CONVERSATION MEMORY — prior turns must carry context
# ---------------------------------------------------------------------------

class TestConversationMemory:

    def test_followup_uses_prior_context(self, test_manual):
        """'What grade should I use for that?' must resolve 'that' from history."""
        r1 = call(test_manual, "How often should I change the engine oil?")
        history = [
            {"role": "user", "text": "How often should I change the engine oil?"},
            {"role": "assistant", "text": r1},
        ]
        r2 = call(test_manual, "What grade should I use for that?", history=history)
        assert "10W-40" in r2, (
            f"Follow-up didn't resolve oil grade from context.\nResponse: {r2}"
        )

    def test_what_to_do_next_after_refusal_uses_context(self, test_manual):
        """'What should I do next?' after a smoke refusal should not ask for clarification."""
        r1 = call(test_manual, "Why is white smoke coming from my exhaust?")
        history = [
            {"role": "user", "text": "Why is white smoke coming from my exhaust?"},
            {"role": "assistant", "text": r1},
        ]
        r2 = call(test_manual, "What should I do next?", history=history)
        lower = r2.lower()
        assert "what situation" not in lower, (
            f"Bot asked for clarification instead of using history.\nResponse: {r2}"
        )
        assert "more context" not in lower, (
            f"Bot asked for more context instead of using history.\nResponse: {r2}"
        )

    def test_yes_share_it_fetches_bridged_section(self, test_manual):
        """After a bridge offer, 'Yes, share it' must return the cited section."""
        r1 = call(test_manual, "My engine is making a knocking sound.")
        history = [
            {"role": "user", "text": "My engine is making a knocking sound."},
            {"role": "assistant", "text": r1},
        ]
        r2 = call(test_manual, "Yes, share it.", history=history)
        assert "10W-40" in r2 or "5,000" in r2 or "oil" in r2.lower(), (
            f"Follow-up didn't fetch the bridged oil section.\nResponse: {r2}"
        )
        assert_has_citation(r2, "bridge_followup")

    def test_smoke_is_emission_same_context(self, test_manual):
        """'Is it same like emission?' after smoke refusal should use memory."""
        r1 = call(test_manual, "Why is white smoke coming from the exhaust?")
        history = [
            {"role": "user", "text": "Why is white smoke coming from the exhaust?"},
            {"role": "assistant", "text": r1},
        ]
        r2 = call(test_manual, "Is it same like emission?", history=history)
        # Should NOT bridge to evaporative emission as if it's related to smoke
        assert "evaporative" not in r2.lower() or "not" in r2.lower(), (
            f"Incorrectly connected smoke to evaporative emission.\nResponse: {r2}"
        )

    def test_multi_turn_stays_grounded(self, test_manual):
        """After 3 turns, bot must still refuse non-manual questions."""
        r1 = call(test_manual, "How often should I change the oil?")
        r2 = call(test_manual, "What grade?", history=[
            {"role": "user", "text": "How often should I change the oil?"},
            {"role": "assistant", "text": r1},
        ])
        history = [
            {"role": "user", "text": "How often should I change the oil?"},
            {"role": "assistant", "text": r1},
            {"role": "user", "text": "What grade?"},
            {"role": "assistant", "text": r2},
        ]
        r3 = call(test_manual, "Why is there white smoke from the exhaust?", history=history)
        assert_clean_refusal(r3, "multi_turn_grounded")


# ---------------------------------------------------------------------------
# 7. REFUSAL FORMAT
# ---------------------------------------------------------------------------

class TestRefusalFormat:

    def test_refusal_opens_with_contract_phrase(self, test_manual):
        r = call(test_manual, "Why is blue smoke coming from the exhaust?")
        assert r.lower().startswith("this is not covered"), (
            f"Refusal didn't open with contract phrase.\nStarts with: {r[:100]!r}"
        )

    def test_refusal_with_bridge_is_short(self, test_manual):
        r = call(test_manual, "My engine is making a knocking sound.")
        sentences = [s.strip() for s in re.split(r"[.!?]+", r) if s.strip()]
        assert len(sentences) <= 3, (
            f"Bridge refusal too long ({len(sentences)} sentences).\nResponse: {r}"
        )

    def test_support_redirect_refusal_is_short(self, test_manual):
        r = call(test_manual, "Why is white smoke coming from the exhaust?")
        sentences = [s.strip() for s in re.split(r"[.!?]+", r) if s.strip()]
        assert len(sentences) <= 3, (
            f"Support-redirect refusal too long ({len(sentences)} sentences).\nResponse: {r}"
        )
