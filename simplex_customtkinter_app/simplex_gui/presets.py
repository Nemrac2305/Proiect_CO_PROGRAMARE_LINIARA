from __future__ import annotations

from .models import LPProblem


PRESET_PROBLEMS: dict[str, LPProblem] = {
    "Demo MAX (<=)": LPProblem(
        name="Demo MAX (<=)",
        optimization="max",
        objective=[3.0, 5.0],
        constraints=[
            [2.0, 3.0],
            [2.0, 1.0],
        ],
        rhs=[8.0, 4.0],
        relations=["<=", "<="],
    ),
    "Demo MIN (Big-M)": LPProblem(
        name="Demo MIN (Big-M)",
        optimization="min",
        objective=[1.0, 2.0],
        constraints=[
            [1.0, 1.0],
            [1.0, 3.0],
        ],
        rhs=[4.0, 6.0],
        relations=[">=", "=="],
    ),
    "Demo MAX (solutii multiple)": LPProblem(
        name="Demo MAX (solutii multiple)",
        optimization="max",
        objective=[1.0, 1.0],
        constraints=[
            [1.0, 1.0],
            [1.0, 0.0],
            [0.0, 1.0],
        ],
        rhs=[4.0, 4.0, 4.0],
        relations=["<=", "<=", "<="],
    ),
    "Demo MAX (normalizare b<0)": LPProblem(
        name="Demo MAX (normalizare b<0)",
        optimization="max",
        objective=[2.0, 1.0],
        constraints=[
            [1.0, 1.0],
            [1.0, -1.0],
            [1.0, 0.0],
        ],
        rhs=[4.0, -1.0, 3.0],
        relations=["<=", ">=", "<="],
    ),
}
