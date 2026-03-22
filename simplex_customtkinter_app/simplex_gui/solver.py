from __future__ import annotations

from dataclasses import asdict

from .numeric import format_number

from .models import (
    AlternateSolution,
    ConstraintCheck,
    IterationSnapshot,
    LPProblem,
    OptimizationType,
    Relation,
    SolveResult,
    VerificationReport,
)

EPS = 1e-9


# -----------------------------------------------------------------------------
# Utilitare numerice si copii defensive
# -----------------------------------------------------------------------------

def nearly_zero(value: float, eps: float = EPS) -> bool:
    return abs(value) <= eps



def are_equal(left: float, right: float, eps: float = EPS) -> bool:
    return abs(left - right) <= eps



def is_positive(value: float, eps: float = EPS) -> bool:
    return value > eps



def is_negative(value: float, eps: float = EPS) -> bool:
    return value < -eps



def clone_vector(values: list[float] | list[int]) -> list:
    return list(values)



def clone_matrix(matrix: list[list[float]]) -> list[list[float]]:
    return [list(row) for row in matrix]



def sanitize_number(value: float) -> float:
    rounded = round(value, 10)
    return 0.0 if nearly_zero(rounded) else rounded



def default_variable_labels(n_variables: int) -> list[str]:
    return [f"x{index + 1}" for index in range(n_variables)]


# -----------------------------------------------------------------------------
# Transformari problema
# -----------------------------------------------------------------------------

def normalize_constraints(
    coefficients: list[list[float]],
    rhs: list[float],
    relations: list[Relation],
) -> bool:
    """Asigura b >= 0, exact ca in codul initial."""

    changed = False

    for i, row in enumerate(coefficients):
        if is_negative(rhs[i]):
            rhs[i] = -rhs[i]
            for j in range(len(row)):
                row[j] = -row[j]
            if relations[i] == "<=":
                relations[i] = ">="
            elif relations[i] == ">=":
                relations[i] = "<="
            changed = True

        rhs[i] = sanitize_number(rhs[i])
        for j in range(len(row)):
            row[j] = sanitize_number(row[j])

    return changed



def find_identity_basis(coefficients: list[list[float]], n_rows: int, n_columns: int) -> list[int]:
    basis: list[int] = []
    used_columns: set[int] = set()

    for i in range(n_rows):
        found = False
        for j in range(n_columns):
            if j in used_columns:
                continue
            if are_equal(coefficients[i][j], 1.0):
                valid = True
                for k in range(n_rows):
                    if k != i and not nearly_zero(coefficients[k][j]):
                        valid = False
                        break
                if valid:
                    basis.append(j)
                    used_columns.add(j)
                    found = True
                    break
        if not found:
            return []

    return basis



def compute_big_m(c: list[float], a: list[list[float]], b: list[float]) -> float:
    total = 1.0
    total += sum(abs(value) for value in c)
    total += sum(abs(value) for row in a for value in row)
    total += sum(abs(value) for value in b)
    #return max(1000.0, 10.0 * total)
    return 1000.0



