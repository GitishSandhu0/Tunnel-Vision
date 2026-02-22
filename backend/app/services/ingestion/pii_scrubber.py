from __future__ import annotations

import re
from typing import List

# ---------------------------------------------------------------------------
# Compiled regex patterns (compiled once at module load for performance)
# ---------------------------------------------------------------------------

# Email addresses  –  user@example.com
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b"
)

# US phone numbers in various formats:
#   (555) 123-4567  |  555-123-4567  |  +1-555-123-4567  |  5551234567
_PHONE_RE = re.compile(
    r"""
    (?:\+?1[\s.\-]?)?         # optional country code
    (?:\(?\d{3}\)?[\s.\-]?)   # area code  (with or without parens)
    \d{3}[\s.\-]?\d{4}        # local number
    """,
    re.VERBOSE,
)

# US Social Security Numbers:
#   Formatted:   123-45-6789  |  123 45 6789
#   Unformatted: 123456789   (9 consecutive digits not starting with 000/666/9xx)
_SSN_RE = re.compile(
    r"\b(?!000|666|9\d{2})\d{3}(?:[- ]\d{2}[- ]\d{4}|\d{6})\b"
)

# Payment card numbers (Visa, MC, Amex, Discover) – 13–16 digit groups
_CREDIT_CARD_RE = re.compile(
    r"""
    \b
    (?:
        4\d{3}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}   # Visa
      | 5[1-5]\d{2}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}  # MasterCard
      | 3[47]\d{2}[\s\-]?\d{6}[\s\-]?\d{5}             # Amex
      | 6(?:011|5\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}  # Discover
    )
    \b
    """,
    re.VERBOSE,
)

# IPv4 addresses:  192.168.1.1  |  10.0.0.1
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# IPv6 addresses (simplified pattern covering common forms)
_IPV6_RE = re.compile(
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
    r"|(?:[0-9a-fA-F]{1,4}:){1,7}:"
    r"|::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}"
)

# US Passport-style numbers (letter + 8 digits):  A12345678
_PASSPORT_RE = re.compile(r"\b[A-Z]\d{8}\b")

# US Driver License-like patterns (state-code + alphanumeric):  CA-D1234567
_DL_RE = re.compile(
    r"\b[A-Z]{1,2}[\s\-]?[A-Z0-9]{6,9}\b"
)

# Date of birth patterns:  01/01/1990  |  01-01-1990  |  1990-01-01
_DOB_RE = re.compile(
    r"\b(?:\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{2}[/\-]\d{2})\b"
)

# Street addresses (simplified):  "123 Main St"  |  "45 Oak Avenue Apt 2"
_STREET_ADDRESS_RE = re.compile(
    r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,3}(?:St(?:reet)?|Ave(?:nue)?|Blvd|Rd|Dr|Ln|Ct|Pl|Way)\b",
    re.IGNORECASE,
)

# Ordered list of (compiled_pattern, replacement_label)
_PATTERNS: list[tuple[re.Pattern, str]] = [
    (_SSN_RE, "[REDACTED-SSN]"),
    (_CREDIT_CARD_RE, "[REDACTED-CARD]"),
    (_EMAIL_RE, "[REDACTED-EMAIL]"),
    (_PHONE_RE, "[REDACTED-PHONE]"),
    (_IPV6_RE, "[REDACTED-IP]"),
    (_IPV4_RE, "[REDACTED-IP]"),
    (_STREET_ADDRESS_RE, "[REDACTED-ADDRESS]"),
    (_DOB_RE, "[REDACTED-DOB]"),
    (_PASSPORT_RE, "[REDACTED-ID]"),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scrub_pii(text: str) -> str:
    """
    Remove PII from a single text string using regex substitution.

    Patterns are applied in order from most-specific (SSN, credit cards)
    to least-specific (dates) to minimise false positives from overlapping
    pattern ranges.

    Args:
        text: Raw input string potentially containing PII.

    Returns:
        Sanitised string with PII replaced by labelled placeholders.
    """
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def scrub_batch(texts: List[str]) -> List[str]:
    """
    Apply :func:`scrub_pii` to every item in a list of strings.

    Args:
        texts: List of raw text strings from the parser.

    Returns:
        New list of sanitised strings (same order, same length).
    """
    return [scrub_pii(t) for t in texts]
