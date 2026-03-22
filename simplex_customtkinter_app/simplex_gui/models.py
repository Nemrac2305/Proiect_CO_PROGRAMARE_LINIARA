from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from .numeric import parse_number

Relation = Literal["<=", ">=", "=="]
OptimizationType = Literal["max", "min"]


@dataclass(slots=True)
class LPProblem:
    """Defineste o problema de programare liniara in forma generala.

    Toate variabilele principale sunt presupuse nenegative.
    """

    optimization: OptimizationType
    objective: list[float]
    constraints: list[list[float]]
    rhs: list[float]
    relations: list[Relation]
    name: str = "Problema fara nume"

    @property
    def n_variables(self) -> int:
        return len(self.objective)

    @property
    def n_constraints(self) -> int:
        return len(self.constraints)

    def validate(self) -> None:
        if self.optimization not in {"max", "min"}:
            raise ValueError("Tipul de optimizare trebuie sa fie 'max' sau 'min'.")

        if not self.objective:
            raise ValueError("Functia obiectiv trebuie sa contina cel putin o variabila.")

        if not self.constraints:
            raise ValueError("Problema trebuie sa contina cel putin o restrictie.")

        if len(self.constraints) != len(self.rhs) or len(self.constraints) != len(self.relations):
            raise ValueError("Numarul de restrictii, termeni liberi si relatii nu coincide.")

        n = len(self.objective)
        for i, row in enumerate(self.constraints, start=1):
            if len(row) != n:
                raise ValueError(
                    f"Restrictia #{i} are {len(row)} coeficienti, dar functia obiectiv are {n} variabile."
                )

        for relation in self.relations:
            if relation not in {"<=", ">=", "=="}:
                raise ValueError("Relatiile permise sunt <=, >= si ==.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "optimization": self.optimization,
            "objective": list(self.objective),
            "constraints": [list(row) for row in self.constraints],
            "rhs": list(self.rhs),
            "relations": list(self.relations),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LPProblem":
        problem = cls(
            name=str(data.get("name", "Problema incarcata")),
            optimization=str(data["optimization"]),
            objective=[parse_number(x) for x in data["objective"]],
            constraints=[[parse_number(x) for x in row] for row in data["constraints"]],
            rhs=[parse_number(x) for x in data["rhs"]],
            relations=[str(x) for x in data["relations"]],
        )
        problem.validate()
        return problem


@dataclass(slots=True)
class ConstraintCheck:
    index: int
    lhs: float
    relation: Relation
    rhs: float
    ok: bool


@dataclass(slots=True)
class VerificationReport:
    objective_from_solution: float
    objective_matches: bool
    reconstructed_rhs: list[float]
    rhs_matches: bool
    normalized_rhs: list[float] = field(default_factory=list)
    basis_submatrix: list[list[float]] = field(default_factory=list)
    constraint_checks: list[ConstraintCheck] = field(default_factory=list)


@dataclass(slots=True)
class AlternateSolution:
    entering_variable: int
    leaving_row: int
    basis: list[int]
    solution: list[float]
    objective_value: float


@dataclass(slots=True)
class IterationSnapshot:
    index: int
    tableau: list[list[float]]
    basis: list[int]
    cb: list[float]
    xb: list[float]
    z: list[float]
    delta: list[float]
    objective_value: float
    pivot_row: Optional[int] = None
    pivot_col: Optional[int] = None
    message: str = ""


@dataclass(slots=True)
class SolveResult:
    status: str = "not_started"
    status_message: str = ""
    objective_value: Optional[float] = None
    solution: list[float] = field(default_factory=list)
    variable_labels: list[str] = field(default_factory=list)
    final_basis: list[int] = field(default_factory=list)
    final_xb: list[float] = field(default_factory=list)
    iterations: list[IterationSnapshot] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    verification: Optional[VerificationReport] = None
    normalized_problem_changed: bool = False
    already_standard: bool = False
    standardized_variable_count: int = 0
    added_slack_surplus: int = 0
    added_artificial: int = 0
    big_m_abs: float = 0.0
    multiple_optima_detected: bool = False
    infinite_optimal_family_detected: bool = False
    alternate_optimal_solutions: list[AlternateSolution] = field(default_factory=list)
    error_details: Optional[str] = None