def standardize_problem(
    coefficients: list[list[float]],
    rhs: list[float],
    objective: list[float],
    relations: list[Relation],
    optimization: OptimizationType,
) -> tuple[list[list[float]], list[float], list[float], list[int], int, int, float, list[str]]:
    """Transforma problema in PLS prin slack/surplus + Big-M."""

    m = len(coefficients)
    n = len(coefficients[0]) if coefficients else 0

    slack_surplus_count = 0
    artificial_count = 0

    for relation in relations:
        if relation == "<=":
            slack_surplus_count += 1
        elif relation == ">=":
            slack_surplus_count += 1
            artificial_count += 1
        else:
            artificial_count += 1

    extended_labels = default_variable_labels(n)
    extended_labels.extend(f"variabila_compensare_{index + 1}" for index in range(slack_surplus_count))
    extended_labels.extend(f"variabila_penalizare_{index + 1}" for index in range(artificial_count))

    for row in coefficients:
        row.extend([0.0] * (slack_surplus_count + artificial_count))

    slack_index = n
    artificial_index = n + slack_surplus_count
    initial_basis: list[int] = []

    for i, relation in enumerate(relations):
        if relation == "<=":
            coefficients[i][slack_index] = 1.0
            initial_basis.append(slack_index)
            slack_index += 1
        elif relation == ">=":
            coefficients[i][slack_index] = -1.0
            slack_index += 1
            coefficients[i][artificial_index] = 1.0
            initial_basis.append(artificial_index)
            artificial_index += 1
        else:
            coefficients[i][artificial_index] = 1.0
            initial_basis.append(artificial_index)
            artificial_index += 1

    extended_objective = clone_vector(objective)
    extended_objective.extend([0.0] * slack_surplus_count)

    big_m_abs = compute_big_m(objective, coefficients, rhs)
    big_m = -big_m_abs if optimization == "max" else big_m_abs
    extended_objective.extend([big_m] * artificial_count)

    return (
        coefficients,
        rhs,
        extended_objective,
        initial_basis,
        slack_surplus_count,
        artificial_count,
        big_m_abs,
        extended_labels,
    )


# -----------------------------------------------------------------------------
# Teste simple pentru algoritm
# -----------------------------------------------------------------------------

def has_pivot_row(coefficients: list[list[float]], column_index: int) -> bool:
    return any(is_positive(coefficients[i][column_index]) for i in range(len(coefficients)))



def has_unbounded_optimum(
    delta: list[float],
    coefficients: list[list[float]],
    basis: list[int],
    optimization: OptimizationType,
) -> bool:
    for j in range(len(coefficients[0])):
        if j in basis:
            continue
        if optimization == "min":
            if is_negative(delta[j]) and not has_pivot_row(coefficients, j):
                return True
        else:
            if is_positive(delta[j]) and not has_pivot_row(coefficients, j):
                return True
    return False



def analyze_multiple_solutions(
    basis: list[int],
    delta: list[float],
    coefficients: list[list[float]],
) -> tuple[list[int], list[int]]:
    multiple_bfs_candidates: list[int] = []
    infinite_family_candidates: list[int] = []

    for j in range(len(delta)):
        if j in basis:
            continue
        if nearly_zero(delta[j]):
            if has_pivot_row(coefficients, j):
                multiple_bfs_candidates.append(j)
            else:
                infinite_family_candidates.append(j)

    return multiple_bfs_candidates, infinite_family_candidates



def choose_entering_variable(
    delta: list[float],
    basis: list[int],
    optimization: OptimizationType,
) -> int | None:
    candidate: int | None = None

    for j in range(len(delta)):
        if j in basis:
            continue

        if optimization != "min":
            if is_positive(delta[j]):
                if candidate is None or delta[j] > delta[candidate] + EPS or (
                    are_equal(delta[j], delta[candidate]) and j < candidate
                ):
                    candidate = j
        else:
            if is_negative(delta[j]):
                if candidate is None or delta[j] < delta[candidate] - EPS or (
                    are_equal(delta[j], delta[candidate]) and j < candidate
                ):
                    candidate = j

    return candidate



def lexicographic_key(
    coefficients: list[list[float]],
    xb: list[float],
    row_index: int,
    pivot_column: int,
    basis: list[int],
) -> tuple[float, ...]:
    pivot = coefficients[row_index][pivot_column]
    key = [xb[row_index] / pivot]
    for k in range(len(coefficients[0])):
        key.append(coefficients[row_index][k] / pivot)
    key.append(float(basis[row_index]))
    return tuple(round(value, 12) for value in key)



