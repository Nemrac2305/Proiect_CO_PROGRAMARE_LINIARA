from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .models import LPProblem, SolveResult
from .numeric import format_number, parse_number
from .presets import PRESET_PROBLEMS
from .solver import solve_lp

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

MONO_FONT = ("Courier New", 12)
STATUS_COLORS = {
    "not_started": ("gray40", "gray70"),
    "running": ("#1565C0", "#90CAF9"),
    "optimal": ("#2E7D32", "#81C784"),
    "optimal_multiple": ("#2E7D32", "#81C784"),
    "optimal_infinite_family": ("#2E7D32", "#81C784"),
    "unbounded": ("#E65100", "#FFB74D"),
    "infeasible": ("#C62828", "#EF9A9A"),
    "invalid_basis": ("#C62828", "#EF9A9A"),
    "stopped": ("#6D4C41", "#BCAAA4"),
}


class ValidationError(ValueError):
    def __init__(self, message: str, widgets: list[ctk.CTkEntry] | None = None):
        super().__init__(message)
        self.widgets = widgets or []


# -----------------------------------------------------------------------------
# Formatare text pentru UI / export
# -----------------------------------------------------------------------------


def build_solution_string(solution: list[float]) -> str:
    if not solution:
        return "-"
    return ", ".join(f"x{i + 1} = {format_number(value)}" for i, value in enumerate(solution))



def format_problem(problem: LPProblem) -> str:
    lines = [
        f"Nume: {problem.name}",
        f"Optimizare: {problem.optimization}",
        f"Numar variabile: {problem.n_variables}",
        f"Numar restrictii: {problem.n_constraints}",
        "",
        "Functia obiectiv:",
        "  " + " + ".join(f"{format_number(c)} * x{i + 1}" for i, c in enumerate(problem.objective)),
        "",
        "Restrictii:",
    ]
    for i, row in enumerate(problem.constraints):
        lhs = " + ".join(f"{format_number(value)} * x{j + 1}" for j, value in enumerate(row))
        lines.append(
            f"  R{i + 1}: {lhs} {problem.relations[i]} {format_number(problem.rhs[i])}"
        )
    lines.append("")
    lines.append("Presupunere: x_j >= 0 pentru toate variabilele principale.")
    return "\n".join(lines)



def format_console_float(value: float | None, precision: int = 2) -> str:
    if value is None:
        return "-"
    return str(round(float(value), precision))



def format_console_coeff(value: float) -> str:
    return format_number(value, prefer_fraction=False)



def format_console_matrix_row(row: list[float]) -> str:
    values: list[str] = []
    for value in row:
        numeric = float(value)
        if abs(numeric - round(numeric)) <= 1e-9:
            values.append(str(int(round(numeric))))
        else:
            values.append(format_console_float(numeric, 2))
    return "[" + ", ".join(values) + "]"



def build_didactic_solution_line(solution: list[float]) -> str:
    parts = [f"x{i + 1} = {format_console_float(value, 2)}" for i, value in enumerate(solution)]
    return "    pentru valorile optimale:  x = (" + ", ".join(parts) + ")"



def build_nonnegativity_verification(result: SolveResult) -> list[str]:
    eps = 1e-9
    values_text = ", ".join(
        f"x{i + 1} = {format_console_float(value, 2)}"
        for i, value in enumerate(result.solution)
    )
    ok = all(value >= -eps for value in result.solution)

    return [
        "Verificarea Nenegativitatii (Admisibilitatea)",
        "",
        "Se verifica daca toate variabilele din solutia finala respecta conditia de nenegativitate:",
        "   pentru orice xj din x optim  ==>  xj >= 0",
        "",
        "In cazul nostru:",
        f"   {values_text}    ==> {'Verificat' if ok else 'Neverificat'}",
        "",
    ]


def build_objective_verification_line(problem: LPProblem, result: SolveResult) -> str:
    report = result.verification
    if report is None:
        return ""

    terms = []
    for i, coeff in enumerate(problem.objective):
        term = f"{format_console_coeff(coeff)} x x{i + 1}"
        if i > 0:
            term = "+ " + term
        terms.append(term)

    status = "Ok." if report.objective_matches else "Nu se verifica."
    z_index = max(0, len(result.iterations) - 1)
    return (
        "f(x) = "
        + " ".join(terms)
        + f" = {format_console_float(report.objective_from_solution, 2)}"
        + f" {'==' if report.objective_matches else '???'} Z[{z_index}]"
        + ("" if report.objective_matches else f" (= {format_console_float(result.objective_value, 2)})")
        + f" --> {status}"
    )



