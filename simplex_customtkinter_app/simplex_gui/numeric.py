from __future__ import annotations

from fractions import Fraction
from typing import Final

EPS: Final[float] = 1e-9
DECIMAL_PLACES: Final[int] = 6
MAX_FRACTION_DENOMINATOR: Final[int] = 1000
FRACTION_TOLERANCE: Final[float] = 1e-9

NumberInput = str | int | float


def normalize_number(value: float, eps: float = EPS) -> float:
    """Curata artefactele numerice foarte mici si valorile aproape intregi."""

    if abs(value) <= eps:
        return 0.0

    rounded_integer = round(value)
    if abs(value - rounded_integer) <= eps:
        return float(rounded_integer)

    return float(value)



def format_decimal(value: float, decimal_places: int = DECIMAL_PLACES) -> str:
    text = f"{value:.{decimal_places}f}".rstrip("0").rstrip(".")
    if text in {"", "-0"}:
        return "0"
    return text



def try_fraction(
    value: float,
    *,
    max_denominator: int = MAX_FRACTION_DENOMINATOR,
    tolerance: float = FRACTION_TOLERANCE,
) -> Fraction | None:
    """Intoarce o fractie simpla doar daca reprezinta fidel valoarea data."""

    candidate = Fraction(str(round(value, 12))).limit_denominator(max_denominator)
    if abs(value - float(candidate)) <= tolerance:
        return candidate
    return None



def format_number(
    value: float | None,
    *,
    max_denominator: int = MAX_FRACTION_DENOMINATOR,
    tolerance: float = FRACTION_TOLERANCE,
    decimal_places: int = DECIMAL_PLACES,
    prefer_fraction: bool = True,
) -> str:
    """Afiseaza numerele intr-un mod compact si lizibil.

    Reguli:
    - None -> '-'
    - aproape zero -> '0'
    - aproape intreg -> intreg
    - daca valoarea este foarte aproape de o fractie simpla si forma a/b este mai scurta
      sau la fel de scurta ca forma zecimala, afiseaza fractia
    - altfel pastreaza forma zecimala compacta
    """

    if value is None:
        return "-"

    normalized = normalize_number(float(value), eps=tolerance)
    if normalized.is_integer():
        return str(int(normalized))

    decimal_text = format_decimal(normalized, decimal_places)
    if not prefer_fraction:
        return decimal_text

    fraction = try_fraction(
        normalized,
        max_denominator=max_denominator,
        tolerance=tolerance,
    )
    if fraction is None or fraction.denominator == 1:
        return decimal_text

    fraction_text = str(fraction)
    if len(fraction_text) <= len(decimal_text):
        return fraction_text

    return decimal_text



def parse_number(value: NumberInput) -> float:
    """Accepta atat zecimale, cat si fractii simple de forma a/b."""

    if isinstance(value, (int, float)):
        return float(value)

    raw = str(value).strip().replace(",", ".")
    if not raw:
        raise ValueError("Valoarea este goala.")

    if "/" not in raw:
        return float(raw)

    if raw.count("/") != 1:
        raise ValueError("Fractia trebuie sa contina exact un singur '/'.")

    numerator_text, denominator_text = raw.split("/", 1)
    numerator = float(numerator_text.strip())
    denominator = float(denominator_text.strip())

    if abs(denominator) <= EPS:
        raise ValueError("Numitorul fractiei nu poate fi zero.")

    return numerator / denominator