def choose_leaving_row(
    coefficients: list[list[float]],
    xb: list[float],
    pivot_column: int,
    basis: list[int],
) -> int | None:
    candidates: list[tuple[int, float]] = []

    for i in range(len(xb)):
        if is_positive(coefficients[i][pivot_column]) and xb[i] >= -EPS:
            ratio = xb[i] / coefficients[i][pivot_column]
            candidates.append((i, sanitize_number(ratio)))

    if not candidates:
        return None

    minimum_ratio = min(ratio for _, ratio in candidates)
    tied_rows = [row for row, ratio in candidates if are_equal(ratio, minimum_ratio)]

    if len(tied_rows) == 1:
        return tied_rows[0]

    best_row = tied_rows[0]
    best_key = lexicographic_key(coefficients, xb, best_row, pivot_column, basis)

    for row in tied_rows[1:]:
        candidate_key = lexicographic_key(coefficients, xb, row, pivot_column, basis)
        if candidate_key < best_key:
            best_row = row
            best_key = candidate_key

    return best_row



def is_optimal(delta: list[float], basis: list[int], optimization: OptimizationType) -> bool:
    for j in range(len(delta)):
        if j in basis:
            continue
        if optimization != "min":
            if is_positive(delta[j]):
                return False
        else:
            if is_negative(delta[j]):
                return False
    return True


# -----------------------------------------------------------------------------
# Calcule simplex
# -----------------------------------------------------------------------------

def compute_z_delta(
    coefficients: list[list[float]],
    cb: list[float],
    objective: list[float],
) -> tuple[list[float], list[float]]:
    total_variables = len(coefficients[0])
    z = [0.0] * total_variables
    delta = [0.0] * total_variables

    for j in range(total_variables):
        value = 0.0
        for i in range(len(coefficients)):
            value += cb[i] * coefficients[i][j]
        z[j] = sanitize_number(value)
        delta[j] = sanitize_number(objective[j] - z[j])

    return z, delta



def compute_objective_value(cb: list[float], xb: list[float]) -> float:
    value = 0.0
    for i in range(len(xb)):
        value += cb[i] * xb[i]
    return sanitize_number(value)



def pivot(
    coefficients: list[list[float]],
    xb: list[float],
    basis: list[int],
    cb: list[float],
    objective: list[float],
    pivot_row: int,
    pivot_column: int,
) -> float:
    pivot_value = coefficients[pivot_row][pivot_column]
    total_variables = len(coefficients[0])
    m = len(coefficients)

    for j in range(total_variables):
        coefficients[pivot_row][j] = sanitize_number(coefficients[pivot_row][j] / pivot_value)
    xb[pivot_row] = sanitize_number(xb[pivot_row] / pivot_value)

    for i in range(m):
        if i == pivot_row:
            continue
        factor = coefficients[i][pivot_column]
        if nearly_zero(factor):
            coefficients[i][pivot_column] = 0.0
            continue
        for j in range(total_variables):
            coefficients[i][j] = sanitize_number(coefficients[i][j] - factor * coefficients[pivot_row][j])
        xb[i] = sanitize_number(xb[i] - factor * xb[pivot_row])
        coefficients[i][pivot_column] = 0.0

    coefficients[pivot_row][pivot_column] = 1.0
    basis[pivot_row] = pivot_column
    cb[pivot_row] = objective[pivot_column]
    return sanitize_number(pivot_value)


# -----------------------------------------------------------------------------
# Formatare / extragere rezultate
# -----------------------------------------------------------------------------

def build_solution_vector(n_variables: int, basis: list[int], xb: list[float]) -> list[float]:
    solution = [0.0] * n_variables
    for j in range(n_variables):
        if j in basis:
            position = basis.index(j)
            solution[j] = sanitize_number(xb[position])
    return solution



def has_positive_artificial_basic_variable(
    basis: list[int],
    xb: list[float],
    total_variables: int,
    artificial_count: int,
) -> bool:
    if artificial_count == 0:
        return False

    threshold = total_variables - artificial_count
    for i in range(len(xb)):
        if basis[i] >= threshold and xb[i] > EPS:
            return True
    return False