def format_verification(problem: LPProblem, result: SolveResult) -> str:
    report = result.verification
    if report is None:
        return "Nu exista verificare disponibila."

    lines = ["Verificari solutie", ""]
    lines.extend(build_nonnegativity_verification(result))
    lines.append("Verificare optim functie obiectiv de valorile optimale ale variabilelor:")
    lines.append(build_objective_verification_line(problem, result))
    lines.append("")
    lines.append("Verificare matrice S x vector XB final = b1 == b:")

    for i, row in enumerate(report.basis_submatrix):
        matrix_row = format_console_matrix_row(row)
        xb_value = result.final_xb[i] if i < len(result.final_xb) else 0.0
        reconstructed = report.reconstructed_rhs[i] if i < len(report.reconstructed_rhs) else 0.0
        rhs_value = report.normalized_rhs[i] if i < len(report.normalized_rhs) else 0.0
        lines.append(
            f"{matrix_row}   {format_console_float(xb_value, 2)}   "
            f"{format_console_float(reconstructed, 2)}     {format_console_float(rhs_value, 2)}"
        )

    if report.rhs_matches:
        lines.append("--> Ok. (S x XB = b1 == b)")
    else:
        lines.append("--> Nu se verifica (S x XB = b1 != b)")

    lines.append("")
    lines.append("Verificare restrictii pentru valorile optimale ale variabilelor:")
    for check in report.constraint_checks:
        if abs(check.lhs - check.rhs) <= 1e-9:
            relation_symbol = "=="
        elif check.lhs < check.rhs:
            relation_symbol = "<"
        else:
            relation_symbol = ">"

        status = "Ok." if check.ok else "Restrictia nu se verifica"
        lines.append(
            f"   {format_console_float(check.lhs, 2)} {relation_symbol} "
            f"{format_console_float(check.rhs, 2)} --> {status}"
        )

    return "\n".join(lines)



def format_iteration(snapshot, variable_labels: list[str]) -> str:
    labels = [f"a{i + 1}" for i in range(len(snapshot.delta))]
    width = 12

    lines: list[str] = [
        f"Iteratia {snapshot.index}",
        "=" * 72,
        snapshot.message or "",
        "",
        f"Valoare obiectiv: {format_number(snapshot.objective_value)}",
        "",
        "Baza curenta:",
    ]

    for i, basis_index in enumerate(snapshot.basis):
        basis_label = labels[basis_index] if basis_index < len(labels) else f"v{basis_index + 1}"
        lines.append(
            f"  linia {i + 1}: {basis_label:<6} | CB = {format_number(snapshot.cb[i]):>8} | "
            f"XB = {format_number(snapshot.xb[i]):>8}"
        )

    lines.append("")
    lines.append("Matricea A:")
    header = " " * 10 + " ".join(f"{label:>{width}}" for label in labels)
    lines.append(header)
    for i, row in enumerate(snapshot.tableau):
        body = " ".join(f"{format_number(value):>{width}}" for value in row)
        lines.append(f"R{i + 1:<2}      {body}")

    lines.append("")
    lines.append("Vector z:")
    lines.append("  " + " ".join(f"{format_number(value):>{width}}" for value in snapshot.z))
    lines.append("Vector delta:")
    lines.append("  " + " ".join(f"{format_number(value):>{width}}" for value in snapshot.delta))

    if snapshot.pivot_row is not None and snapshot.pivot_col is not None:
        pivot_label = labels[snapshot.pivot_col] if snapshot.pivot_col < len(labels) else f"v{snapshot.pivot_col + 1}"
        lines.append("")
        lines.append(
            f"Pivot selectat: rand {snapshot.pivot_row + 1}, coloana {snapshot.pivot_col + 1} ({pivot_label})"
        )

    return "\n".join(lines)



def format_result_generic(result: SolveResult) -> str:
    lines = [
        "Rezumat solver",
        "============",
        "",
        f"Status: {result.status}",
        f"Mesaj: {result.status_message}",
        f"Valoare obiectiv: {format_number(result.objective_value)}",
        f"Solutie principala: {build_solution_string(result.solution)}",
        "",
        "Meta-date solver:",
        f"  Variabile totale dupa standardizare: {result.standardized_variable_count}",
        f"  Variabile de compensare adaugate: {result.added_slack_surplus}",
        f"  Variabile de penalizare adaugate: {result.added_artificial}",
        f"  |M| folosit: {format_number(result.big_m_abs) if result.big_m_abs else '0'}",
        f"  Normalizare b < 0 aplicata: {'da' if result.normalized_problem_changed else 'nu'}",
        f"  Problema era deja standarda: {'da' if result.already_standard else 'nu'}",
        "",
        f"Baza finala: {', '.join(result.variable_labels[index] for index in result.final_basis) if result.final_basis else '-'}",
    ]
    return "\n".join(lines)



