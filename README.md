# Proiect CO - Programare Liniară

> Implementare didactică a rezolvării problemelor de **programare liniară** prin **Algoritmul Simplex Primal**, atât în **consolă**, cât și printr-o **interfață grafică** realizată cu **CustomTkinter**.

---

## Descriere

Acest repository conține un proiect educațional dedicat studierii și implementării metodelor de rezolvare a problemelor de **programare liniară**, cu accent pe **Algoritmul Simplex Primal** și pe legătura dintre teoria matematică și transpunerea sa într-o aplicație software.

Proiectul a fost conceput astfel încât să ofere două moduri de utilizare:

- o variantă de **consolă**, potrivită pentru urmărirea directă a pașilor algoritmici;
- o variantă cu **interfață grafică**, pentru o utilizare mai accesibilă și o prezentare mai clară a rezultatelor.

Scopul principal al proiectului este unul **didactic**: evidențierea etapelor de formulare, standardizare și rezolvare a unei probleme de optimizare liniară, precum și interpretarea riguroasă a soluției obținute.

---

## Obiectivele proiectului

Acest proiect urmărește:

- formularea unei probleme de programare liniară în mod riguros;
- transformarea problemei într-o formă compatibilă cu aplicarea algoritmului simplex;
- utilizarea metodei **Big-M** pentru tratarea variabilelor artificiale;
- parcurgerea iterațiilor specifice **Algoritmului Simplex Primal**;
- afișarea și verificarea soluției finale;
- evidențierea unor situații speciale precum:
  - degenerare;
  - soluții multiple;
  - optim infinit;
  - lipsa unei soluții admisibile.

---

## Funcționalități

### Varianta în consolă
Fișierul `CO_programare_liniara.py` permite:

- introducerea interactivă a datelor problemei;
- alegerea tipului de optimizare: **maximizare** sau **minimizare**;
- definirea restricțiilor de tip `<=`, `>=` și `=`;
- standardizarea problemei;
- introducerea variabilelor de compensare și artificiale;
- aplicarea metodei **Big-M**;
- parcurgerea iterativă a pașilor algoritmului simplex;
- afișarea soluției și verificarea finală a rezultatului.

### Varianta cu interfață grafică
Aplicația din folderul `simplex_customtkinter_app` oferă:

- interfață modernă pentru introducerea funcției obiectiv și a restricțiilor;
- alegerea între probleme de tip **max** și **min**;
- salvarea și încărcarea problemelor în format **JSON**;
- utilizarea unor exemple predefinite;
- afișarea etapelor solverului;
- afișarea iterațiilor și a bazei curente;
- exportul unui raport text;
- verificarea finală a soluției.

---

## Structura proiectului

```text
Proiect_CO_PROGRAMARE_LINIARA/
├── CO_programare_liniara.py
├── CO_programare_liniara_pseudocod.txt
├── Pseudocod_Proiect_Programare_Liniara_interactiv.md
└── simplex_customtkinter_app/
    ├── app.py
    ├── requirements.txt
    ├── README.md
    └── simplex_gui/
        ├── __init__.py
        ├── models.py
        ├── numeric.py
        ├── presets.py
        ├── solver.py
        └── ui.py
