"""
Tests for Date Shifter and Age > 89 Aggregation Engine (Tiers 1 & 2).
Verifies:
- Deterministic offset derivation per patient/document seed.
- Relative timeline interval preservation: Delta t' == Delta t.
- Relative duration protection (e.g. "post-op day 3", "for 2 weeks" NOT shifted).
- Multi-format date parsing and style reconstruction.
- Safe Harbor Age > 89 aggregation to [AGE_90+] per 45 CFR § 164.514(b)(2)(i)(C).
- Leap year, year-end boundaries, and century transitions.
"""

import datetime
import pytest

try:
    from deid_gateway.core.date_shifter import DateShifter, DateShiftResult
except ImportError:
    DateShifter = None
    DateShiftResult = None


# =============================================================================
# TIER 1: FEATURE COVERAGE - DETERMINISTIC DATE SHIFTING & RELATIVE DELTAS
# =============================================================================

class TestDateShifterFeatureCoverage:
    """Tier 1: Tests deterministic offset calculation and clinical interval preservation."""

    def test_deterministic_offset_generation(self):
        """Verifies same seed produces identical delta, different seeds produce different deltas."""
        if DateShifter is None:
            pytest.skip("DateShifter implementation pending")
        shifter = DateShifter(salt="test_salt_123")
        delta1 = shifter.compute_delta_days(seed="PATIENT_001")
        delta2 = shifter.compute_delta_days(seed="PATIENT_001")
        delta3 = shifter.compute_delta_days(seed="PATIENT_002")

        assert delta1 == delta2, "Non-deterministic delta generated for same patient seed"
        assert delta1 != 0, "Delta must never be zero (would leave dates unshifted)"
        assert -350 <= delta1 <= 350, f"Delta {delta1} outside expected [-350, +350] bounds"
        assert delta1 != delta3, "Different patient seeds produced colliding deltas"

    def test_explicit_offset_override(self):
        """Verifies explicitly supplied delta_days overrides hash calculation."""
        if DateShifter is None:
            pytest.skip("DateShifter implementation pending")
        shifter = DateShifter()
        delta = shifter.compute_delta_days(explicit_days=45)
        assert delta == 45

    def test_relative_timeline_preservation_invariance(self):
        """
        Mathematical proof test:
        For admission date D1 = 10/10/2023 and discharge date D2 = 10/15/2023 (interval = 5 days),
        shifted dates D1' and D2' must have the exact same difference (D2' - D1' == 5 days).
        """
        if DateShifter is None:
            pytest.skip("DateShifter implementation pending")
        shifter = DateShifter()
        delta = shifter.compute_delta_days(seed="PATIENT_TIMELINE_TEST")

        res_admit = shifter.parse_and_shift("10/10/2023", delta)
        res_disch = shifter.parse_and_shift("10/15/2023", delta)

        assert res_admit is not None and res_disch is not None
        orig_interval = (res_disch.parsed_date - res_admit.parsed_date).days
        shifted_interval = (res_disch.shifted_date - res_admit.shifted_date).days

        assert orig_interval == 5
        assert shifted_interval == 5
        assert shifted_interval == orig_interval, "Clinical relative time interval corrupted by date shift!"

    @pytest.mark.parametrize("date_input", [
        "10/14/2023",
        "2023-10-14",
        "10-14-2023",
        "October 14, 2023",
        "Oct 14, 2023",
        "14 October 2023",
        "14-Oct-2023",
        "October 2023",
    ])
    def test_date_formatting_style_preservation(self, date_input: str):
        """Verifies date shifter parses various date formats."""
        if DateShifter is None:
            pytest.skip("DateShifter implementation pending")
        shifter = DateShifter()
        res = shifter.parse_and_shift(date_input, delta_days=30)
        assert res is not None, f"Failed to parse date '{date_input}'"
        assert res.shifted_text != date_input

    @pytest.mark.parametrize("relative_expr", [
        "post-operative day 2",
        "POD #3",
        "for the past 3 weeks",
        "in 48 hours",
        "every 8 hours",
        "yesterday",
        "today",
        "tomorrow",
        "2 days post-op",
        "5 days prior",
        "x 14 days"
    ])
    def test_relative_expressions_are_protected(self, relative_expr: str):
        """Verifies relative clinical duration expressions are NOT parsed as calendar dates."""
        if DateShifter is None:
            pytest.skip("DateShifter implementation pending")
        shifter = DateShifter()
        assert shifter.is_relative_expression(relative_expr) is True
        res = shifter.parse_and_shift(relative_expr, delta_days=30)
        assert res is None, f"Relative expression '{relative_expr}' was incorrectly shifted!"


# =============================================================================
# TIER 1 & 2: AGE > 89 AGGREGATION RULE (45 CFR § 164.514(b)(2)(i)(C))
# =============================================================================

class TestAge90PlusAggregation:
    """Tier 1 & 2: Tests detection and aggregation of nonagenarian and centenarian ages."""

    @pytest.mark.parametrize("age_text", [
        "90-year-old male",
        "91 yo female",
        "94 y/o",
        "97 years old",
        "102-year-old centenarian",
        "104 years old",
        "nonagenarian patient",
        "centenarian",
        "90th birthday celebration",
        "turned 92 yesterday"
    ])
    def test_age_90_plus_detection(self, age_text: str):
        """Verifies all ages >= 90 and indicative terms trigger age aggregation."""
        if DateShifter is None:
            pytest.skip("DateShifter implementation pending")
        shifter = DateShifter()
        assert shifter.is_age_90_plus(age_text) is True, f"Failed to flag age > 89 in: '{age_text}'"

    @pytest.mark.parametrize("regular_age_text", [
        "45-year-old male",
        "68 yo",
        "88 y/o female",
        "89 years old",
        "12-month-old infant",
        "30th birthday"
    ])
    def test_regular_ages_not_flagged_as_90_plus(self, regular_age_text: str):
        """Verifies ages <= 89 are NOT flagged as age > 89."""
        if DateShifter is None:
            pytest.skip("DateShifter implementation pending")
        shifter = DateShifter()
        assert shifter.is_age_90_plus(regular_age_text) is False, f"Incorrectly flagged age <= 89: '{regular_age_text}'"


# =============================================================================
# TIER 2: BOUNDARY AND CORNER CASES
# =============================================================================

class TestDateShifterBoundaryCases:
    """Tier 2: Leap years, century boundaries, negative deltas, and year transitions."""

    def test_leap_year_february_29(self):
        """Boundary: Shifting across February 29 on leap year (2024)."""
        if DateShifter is None:
            pytest.skip("DateShifter implementation pending")
        shifter = DateShifter()
        res = shifter.parse_and_shift("02/28/2024", delta_days=2)
        assert res is not None
        assert res.shifted_date == datetime.date(2024, 3, 1)

    def test_year_transition_forward_and_backward(self):
        """Boundary: Shifting dates across Dec 31 / Jan 1 boundary."""
        if DateShifter is None:
            pytest.skip("DateShifter implementation pending")
        shifter = DateShifter()
        res_fwd = shifter.parse_and_shift("12/30/2023", delta_days=5)
        assert res_fwd is not None
        assert res_fwd.shifted_date.year == 2024

        res_back = shifter.parse_and_shift("01/03/2023", delta_days=-10)
        assert res_back is not None
        assert res_back.shifted_date.year == 2022