def format_result(problem: LPProblem, result: SolveResult) -> str:
    if result.status not in {"optimal", "optimal_multiple", "optimal_infinite_family"}:
        return format_result_generic(result)

    objective_tag = "fmax" if problem.optimization == "max" else "fmin"
    z_index = max(0, len(result.iterations) - 1)
    lines = [
        f"==> Optim gasit pentru functia obiectiv:  {objective_tag}(x) == Z[{z_index}] = {format_console_float(result.objective_value, 2)}",
        build_didactic_solution_line(result.solution),
        "",
        "",
        format_verification(problem, result),
        "",
    ]

    if result.status == "optimal_infinite_family":
        lines.append("Obs: Exista o familie infinita de solutii optime")
    elif result.status == "optimal_multiple":
        count = len(result.alternate_optimal_solutions)
        lines.append(f"Obs: Solutii multiple PLS (delta == 0 pt. inca {count} variabile non-baza)")
        lines.append("")
        lines.append("Alte solutii optime de baza:")
        for idx, alternative in enumerate(result.alternate_optimal_solutions, start=1):
            solution_text = ", ".join(
                f"x{i + 1} = {format_console_float(value, 2)}"
                for i, value in enumerate(alternative.solution)
            )
            lines.append(
                f"   {idx}. x = ({solution_text}) | Z = {format_console_float(alternative.objective_value, 2)}"
            )
    else:
        lines.append("Obs: Solutie unica (nu exista solutii multiple)")

    lines.extend(["", "------------------------------------------------------", "", "Terminare program"])
    return "\n".join(lines)



def build_full_report(problem: LPProblem, result: SolveResult) -> str:
    sections = [
        "Aplicatie simplex primal - raport",
        "=" * 32,
        "",
        format_problem(problem),
        "",
        format_result(problem, result),
        "",
        "Log solver",
        "==========",
        *result.logs,
    ]
    return "\n".join(sections)


# -----------------------------------------------------------------------------
# Widget-uri reutilizabile
# -----------------------------------------------------------------------------

def remember_default_border(widget: ctk.CTkEntry) -> None:
    widget._default_border_color = widget.cget("border_color")  # type: ignore[attr-defined]



def reset_border(widget: ctk.CTkEntry) -> None:
    color = getattr(widget, "_default_border_color", None)
    if color is not None:
        widget.configure(border_color=color)



def mark_invalid(widget: ctk.CTkEntry) -> None:
    widget.configure(border_color=("#D32F2F", "#EF9A9A"))


class ObjectiveEditor(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, orientation="horizontal", height=130, **kwargs)
        self.variable_count = 0
        self.entries: list[ctk.CTkEntry] = []

    def set_variable_count(self, variable_count: int) -> None:
        self.variable_count = variable_count
        for child in self.winfo_children():
            child.destroy()
        self.entries.clear()

        if variable_count <= 0:
            return

        for j in range(variable_count):
            label = ctk.CTkLabel(self, text=f"x{j + 1}")
            label.grid(row=0, column=j, padx=(10, 6), pady=(10, 4))

            entry = ctk.CTkEntry(self, width=90, justify="center")
            entry.grid(row=1, column=j, padx=(10, 6), pady=(0, 12))
            entry.insert(0, "0")
            remember_default_border(entry)
            self.entries.append(entry)

    def get_entry_widgets(self) -> list[ctk.CTkEntry]:
        return list(self.entries)

    def set_values(self, values: list[float]) -> None:
        self.set_variable_count(len(values))
        for entry, value in zip(self.entries, values):
            entry.delete(0, tk.END)
            entry.insert(0, format_number(value))

    def fill_with_zeros(self) -> None:
        for entry in self.entries:
            entry.delete(0, tk.END)
            entry.insert(0, "0")


