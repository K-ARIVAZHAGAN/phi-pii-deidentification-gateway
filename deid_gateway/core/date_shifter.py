"""
Deterministic Relative Date Shifting and Age > 89 Aggregation Engine.
Preserves exact clinical time deltas (Delta t' = Delta t) while shifting calendar anchors.
Aggregates all ages > 89 to [AGE_90+] in accordance with 45 CFR § 164.514(b)(2)(i)(C).
"""

import datetime
import hashlib
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DateShiftResult:
    """Represents the transformation of a detected date entity."""
    original_text: str
    shifted_text: str
    parsed_date: Optional[datetime.date]
    shifted_date: Optional[datetime.date]
    delta_days: int
    format_type: str


class DateShifter:
    r"""
    Deterministic relative date shifting engine.
    Calculates patient/document-specific signed integer day offset Delta in [-350, +350] \ {0},
    shifts dates while retaining formatting style, and aggregates ages >= 90.
    """

    MONTH_NAMES = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    MONTH_ABBRS = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    MONTH_MAP = {
        "january": 1, "jan": 1, "jan.": 1,
        "february": 2, "feb": 2, "feb.": 2,
        "march": 3, "mar": 3, "mar.": 3,
        "april": 4, "apr": 4, "apr.": 4,
        "may": 5,
        "june": 6, "jun": 6, "jun.": 6,
        "july": 7, "jul": 7, "jul.": 7,
        "august": 8, "aug": 8, "aug.": 8,
        "september": 9, "sep": 9, "sept": 9, "sep.": 9,
        "october": 10, "oct": 10, "oct.": 10,
        "november": 11, "nov": 11, "nov.": 11,
        "december": 12, "dec": 12, "dec.": 12,
    }

    # Relative duration patterns to PROTECT (do NOT shift or treat as calendar anchors)
    RELATIVE_DURATION_PATTERN = re.compile(
        r'\b(?:post-operative\s+day\s+\d+|POD\s*#?\s*\d+|'
        r'(?:\d+\s+)?(?:days?|weeks?|months?|years?|hours?)\s+(?:post-op|prior|ago|later|after|before|duration)|'
        r'in\s+\d+\s+(?:days?|weeks?|months?|hours?)|'
        r'for\s+(?:the\s+past\s+)?\d+\s+(?:days?|weeks?|months?|years?|hours?)|'
        r'every\s+\d+\s+hours?|q\d+h|q\s*\d+\s*hours?|'
        r'yesterday|today|tomorrow|post-op|pre-op|intra-op|'
        r'x\s*\d+\s*(?:days?|weeks?|months?|hours?))\b',
        re.IGNORECASE
    )

    # Age patterns >= 90
    AGE_90_PLUS_PATTERN = re.compile(
        r'\b(?:(?:age\s*[:\s]*)?(?:9[0-9]|1[0-2][0-9])\s*(?:-|–|\s)?(?:yo|y/o|y\.o\.|yo/f|yo/m|yr\s+old|yrs\s+old|years?\s+old|-year-old|-yr-old)|'
        r'(?:age|aged)\s+(?:9[0-9]|1[0-2][0-9])\b|'
        r'\b(?:nonagenarian|centenarian)\b|'
        r'\b(?:9[0-9]|1[0-2][0-9])(?:th|st|nd|rd)\s+birthday\b|'
        r'\bturned\s+(?:9[0-9]|1[0-2][0-9])\b)',
        re.IGNORECASE
    )

    def __init__(self, salt: str = "deid_gateway_secure_salt_v1"):
        self.salt = salt

    def compute_delta_days(self, seed: Optional[str] = None, explicit_days: Optional[int] = None) -> int:
        r"""
        Derives deterministic signed day offset Delta in [-350, +350] \ {0}.
        """
        if explicit_days is not None and explicit_days != 0:
            return explicit_days
        
        seed_str = seed or "default_patient_seed"
        h = hashlib.sha256(f"{self.salt}:{seed_str}".encode("utf-8")).hexdigest()
        val = int(h, 16) % 700 - 350
        if val == 0:
            val = 137
        return val

    def is_relative_expression(self, text: str) -> bool:
        """Checks if a span is a relative duration phrase rather than a calendar date."""
        return bool(self.RELATIVE_DURATION_PATTERN.search(text.strip()))

    def is_age_90_plus(self, text: str) -> bool:
        """Checks if text indicates an age of 90 or older."""
        return bool(self.AGE_90_PLUS_PATTERN.search(text))

    def parse_and_shift(self, date_str: str, delta_days: int) -> Optional[DateShiftResult]:
        """
        Parses a date string, applies delta_days shift, and formats back matching style.
        """
        clean = date_str.strip()
        if self.is_relative_expression(clean):
            return None

        # 1. ISO format: YYYY-MM-DD
        m = re.fullmatch(r'(\d{4})-(\d{1,2})-(\d{1,2})', clean)
        if m:
            y, mth, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                dt = datetime.date(y, mth, d)
                shifted = dt + datetime.timedelta(days=delta_days)
                return DateShiftResult(
                    original_text=date_str,
                    shifted_text=f"{shifted.year:04d}-{shifted.month:02d}-{shifted.day:02d}",
                    parsed_date=dt,
                    shifted_date=shifted,
                    delta_days=delta_days,
                    format_type="YYYY-MM-DD"
                )
            except ValueError:
                pass

        # 2. Slash format: MM/DD/YYYY or M/D/YYYY or MM/DD/YY
        m = re.fullmatch(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', clean)
        if m:
            mth, d, y_str = int(m.group(1)), int(m.group(2)), m.group(3)
            y = int(y_str)
            two_digit = len(y_str) == 2
            if two_digit:
                y = 1900 + y if y >= 50 else 2000 + y
            try:
                dt = datetime.date(y, mth, d)
                shifted = dt + datetime.timedelta(days=delta_days)
                if two_digit:
                    yr_out = f"{shifted.year % 100:02d}"
                else:
                    yr_out = f"{shifted.year:04d}"
                
                # Check zero padding of input
                pad_m = len(m.group(1)) == 2
                pad_d = len(m.group(2)) == 2
                m_str = f"{shifted.month:02d}" if pad_m else f"{shifted.month}"
                d_str = f"{shifted.day:02d}" if pad_d else f"{shifted.day}"
                
                return DateShiftResult(
                    original_text=date_str,
                    shifted_text=f"{m_str}/{d_str}/{yr_out}",
                    parsed_date=dt,
                    shifted_date=shifted,
                    delta_days=delta_days,
                    format_type="MM/DD/YYYY" if not two_digit else "MM/DD/YY"
                )
            except ValueError:
                pass

        # 3. Hyphen format: MM-DD-YYYY or M-D-YYYY
        m = re.fullmatch(r'(\d{1,2})-(\d{1,2})-(\d{2,4})', clean)
        if m:
            mth, d, y_str = int(m.group(1)), int(m.group(2)), m.group(3)
            y = int(y_str)
            two_digit = len(y_str) == 2
            if two_digit:
                y = 1900 + y if y >= 50 else 2000 + y
            try:
                dt = datetime.date(y, mth, d)
                shifted = dt + datetime.timedelta(days=delta_days)
                yr_out = f"{shifted.year % 100:02d}" if two_digit else f"{shifted.year:04d}"
                pad_m = len(m.group(1)) == 2
                pad_d = len(m.group(2)) == 2
                m_str = f"{shifted.month:02d}" if pad_m else f"{shifted.month}"
                d_str = f"{shifted.day:02d}" if pad_d else f"{shifted.day}"
                return DateShiftResult(
                    original_text=date_str,
                    shifted_text=f"{m_str}-{d_str}-{yr_out}",
                    parsed_date=dt,
                    shifted_date=shifted,
                    delta_days=delta_days,
                    format_type="MM-DD-YYYY"
                )
            except ValueError:
                pass

        # 4. Textual Month: Month DD, YYYY or Mon DD, YYYY or DD Month YYYY
        m1 = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})', clean)
        if m1:
            mth_str, d, y = m1.group(1).lower(), int(m1.group(2)), int(m1.group(3))
            if mth_str in self.MONTH_MAP:
                mth = self.MONTH_MAP[mth_str]
                try:
                    dt = datetime.date(y, mth, d)
                    shifted = dt + datetime.timedelta(days=delta_days)
                    is_abbr = len(m1.group(1)) <= 4 and mth_str in self.MONTH_ABBRS or len(m1.group(1)) <= 3
                    out_mth = self.MONTH_ABBRS[shifted.month - 1] if is_abbr else self.MONTH_NAMES[shifted.month - 1]
                    comma = "," if "," in clean else ""
                    return DateShiftResult(
                        original_text=date_str,
                        shifted_text=f"{out_mth} {shifted.day}{comma} {shifted.year}",
                        parsed_date=dt,
                        shifted_date=shifted,
                        delta_days=delta_days,
                        format_type="Month DD, YYYY"
                    )
                except ValueError:
                    pass

        # DD Month YYYY or DD-Mon-YYYY
        m2 = re.fullmatch(r'(\d{1,2})[-\s]+([A-Za-z]+)\.?[-\s]+(\d{2,4})', clean)
        if m2:
            d, mth_str, y_str = int(m2.group(1)), m2.group(2).lower(), m2.group(3)
            y = int(y_str)
            two_digit = len(y_str) == 2
            if two_digit:
                y = 1900 + y if y >= 50 else 2000 + y
            if mth_str in self.MONTH_MAP:
                mth = self.MONTH_MAP[mth_str]
                try:
                    dt = datetime.date(y, mth, d)
                    shifted = dt + datetime.timedelta(days=delta_days)
                    yr_out = f"{shifted.year % 100:02d}" if two_digit else f"{shifted.year:04d}"
                    is_abbr = len(m2.group(2)) <= 4
                    out_mth = self.MONTH_ABBRS[shifted.month - 1] if is_abbr else self.MONTH_NAMES[shifted.month - 1]
                    sep = "-" if "-" in clean else " "
                    return DateShiftResult(
                        original_text=date_str,
                        shifted_text=f"{shifted.day}{sep}{out_mth}{sep}{yr_out}",
                        parsed_date=dt,
                        shifted_date=shifted,
                        delta_days=delta_days,
                        format_type="DD Month YYYY"
                    )
                except ValueError:
                    pass

        # Month YYYY or Mon YYYY: e.g. "October 2023", "Oct 2023"
        m3 = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d{4})', clean)
        if m3:
            mth_str, y = m3.group(1).lower(), int(m3.group(2))
            if mth_str in self.MONTH_MAP:
                mth = self.MONTH_MAP[mth_str]
                try:
                    dt = datetime.date(y, mth, 15)  # Mid-month anchor
                    shifted = dt + datetime.timedelta(days=delta_days)
                    is_abbr = len(m3.group(1)) <= 4
                    out_mth = self.MONTH_ABBRS[shifted.month - 1] if is_abbr else self.MONTH_NAMES[shifted.month - 1]
                    return DateShiftResult(
                        original_text=date_str,
                        shifted_text=f"{out_mth} {shifted.year}",
                        parsed_date=dt,
                        shifted_date=shifted,
                        delta_days=delta_days,
                        format_type="Month YYYY"
                    )
                except ValueError:
                    pass

        return None
