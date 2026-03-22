# Simplex primal cu CustomTkinter

Proiectul separa clar:
- `simplex_gui/models.py` - modelele de date
- `simplex_gui/solver.py` - logica simplex si Big-M
- `simplex_gui/presets.py` - exemple rapide
- `simplex_gui/ui.py` - interfata grafica
- `app.py` - punctul de intrare

## Pornire

```bash
pip install -r requirements.txt
python app.py
```

## Ce poate face

- editare grafica a functiei obiectiv si a restrictiilor
- alegere `max` / `min`
- salvare / incarcare problema in JSON
- exemple predefinite
- rezolvare completa cu pasii solverului
- afisarea iteratiilor, bazei, vectorilor `z` si `delta`
- afisarea unei verificari finale a solutiei
- export raport text

## Idei de extindere

1. Adauga export in PDF sau CSV pornind din `build_full_report()`.
2. Introdu suport pentru denumiri custom de variabile in `LPProblem`.
3. Adauga rulare in thread separat daca vrei probleme mai mari.
4. Inlocuieste editorul curent cu un tabel dedicat daca vrei UX mai avansat.