class ConstraintsEditor(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, height=420, **kwargs)
        self.constraint_count = 0
        self.variable_count = 0
        self.coefficient_entries: list[list[ctk.CTkEntry]] = []
        self.relation_menus: list[ctk.CTkOptionMenu] = []
        self.rhs_entries: list[ctk.CTkEntry] = []

    def set_dimensions(self, constraint_count: int, variable_count: int) -> None:
        self.constraint_count = constraint_count
        self.variable_count = variable_count

        for child in self.winfo_children():
            child.destroy()

        self.coefficient_entries.clear()
        self.relation_menus.clear()
        self.rhs_entries.clear()

        if constraint_count <= 0 or variable_count <= 0:
            return

        ctk.CTkLabel(self, text="Restr.").grid(row=0, column=0, padx=8, pady=(10, 6), sticky="w")
        for j in range(variable_count):
            ctk.CTkLabel(self, text=f"x{j + 1}").grid(
                row=0,
                column=j + 1,
                padx=6,
                pady=(10, 6),
            )
        ctk.CTkLabel(self, text="Rel.").grid(
            row=0,
            column=variable_count + 1,
            padx=6,
            pady=(10, 6),
        )
        ctk.CTkLabel(self, text="b").grid(
            row=0,
            column=variable_count + 2,
            padx=6,
            pady=(10, 6),
        )

        for i in range(constraint_count):
            ctk.CTkLabel(self, text=f"R{i + 1}").grid(
                row=i + 1,
                column=0,
                padx=8,
                pady=6,
                sticky="w",
            )

            row_entries: list[ctk.CTkEntry] = []
            for j in range(variable_count):
                entry = ctk.CTkEntry(self, width=84, justify="center")
                entry.grid(row=i + 1, column=j + 1, padx=6, pady=6)
                entry.insert(0, "0")
                remember_default_border(entry)
                row_entries.append(entry)

            relation_menu = ctk.CTkOptionMenu(self, values=["<=", ">=", "=="], width=90)
            relation_menu.grid(row=i + 1, column=variable_count + 1, padx=6, pady=6)
            relation_menu.set("<=")

            rhs_entry = ctk.CTkEntry(self, width=84, justify="center")
            rhs_entry.grid(row=i + 1, column=variable_count + 2, padx=6, pady=6)
            rhs_entry.insert(0, "0")
            remember_default_border(rhs_entry)

            self.coefficient_entries.append(row_entries)
            self.relation_menus.append(relation_menu)
            self.rhs_entries.append(rhs_entry)

    def get_entry_widgets(self) -> list[ctk.CTkEntry]:
        widgets: list[ctk.CTkEntry] = []
        for row in self.coefficient_entries:
            widgets.extend(row)
        widgets.extend(self.rhs_entries)
        return widgets

    def set_data(self, constraints: list[list[float]], relations: list[str], rhs: list[float]) -> None:
        self.set_dimensions(len(constraints), len(constraints[0]) if constraints else 0)
        for i, row in enumerate(constraints):
            for j, value in enumerate(row):
                entry = self.coefficient_entries[i][j]
                entry.delete(0, tk.END)
                entry.insert(0, format_number(value))
            self.relation_menus[i].set(relations[i])
            self.rhs_entries[i].delete(0, tk.END)
            self.rhs_entries[i].insert(0, format_number(rhs[i]))

    def fill_with_zeros(self) -> None:
        for row in self.coefficient_entries:
            for entry in row:
                entry.delete(0, tk.END)
                entry.insert(0, "0")
        for menu in self.relation_menus:
            menu.set("<=")
        for rhs_entry in self.rhs_entries:
            rhs_entry.delete(0, tk.END)
            rhs_entry.insert(0, "0")