def verify_solution(
    n_variables: int,
    basis: list[int],
    xb: list[float],
    original_objective: list[float],
    normalized_rhs: list[float],
    standardized_matrix: list[list[float]],
    objective_value: float,
    normalized_relations: list[Relation],
) -> VerificationReport:
    solution = build_solution_vector(n_variables, basis, xb)
    objective_from_solution = sanitize_number(
        sum(original_objective[j] * solution[j] for j in range(n_variables))
    )
    objective_matches = are_equal(objective_from_solution, objective_value)

    basis_submatrix: list[list[float]] = []
    reconstructed_rhs: list[float] = []
    for i in range(len(standardized_matrix)):
        basis_row = []
        value = 0.0
        for j in range(len(basis)):
            coeff = sanitize_number(standardized_matrix[i][basis[j]])
            basis_row.append(coeff)
            value += coeff * xb[j]
        basis_submatrix.append(basis_row)
        reconstructed_rhs.append(sanitize_number(value))

    rhs_matches = all(are_equal(normalized_rhs[i], reconstructed_rhs[i]) for i in range(len(normalized_rhs)))

    constraint_checks: list[ConstraintCheck] = []
    for i in range(len(standardized_matrix)):
        lhs = 0.0
        for j in range(n_variables):
            lhs += standardized_matrix[i][j] * solution[j]
        lhs = sanitize_number(lhs)

        relation = normalized_relations[i]
        rhs_value = normalized_rhs[i]
        if relation == "<=":
            ok = lhs <= rhs_value + EPS
        elif relation == ">=":
            ok = lhs >= rhs_value - EPS
        else:
            ok = are_equal(lhs, rhs_value)

        constraint_checks.append(
            ConstraintCheck(index=i, lhs=lhs, relation=relation, rhs=rhs_value, ok=ok)
        )

    return VerificationReport(
        objective_from_solution=objective_from_solution,
        objective_matches=objective_matches,
        reconstructed_rhs=reconstructed_rhs,
        rhs_matches=rhs_matches,
        normalized_rhs=clone_vector(normalized_rhs),
        basis_submatrix=basis_submatrix,
        constraint_checks=constraint_checks,
    )



def build_iteration_snapshot(
    index: int,
    coefficients: list[list[float]],
    basis: list[int],
    cb: list[float],
    xb: list[float],
    z: list[float],
    delta: list[float],
    objective_value: float,
    message: str,
    pivot_row: int | None = None,
    pivot_col: int | None = None,
) -> IterationSnapshot:
    return IterationSnapshot(
        index=index,
        tableau=clone_matrix(coefficients),
        basis=clone_vector(basis),
        cb=clone_vector(cb),
        xb=clone_vector(xb),
        z=clone_vector(z),
        delta=clone_vector(delta),
        objective_value=objective_value,
        pivot_row=pivot_row,
        pivot_col=pivot_col,
        message=message,
    )



def enumerate_alternate_optimal_solutions(
    n_variables: int,
    coefficients: list[list[float]],
    basis: list[int],
    cb: list[float],
    xb: list[float],
    objective: list[float],
    zero_delta_candidates: list[int],
) -> list[AlternateSolution]:
    alternatives: list[AlternateSolution] = []
    seen: set[tuple[float, ...]] = set()

    for entering in zero_delta_candidates:
        a2 = clone_matrix(coefficients)
        b2 = clone_vector(basis)
        cb2 = clone_vector(cb)
        xb2 = clone_vector(xb)

        leaving = choose_leaving_row(a2, xb2, entering, b2)
        if leaving is None:
            continue

        pivot(a2, xb2, b2, cb2, objective, leaving, entering)
        solution = build_solution_vector(n_variables, b2, xb2)
        signature = tuple(round(value, 8) for value in solution)
        if signature in seen:
            continue
        seen.add(signature)

        alternatives.append(
            AlternateSolution(
                entering_variable=entering,
                leaving_row=leaving,
                basis=clone_vector(b2),
                solution=solution,
                objective_value=compute_objective_value(cb2, xb2),
            )
        )

    return alternatives