# -----------------------------------------------------------------------------
# Aplicatia principala
# -----------------------------------------------------------------------------
class SimplexApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Simplex primal - CustomTkinter")
        self.geometry("1440x900")
        self.minsize(1180, 760)

        self.current_result: SolveResult | None = None
        self.current_problem: LPProblem | None = None
        self.current_iteration_index = 0

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

        self.n_vars_entry.insert(0, "2")
        self.n_constraints_entry.insert(0, "2")
        remember_default_border(self.n_vars_entry)
        remember_default_border(self.n_constraints_entry)

        self.generate_tables(silent=True)
        self.preset_menu.set(next(iter(PRESET_PROBLEMS.keys())))
        self.load_selected_preset(show_message=False)

    # ------------------------------------------------------------------
    # Constructie UI
    # ------------------------------------------------------------------
    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(99, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="Simplex UI",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(24, 8), sticky="w")

        ctk.CTkLabel(
            sidebar,
            text="Solver tabelar, refactorizat pentru extensii.",
            justify="left",
            wraplength=250,
        ).grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        ctk.CTkLabel(sidebar, text="Aspect").grid(row=2, column=0, padx=20, pady=(0, 6), sticky="w")
        self.appearance_menu = ctk.CTkOptionMenu(
            sidebar,
            values=["System", "Light", "Dark"],
            command=ctk.set_appearance_mode,
        )
        self.appearance_menu.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="ew")
        self.appearance_menu.set("System")

        ctk.CTkLabel(sidebar, text="Tip optimizare").grid(row=4, column=0, padx=20, pady=(0, 6), sticky="w")
        self.optimization_selector = ctk.CTkSegmentedButton(sidebar, values=["max", "min"])
        self.optimization_selector.grid(row=5, column=0, padx=20, pady=(0, 18), sticky="ew")
        self.optimization_selector.set("max")

        ctk.CTkLabel(sidebar, text="Numar variabile").grid(row=6, column=0, padx=20, pady=(0, 6), sticky="w")
        self.n_vars_entry = ctk.CTkEntry(sidebar)
        self.n_vars_entry.grid(row=7, column=0, padx=20, pady=(0, 12), sticky="ew")

        ctk.CTkLabel(sidebar, text="Numar restrictii").grid(row=8, column=0, padx=20, pady=(0, 6), sticky="w")
        self.n_constraints_entry = ctk.CTkEntry(sidebar)
        self.n_constraints_entry.grid(row=9, column=0, padx=20, pady=(0, 12), sticky="ew")

        ctk.CTkButton(
            sidebar,
            text="Genereaza tabele",
            command=self.generate_tables,
        ).grid(row=10, column=0, padx=20, pady=(0, 18), sticky="ew")

        ctk.CTkLabel(sidebar, text="Exemple rapide").grid(row=11, column=0, padx=20, pady=(0, 6), sticky="w")
        self.preset_menu = ctk.CTkOptionMenu(sidebar, values=list(PRESET_PROBLEMS.keys()))
        self.preset_menu.grid(row=12, column=0, padx=20, pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            sidebar,
            text="Incarca exemplu",
            command=self.load_selected_preset,
        ).grid(row=13, column=0, padx=20, pady=(0, 18), sticky="ew")

        ctk.CTkButton(sidebar, text="Rezolva", command=self.solve_current_problem).grid(
            row=14, column=0, padx=20, pady=(0, 8), sticky="ew"
        )
        ctk.CTkButton(sidebar, text="Reseteaza", command=self.reset_problem).grid(
            row=15, column=0, padx=20, pady=(0, 18), sticky="ew"
        )

        ctk.CTkButton(sidebar, text="Salveaza problema", command=self.save_problem).grid(
            row=16, column=0, padx=20, pady=(0, 8), sticky="ew"
        )
        ctk.CTkButton(sidebar, text="Incarca problema", command=self.load_problem).grid(
            row=17, column=0, padx=20, pady=(0, 8), sticky="ew"
        )
        ctk.CTkButton(sidebar, text="Exporta raport", command=self.export_report).grid(
            row=18, column=0, padx=20, pady=(0, 18), sticky="ew"
        )

        ctk.CTkLabel(
            sidebar,
            text="Nota: aplicatia presupune xj >= 0 pentru toate variabilele principale.",
            wraplength=250,
            justify="left",
        ).grid(row=19, column=0, padx=20, pady=(0, 20), sticky="w")

    def _build_main_area(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        summary = ctk.CTkFrame(container)
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        summary.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            summary,
            text="Status",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, padx=(20, 10), pady=(16, 4), sticky="w")
        self.status_value_label = ctk.CTkLabel(summary, text="gata de lucru")
        self.status_value_label.grid(row=0, column=1, padx=(0, 20), pady=(16, 4), sticky="w")

        ctk.CTkLabel(
            summary,
            text="Valoare obiectiv",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=1, column=0, padx=(20, 10), pady=4, sticky="w")
        self.objective_value_label = ctk.CTkLabel(summary, text="-")
        self.objective_value_label.grid(row=1, column=1, padx=(0, 20), pady=4, sticky="w")

        ctk.CTkLabel(
            summary,
            text="Solutie",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=2, column=0, padx=(20, 10), pady=(4, 16), sticky="nw")
        self.solution_value_label = ctk.CTkLabel(summary, text="-", justify="left", wraplength=900)
        self.solution_value_label.grid(row=2, column=1, padx=(0, 20), pady=(4, 16), sticky="w")

        self.tabview = ctk.CTkTabview(container)
        self.tabview.grid(row=1, column=0, sticky="nsew")
        self.problem_tab = self.tabview.add("Problema")
        self.result_tab = self.tabview.add("Rezultat")
        self.iteration_tab = self.tabview.add("Iteratii")
        self.log_tab = self.tabview.add("Log")

        self._build_problem_tab()
        self._build_result_tab()
        self._build_iteration_tab()
        self._build_log_tab()

    def _build_problem_tab(self) -> None:
        self.problem_tab.grid_rowconfigure(1, weight=1)
        self.problem_tab.grid_columnconfigure(0, weight=1)

        objective_card = ctk.CTkFrame(self.problem_tab)
        objective_card.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        objective_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            objective_card,
            text="Functia obiectiv",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")
        ctk.CTkLabel(
            objective_card,
            text="Editeaza coeficientii lui x1..xn.",
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")
        self.objective_editor = ObjectiveEditor(objective_card, fg_color="transparent")
        self.objective_editor.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

        constraints_card = ctk.CTkFrame(self.problem_tab)
        constraints_card.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8, 16))
        constraints_card.grid_rowconfigure(2, weight=1)
        constraints_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            constraints_card,
            text="Restrictii",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")
        ctk.CTkLabel(
            constraints_card,
            text="Fiecare linie contine coeficientii, relatia si termenul liber b.",
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")
        self.constraints_editor = ConstraintsEditor(constraints_card)
        self.constraints_editor.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def _build_result_tab(self) -> None:
        self.result_tab.grid_rowconfigure(0, weight=1)
        self.result_tab.grid_columnconfigure(0, weight=1)
        self.result_textbox = ctk.CTkTextbox(self.result_tab, wrap="none", font=MONO_FONT)
        self.result_textbox.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        self._set_textbox_content(self.result_textbox, "Rezultatul va aparea aici.")

    def _build_iteration_tab(self) -> None:
        self.iteration_tab.grid_rowconfigure(1, weight=1)
        self.iteration_tab.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(self.iteration_tab)
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        toolbar.grid_columnconfigure(3, weight=1)

        self.prev_iteration_button = ctk.CTkButton(toolbar, text="<", width=40, command=self.show_previous_iteration)
        self.prev_iteration_button.grid(row=0, column=0, padx=(12, 6), pady=12)

        self.next_iteration_button = ctk.CTkButton(toolbar, text=">", width=40, command=self.show_next_iteration)
        self.next_iteration_button.grid(row=0, column=1, padx=6, pady=12)

        self.iteration_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["Fara iteratii"],
            command=lambda _: self.on_iteration_selected(),
        )
        self.iteration_menu.grid(row=0, column=2, padx=6, pady=12, sticky="w")
        self.iteration_menu.set("Fara iteratii")

        self.iteration_count_label = ctk.CTkLabel(toolbar, text="0 / 0")
        self.iteration_count_label.grid(row=0, column=3, padx=(12, 16), pady=12, sticky="e")

        self.iteration_textbox = ctk.CTkTextbox(self.iteration_tab, wrap="none", font=MONO_FONT)
        self.iteration_textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8, 16))
        self._set_textbox_content(self.iteration_textbox, "Ruleaza solverul pentru a vedea iteratiile.")

    def _build_log_tab(self) -> None:
        self.log_tab.grid_rowconfigure(0, weight=1)
        self.log_tab.grid_columnconfigure(0, weight=1)
        self.log_textbox = ctk.CTkTextbox(self.log_tab, wrap="word", font=MONO_FONT)
        self.log_textbox.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        self._set_textbox_content(self.log_textbox, "Logul solverului va aparea aici.")

    # ------------------------------------------------------------------
    # Utilitare UI
    # ------------------------------------------------------------------
    def _set_textbox_content(self, textbox: ctk.CTkTextbox, text: str) -> None:
        textbox.configure(state="normal")
        textbox.delete("1.0", tk.END)
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")

    def _reset_all_borders(self) -> None:
        for widget in [self.n_vars_entry, self.n_constraints_entry]:
            reset_border(widget)
        for widget in self.objective_editor.get_entry_widgets():
            reset_border(widget)
        for widget in self.constraints_editor.get_entry_widgets():
            reset_border(widget)

    def _update_summary(self, result: SolveResult | None) -> None:
        if result is None:
            self.status_value_label.configure(text="gata de lucru", text_color=STATUS_COLORS["not_started"])
            self.objective_value_label.configure(text="-")
            self.solution_value_label.configure(text="-")
            return

        status_color = STATUS_COLORS.get(result.status, STATUS_COLORS["not_started"])
        self.status_value_label.configure(text=result.status_message or result.status, text_color=status_color)
        self.objective_value_label.configure(text=format_number(result.objective_value))
        self.solution_value_label.configure(text=build_solution_string(result.solution))

    # ------------------------------------------------------------------
    # Parsare si validare input
    # ------------------------------------------------------------------
    def _parse_positive_int(self, entry: ctk.CTkEntry, field_name: str) -> int:
        raw = entry.get().strip()
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValidationError(f"{field_name} trebuie sa fie un numar intreg pozitiv.", [entry]) from exc
        if value <= 0:
            raise ValidationError(f"{field_name} trebuie sa fie strict pozitiv.", [entry])
        return value

    def _parse_float_entry(self, entry: ctk.CTkEntry, field_name: str) -> float:
        raw = entry.get().strip()
        try:
            value = parse_number(raw)
        except ValueError as exc:
            raise ValidationError(
                f"{field_name} trebuie sa fie numeric (exemple valide: 2, -1.5, 1/3).",
                [entry],
            ) from exc
        return value

    def _validate_dimensions_are_synced(self, n_vars: int, n_constraints: int) -> None:
        if self.objective_editor.variable_count != n_vars or self.constraints_editor.constraint_count != n_constraints:
            raise ValidationError(
                "Ai schimbat numarul de variabile sau restrictii. Apasa 'Genereaza tabele' inainte de rezolvare.",
                [self.n_vars_entry, self.n_constraints_entry],
            )

    def collect_problem_from_ui(self) -> LPProblem:
        self._reset_all_borders()

        n_vars = self._parse_positive_int(self.n_vars_entry, "Numarul de variabile")
        n_constraints = self._parse_positive_int(self.n_constraints_entry, "Numarul de restrictii")
        self._validate_dimensions_are_synced(n_vars, n_constraints)

        objective: list[float] = []
        for index, entry in enumerate(self.objective_editor.entries, start=1):
            objective.append(self._parse_float_entry(entry, f"Coeficientul functiei obiectiv x{index}"))

        constraints: list[list[float]] = []
        rhs: list[float] = []
        relations: list[str] = []

        for i in range(n_constraints):
            row_values: list[float] = []
            for j in range(n_vars):
                entry = self.constraints_editor.coefficient_entries[i][j]
                row_values.append(self._parse_float_entry(entry, f"Coeficientul A[{i + 1}][{j + 1}]"))
            rhs_entry = self.constraints_editor.rhs_entries[i]
            rhs_value = self._parse_float_entry(rhs_entry, f"Termenul liber b[{i + 1}]")
            relation = self.constraints_editor.relation_menus[i].get()

            constraints.append(row_values)
            rhs.append(rhs_value)
            relations.append(relation)

        problem = LPProblem(
            name="Problema editata in UI",
            optimization=self.optimization_selector.get(),
            objective=objective,
            constraints=constraints,
            rhs=rhs,
            relations=relations,
        )
        problem.validate()
        return problem

    # ------------------------------------------------------------------
    # Actiuni principale
    # ------------------------------------------------------------------
    def generate_tables(self, silent: bool = False) -> None:
        self._reset_all_borders()
        try:
            n_vars = self._parse_positive_int(self.n_vars_entry, "Numarul de variabile")
            n_constraints = self._parse_positive_int(self.n_constraints_entry, "Numarul de restrictii")
        except ValidationError as exc:
            for widget in exc.widgets:
                mark_invalid(widget)
            if not silent:
                messagebox.showerror("Date invalide", str(exc))
            return

        self.objective_editor.set_variable_count(n_vars)
        self.constraints_editor.set_dimensions(n_constraints, n_vars)
        self.current_problem = None
        self.current_result = None
        self.current_iteration_index = 0
        self._update_summary(None)
        self._set_textbox_content(self.result_textbox, "Rezultatul va aparea aici.")
        self._set_textbox_content(self.iteration_textbox, "Ruleaza solverul pentru a vedea iteratiile.")
        self._set_textbox_content(self.log_textbox, "Logul solverului va aparea aici.")
        self.iteration_menu.configure(values=["Fara iteratii"])
        self.iteration_menu.set("Fara iteratii")
        self.iteration_count_label.configure(text="0 / 0")

        if not silent:
            messagebox.showinfo("Tabele regenerate", "Editorul a fost actualizat pentru noile dimensiuni.")

    def load_selected_preset(self, show_message: bool = True) -> None:
        problem = PRESET_PROBLEMS[self.preset_menu.get()]
        self.apply_problem(problem)
        if show_message:
            messagebox.showinfo("Exemplu incarcat", f"A fost incarcat exemplul: {problem.name}")

    def apply_problem(self, problem: LPProblem) -> None:
        self.n_vars_entry.delete(0, tk.END)
        self.n_vars_entry.insert(0, str(problem.n_variables))
        self.n_constraints_entry.delete(0, tk.END)
        self.n_constraints_entry.insert(0, str(problem.n_constraints))
        self.optimization_selector.set(problem.optimization)
        self.generate_tables(silent=True)
        self.objective_editor.set_values(problem.objective)
        self.constraints_editor.set_data(problem.constraints, problem.relations, problem.rhs)
        self.current_problem = None
        self.current_result = None
        self._update_summary(None)

    def reset_problem(self) -> None:
        self.generate_tables(silent=True)
        self.objective_editor.fill_with_zeros()
        self.constraints_editor.fill_with_zeros()
        self.optimization_selector.set("max")
        self.current_problem = None
        self.current_result = None
        self._update_summary(None)

    def solve_current_problem(self) -> None:
        try:
            problem = self.collect_problem_from_ui()
        except ValidationError as exc:
            for widget in exc.widgets:
                mark_invalid(widget)
            messagebox.showerror("Date invalide", str(exc))
            return
        except ValueError as exc:
            messagebox.showerror("Date invalide", str(exc))
            return

        self.current_problem = problem
        self.current_result = solve_lp(problem)
        self.current_iteration_index = 0

        self._update_summary(self.current_result)
        self._set_textbox_content(self.result_textbox, format_result(self.current_problem, self.current_result))
        self._set_textbox_content(self.log_textbox, "\n".join(self.current_result.logs) or "Fara log.")
        self._refresh_iteration_selector()

        self.tabview.set("Rezultat")

    def save_problem(self) -> None:
        try:
            problem = self.collect_problem_from_ui()
        except ValidationError as exc:
            for widget in exc.widgets:
                mark_invalid(widget)
            messagebox.showerror("Date invalide", str(exc))
            return
        except ValueError as exc:
            messagebox.showerror("Date invalide", str(exc))
            return

        path = filedialog.asksaveasfilename(
            title="Salveaza problema",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="problema_simplex.json",
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8") as handle:
            json.dump(problem.to_dict(), handle, indent=2, ensure_ascii=False)

        messagebox.showinfo("Salvare reusita", f"Problema a fost salvata in:\n{path}")

    def load_problem(self) -> None:
        path = filedialog.askopenfilename(
            title="Incarca problema",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            problem = LPProblem.from_dict(data)
        except Exception as exc:  # noqa: BLE001 - mesaj prietenos pentru utilizator
            messagebox.showerror("Fisier invalid", f"Nu am putut citi problema:\n{exc}")
            return

        self.apply_problem(problem)
        messagebox.showinfo("Problema incarcata", f"A fost incarcata problema din:\n{path}")

    def export_report(self) -> None:
        if self.current_problem is None or self.current_result is None:
            messagebox.showinfo("Nimic de exportat", "Rezolva mai intai o problema.")
            return

        path = filedialog.asksaveasfilename(
            title="Exporta raport",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt")],
            initialfile="raport_simplex.txt",
        )
        if not path:
            return

        report_text = build_full_report(self.current_problem, self.current_result)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(report_text)

        messagebox.showinfo("Raport exportat", f"Raportul a fost salvat in:\n{path}")

    # ------------------------------------------------------------------
    # Iteratii
    # ------------------------------------------------------------------
    def _refresh_iteration_selector(self) -> None:
        if self.current_result is None or not self.current_result.iterations:
            self.iteration_menu.configure(values=["Fara iteratii"])
            self.iteration_menu.set("Fara iteratii")
            self.iteration_count_label.configure(text="0 / 0")
            self._set_textbox_content(self.iteration_textbox, "Nu exista iteratii de afisat.")
            return

        values = [f"Iteratia {snapshot.index}" for snapshot in self.current_result.iterations]
        self.iteration_menu.configure(values=values)
        self.current_iteration_index = 0
        self.iteration_menu.set(values[0])
        self._show_iteration_by_index(0)

    def _show_iteration_by_index(self, index: int) -> None:
        if self.current_result is None or not self.current_result.iterations:
            return

        index = max(0, min(index, len(self.current_result.iterations) - 1))
        self.current_iteration_index = index
        snapshot = self.current_result.iterations[index]
        self.iteration_menu.set(f"Iteratia {snapshot.index}")
        self.iteration_count_label.configure(text=f"{index + 1} / {len(self.current_result.iterations)}")
        self._set_textbox_content(
            self.iteration_textbox,
            format_iteration(snapshot, self.current_result.variable_labels),
        )

    def on_iteration_selected(self) -> None:
        if self.current_result is None or not self.current_result.iterations:
            return
        label = self.iteration_menu.get()
        try:
            index = int(label.split()[-1])
        except ValueError:
            return

        for position, snapshot in enumerate(self.current_result.iterations):
            if snapshot.index == index:
                self._show_iteration_by_index(position)
                return

    def show_previous_iteration(self) -> None:
        if self.current_result is None:
            return
        self._show_iteration_by_index(self.current_iteration_index - 1)

    def show_next_iteration(self) -> None:
        if self.current_result is None:
            return
        self._show_iteration_by_index(self.current_iteration_index + 1)



def main() -> None:
    app = SimplexApp()
    app.mainloop()