# -----------------------------------------------------------------------------
# Solver principal
# -----------------------------------------------------------------------------

def solve_lp(problem: LPProblem) -> SolveResult:
    problem.validate()

    result = SolveResult(status="running", status_message="Solver pornit.")
    log = result.logs.append

    optimization = problem.optimization
    n_variables = problem.n_variables
    n_constraints = problem.n_constraints

    coefficients = clone_matrix(problem.constraints)
    rhs = clone_vector(problem.rhs)
    relations = list(problem.relations)
    objective = clone_vector(problem.objective)

    original_objective = clone_vector(objective)

    log(f"Problema '{problem.name}' a fost incarcata.")
    log(f"Optimizare: {optimization}. Variabile: {n_variables}. Restrictii: {n_constraints}.")

    normalization_changed = normalize_constraints(coefficients, rhs, relations)
    result.normalized_problem_changed = normalization_changed
    if normalization_changed:
        log("Au fost normalizate restrictiile cu termen liber negativ.")
    else:
        log("Nu a fost necesara normalizarea restrictiilor.")

    normalized_rhs = clone_vector(rhs)
    normalized_relations = list(relations)

    basis: list[int] = []
    variable_labels = default_variable_labels(n_variables)
    slack_surplus_count = 0
    artificial_count = 0
    big_m_abs = 0.0

    already_standard = all(relation == "==" for relation in relations)
    if already_standard:
        basis = find_identity_basis(coefficients, n_constraints, n_variables)

    if already_standard and len(basis) == n_constraints:
        result.already_standard = True
        log("Problema este deja in forma standard si are baza initiala unitate.")
    else:
        (
            coefficients,
            rhs,
            objective,
            basis,
            slack_surplus_count,
            artificial_count,
            big_m_abs,
            variable_labels,
        ) = standardize_problem(coefficients, rhs, objective, relations, optimization)
        log(
            "Problema a fost standardizata: "
            f"{slack_surplus_count} variabile de compensare, "
            f"{artificial_count} variabile de penalizare, |M| = {format_number(big_m_abs)}."
        )

    result.variable_labels = variable_labels
    result.added_slack_surplus = slack_surplus_count
    result.added_artificial = artificial_count
    result.big_m_abs = big_m_abs
    result.standardized_variable_count = len(coefficients[0]) if coefficients else 0

    standardized_matrix = clone_matrix(coefficients)

    if len(basis) != n_constraints:
        result.status = "invalid_basis"
        result.status_message = (
            "Nu s-a putut construi o baza initiala admisibila pentru simplex primal."
        )
        log(result.status_message)
        return result

    cb = [objective[column] for column in basis]
    xb = [sanitize_number(value) for value in rhs]

    z, delta = compute_z_delta(coefficients, cb, objective)
    current_objective = compute_objective_value(cb, xb)

    result.iterations.append(
        build_iteration_snapshot(
            index=0,
            coefficients=coefficients,
            basis=basis,
            cb=cb,
            xb=xb,
            z=z,
            delta=delta,
            objective_value=current_objective,
            message="Baza initiala.",
        )
    )
    log(f"Iteratia 0: valoare obiectiv = {format_number(current_objective)}.")

    if has_unbounded_optimum(delta, coefficients, basis, optimization):
        result.status = "unbounded"
        result.status_message = "Problema are optim infinit pentru baza initiala curenta."
        log(result.status_message)
        return result

    iteration_index = 0

    while True:
        if is_optimal(delta, basis, optimization):
            if has_positive_artificial_basic_variable(
                basis,
                xb,
                len(coefficients[0]),
                artificial_count,
            ):
                result.status = "infeasible"
                result.status_message = (
                    "Problema nu are solutie fezabila: o variabila artificiala a ramas strict pozitiva in baza."
                )
                log(result.status_message)
                return result

            final_objective = compute_objective_value(cb, xb)
            final_solution = build_solution_vector(n_variables, basis, xb)
            verification = verify_solution(
                n_variables=n_variables,
                basis=basis,
                xb=xb,
                original_objective=original_objective,
                normalized_rhs=normalized_rhs,
                standardized_matrix=standardized_matrix,
                objective_value=final_objective,
                normalized_relations=normalized_relations,
            )
            multiple_bfs_candidates, infinite_family_candidates = analyze_multiple_solutions(
                basis,
                delta,
                coefficients,
            )
            alternate_optima = enumerate_alternate_optimal_solutions(
                n_variables=n_variables,
                coefficients=coefficients,
                basis=basis,
                cb=cb,
                xb=xb,
                objective=objective,
                zero_delta_candidates=multiple_bfs_candidates,
            )

            result.objective_value = final_objective
            result.solution = final_solution
            result.final_basis = clone_vector(basis)
            result.final_xb = clone_vector(xb)
            result.verification = verification
            result.multiple_optima_detected = bool(alternate_optima)
            result.infinite_optimal_family_detected = bool(infinite_family_candidates)
            result.alternate_optimal_solutions = alternate_optima

            if result.infinite_optimal_family_detected:
                result.status = "optimal_infinite_family"
                result.status_message = (
                    "S-a gasit o solutie optima, iar problema admite o familie infinita de solutii optime."
                )
            elif result.multiple_optima_detected:
                result.status = "optimal_multiple"
                result.status_message = (
                    "S-a gasit o solutie optima, iar problema admite si alte solutii optime de baza."
                )
            else:
                result.status = "optimal"
                result.status_message = "S-a gasit solutia optima." 

            log(result.status_message)
            return result

        entering = choose_entering_variable(delta, basis, optimization)
        if entering is None:
            result.status = "stopped"
            result.status_message = (
                "Solverul s-a oprit fara sa poata alege o variabila de intrare in baza."
            )
            log(result.status_message)
            return result

        leaving = choose_leaving_row(coefficients, xb, entering, basis)
        if leaving is None:
            result.status = "unbounded"
            result.status_message = (
                "Nu exista variabila valida pentru iesire din baza. Problema are optim infinit."
            )
            log(result.status_message)
            return result

        previous_basic = basis[leaving]
        pivot_value = pivot(
            coefficients=coefficients,
            xb=xb,
            basis=basis,
            cb=cb,
            objective=objective,
            pivot_row=leaving,
            pivot_column=entering,
        )

        iteration_index += 1
        z, delta = compute_z_delta(coefficients, cb, objective)
        current_objective = compute_objective_value(cb, xb)

        result.iterations.append(
            build_iteration_snapshot(
                index=iteration_index,
                coefficients=coefficients,
                basis=basis,
                cb=cb,
                xb=xb,
                z=z,
                delta=delta,
                objective_value=current_objective,
                pivot_row=leaving,
                pivot_col=entering,
                message=(
                    f"Pivot pe randul {leaving + 1}, coloana {entering + 1}. "
                    f"Valoare pivot = {format_number(pivot_value)}. "
                    f"Intra a{entering + 1}, iese a{previous_basic + 1}."
                ),
            )
        )

        log(
            f"Iteratia {iteration_index}: intra a{entering + 1}, "
            f"iese a{previous_basic + 1}, pivot = {format_number(pivot_value)}, "
            f"valoare obiectiv = {format_number(current_objective)}."
        )

        if has_unbounded_optimum(delta, coefficients, basis, optimization):
            result.status = "unbounded"
            result.status_message = "Problema are optim infinit pentru starea curenta."
            log(result.status_message)
            return result
