EPS = 1e-9
MAX_ITER = 100

def este_zero(x, eps=EPS):
    return abs(x) <= eps

def egal(x, y, eps=EPS):
    return abs(x - y) <= eps

def este_pozitiv(x, eps=EPS):
    return x > eps

def este_negativ(x, eps=EPS):
    return x < -eps

def afisare_valoare_float(v, precizie):
    print(round(v, precizie), end='')

def afisare_vector_float(V, precizie):
    n = len(V)
    if n == 0:
        return
    print("[", end='')
    for i in range(n):
        print(round(V[i], precizie), end='')
        if i < n - 1:
            print(", ", end='')
        else:
            print("]")

def copie_vector(V):
    copie_V = []
    for i in range(len(V)):
        copie_V.append(V[i])
    return copie_V

def copie_matrice(M):
    copie_M = []
    for i in range(len(M)):
        line = []
        for j in range(len(M[0])):
            line.append(M[i][j])
        copie_M.append(line)
    return copie_M

def curata_numeric_vector(V, eps=EPS):
    for i in range(len(V)):
        if este_zero(V[i], eps):
            V[i] = 0.0

def curata_numeric_matrice(M, eps=EPS):
    for i in range(len(M)):
        for j in range(len(M[0])):
            if este_zero(M[i][j], eps):
                M[i][j] = 0.0

def inverseaza_restrictie(tip):
    if tip == 1:
        return 2
    if tip == 2:
        return 1
    return 3

def normalizeaza_restrictii(A, b, tip_restrictie):
    for i in range(len(b)):
        if este_negativ(b[i]):
            b[i] = -b[i]
            for j in range(len(A[0])):
                A[i][j] = -A[i][j]
            tip_restrictie[i] = inverseaza_restrictie(tip_restrictie[i])

def solutie_infinit_pe_coloana(A, jj):
    for i in range(len(A)):
        if este_pozitiv(A[i][jj]):
            return False
    return True

def solutii_multiple(B, delta):
    ms_list = []
    for j in range(len(delta)):
        if j not in B and este_zero(delta[j]):
            ms_list.append(j)
    return ms_list

def prezentare_solutie(n, m, Z, B, XB, opt="max"):
    print()
    print()
    print("Obs: Solutia PL == solutia PLS pentru variabilele principale")
    print("------------------------------------------------------------")
    print()

    for i in range(m):
        if B[i] < n and este_zero(XB[i]):
            print("OBS: Solutie degenerata (exista componente bazice nule) !!!")
            print("(criteriul de iesire din baza a implicat metoda perturbatiilor)")
            print()
            break

    k = len(Z) - 1

    if opt != "min":
        print(f"==> Optim gasit pentru functia obiectiv:  fmax(x) == Z[{k}] = {round(Z[k], 10)}")
    else:
        print(f"==> Optim gasit pentru functia obiectiv:  fmin(x) == Z[{k}] = {round(Z[k], 10)}")

    print("    pentru valorile optimale:  x = (", end='')

    for j in range(n):
        if j in B:
            for i in range(m):
                if B[i] == j:
                    print(f"x{j + 1} = ", end='')
                    afisare_valoare_float(XB[i], 6)
                    if j < n - 1:
                        print(", ", end='')
                    else:
                        print(")")
                    break
        else:
            if j < n - 1:
                print(f"x{j + 1} = 0.0", end=", ")
            else:
                print(f"x{j + 1} = 0.0)")

    print()

def verificare_solutie(n, m, Z, B, CB, XB, c, b, S, opt, tip_restrictie):
    print()
    print("Verificari solutie")
    print()

    k = len(Z) - 1

    val = 0.0
    for i in range(m):
        if B[i] < n:
            val = val + c[B[i]] * XB[i]

    val = round(val, 10)

    print("Verificare optim functie obiectiv de valorile optimale ale variabilelor:")
    print("f(x) = ", end='')
    for i in range(n):
        if i > 0:
            print("+ ", end='')
        print(f"{c[i]} x x{i + 1} ", end='')
    print(f"= {val}", end='')

    if egal(Z[k], val):
        print(f" == Z[{k}] --> Ok.")
    else:
        print(f" ??? Z[{k}] (= {Z[k]}) --> Nu se verifica.")

    print()
    print("Verificare matrice S x vector XB final = b1 == b:")

    b1 = []
    for i in range(m):
        val = 0.0
        for j in range(m):
            val = val + S[i][B[j]] * XB[j]
        b1.append(round(val, 10))

    for i in range(m):
        print("[", end='')
        for j in range(m):
            print(f"{round(S[i][B[j]], 6)}", end='')
            if j < m - 1:
                print(", ", end='')
            else:
                print("]   ", end='')
        afisare_valoare_float(XB[i], 6)
        print("   ", end='')
        print(round(b1[i], 6), end="     ")
        print(round(b[i], 6))

    ok = True
    for i in range(m):
        if not egal(b[i], b1[i]):
            ok = False
            break

    if not ok:
        print("--> Nu se verifica (S x XB = b1 != b)")
    else:
        print("--> Ok. (S x XB = b1 == b)")

    print()
    print("Verificare restrictii pentru valorile optimale ale variabilelor:")

    for i in range(m):
        val = 0.0
        for j in range(n):
            for k2 in range(m):
                if B[k2] == j:
                    val = val + S[i][j] * XB[k2]
                    break

        val = round(val, 10)

        if val < b[i] - EPS:
            print(f"   {val} < {b[i]}", end='')
            if tip_restrictie[i] == 1:
                print(" --> Ok.")
            else:
                print(" --> Restrictia nu se verifica")
        elif egal(val, b[i]):
            print(f"   {val} == {b[i]} --> Ok.")
        else:
            print(f"   {val} > {b[i]}", end='')
            if tip_restrictie[i] == 2:
                print(" --> Ok.")
            else:
                print(" --> Restrictia nu se verifica")

def idx_var_in(delta, B, opt="max"):
    jj = None

    if opt != "min":
        maxim = None
        for j in range(len(delta)):
            if j in B:
                continue
            if este_pozitiv(delta[j]):
                if maxim is None or delta[j] > maxim + EPS:
                    maxim = delta[j]
                    jj = j
    else:
        minim = None
        for j in range(len(delta)):
            if j in B:
                continue
            if este_negativ(delta[j]):
                if minim is None or delta[j] < minim - EPS:
                    minim = delta[j]
                    jj = j

    return jj

def idx_var_out(A, XB, jj):
    candidati = []

    for i in range(len(XB)):
        if este_pozitiv(A[i][jj]) and XB[i] >= -EPS:
            raport = max(XB[i], 0.0) / A[i][jj]
            candidati.append((raport, i))

    if len(candidati) == 0:
        return None

    minim = min(x[0] for x in candidati)

    linii_minime = []
    for raport, i in candidati:
        if egal(raport, minim):
            linii_minime.append(i)

    if len(linii_minime) == 1:
        return linii_minime[0]

    ii = linii_minime[0]

    for i in linii_minime[1:]:
        for k in range(len(A[0])):
            v_i = A[i][k] / A[i][jj]
            v_ii = A[ii][k] / A[ii][jj]

            if v_i < v_ii - EPS:
                ii = i
                break
            elif v_i > v_ii + EPS:
                break

    return ii

def TO(delta, B, opt="max"):
    if opt != "min":
        for j in range(len(delta)):
            if j not in B and este_pozitiv(delta[j]):
                return False
    else:
        for j in range(len(delta)):
            if j not in B and este_negativ(delta[j]):
                return False

    return True

def baza_canonica_existenta(A):
    m = len(A)
    n = len(A[0])
    B = []
    folosita = []

    for i in range(m):
        gasit = False
        for j in range(n):
            if j in folosita:
                continue
            if egal(A[i][j], 1.0):
                ok = True
                for k in range(m):
                    if k != i and not este_zero(A[k][j]):
                        ok = False
                        break
                if ok:
                    B.append(j)
                    folosita.append(j)
                    gasit = True
                    break

        if not gasit:
            return []

    return B

def main():
    print()
    print("----------------------------------------------------------")
    print("Rezolvare problema de PL cu ASP")
    print("pentru variabile care satisfac conditia de non-negativitate")
    print("----------------------------------------------------------")
    print()

    print("Definire problema de PL (introducere date)")
    print("-------------------------------------------")
    print()

    opt = input("Tip de optimizare functie obiectiv? [1=max/0=min]: opt = ")
    if opt[0] == '1':
        opt = "max"
    else:
        opt = "min"
    print()

    n = int(input("Numar variabile functie obiectiv?: n = "))
    print()

    c = []

    print("Coeficienti variabile functie obiectiv PL")
    for j in range(n):
        c.append(float(input(f"   coef. lui x{j + 1}?:  c{j + 1} = ")))

    print()
    m = int(input("Numar restrictii PL?: m = "))
    print()

    A = []
    b = []
    tip_restrictie = []

    print("Tipurile restrictiilor")
    for i in range(m):
        tip_restrictie.append(int(input(f"   tip restrictie #{i + 1}? [1:\"<=\"/2:\">=\"/3:\"==\"]: ")))

    for i in range(m):
        print(f"Coeficienti si valoare limita restrictie #{i + 1}")
        line = []
        for j in range(n):
            line.append(float(input(f"   coef. lui x{j + 1}?:  A[{i + 1}][{j + 1}] = ")))
        A.append(line)
        b.append(float(input(f"    val. limita?:  b{i + 1} = ")))

    normalizeaza_restrictii(A, b, tip_restrictie)

    toate_egale = True
    for i in range(m):
        if tip_restrictie[i] != 3:
            toate_egale = False
            break

    n1 = 0
    n2 = 0
    B = []

    if toate_egale:
        B = baza_canonica_existenta(A)

    print()
    if len(B) == m:
        print("Problema este una standard (PL == PLS)")
        print("--------------------------------------")
        print()
    else:
        print("Trecere la forma standard (PL --> PLS)")
        print("--------------------------------------")
        print()

        for i in range(m):
            if tip_restrictie[i] == 1:
                n1 = n1 + 1
            elif tip_restrictie[i] == 2:
                n1 = n1 + 1
                n2 = n2 + 1
            else:
                n2 = n2 + 1

        print(f"==> Numar variabile suplimentare:  n1 = {n1},  n2 = {n2}")
        print()

        for i in range(m):
            for _ in range(n1 + n2):
                A[i].append(0.0)

        idx_slack = 0
        idx_art = 0
        B = []

        for i in range(m):
            if tip_restrictie[i] == 1:
                col_slack = n + idx_slack
                A[i][col_slack] = 1.0
                B.append(col_slack)
                idx_slack += 1

            elif tip_restrictie[i] == 2:
                col_slack = n + idx_slack
                A[i][col_slack] = -1.0
                idx_slack += 1

                col_art = n + n1 + idx_art
                A[i][col_art] = 1.0
                B.append(col_art)
                idx_art += 1

            else:
                col_art = n + n1 + idx_art
                A[i][col_art] = 1.0
                B.append(col_art)
                idx_art += 1

        for _ in range(n1):
            c.append(0.0)

        if opt != "min":
            M = -1000.0
        else:
            M = 1000.0

        for _ in range(n2):
            c.append(M)

    print(f"Coeficientii c: {c}")
    print()

    S = copie_matrice(A)

    k = 0

    print("Start Algoritm Simplex Primal (ASP)")
    print()
    print(f"* Iteratia {k}:")
    print()
    print("Componentele initiale ale Tabelului Simplex (TS)")
    print()

    CB = []
    XB = []
    for i in range(m):
        CB.append(c[B[i]])
        XB.append(b[i])

    curata_numeric_vector(XB)

    print("Vectorii B, CB si XB:")
    for i in range(m):
        print(f"a{B[i] + 1}", end="   ")
        print(CB[i], end="   ")
        print(round(XB[i], 10))

    print()
    print("Matricea A si vectorul b:")
    for i in range(m):
        print(A[i], end='   ')
        print(b[i])

    total_var = len(A[0])
    z = []
    delta = []

    for j in range(total_var):
        val = 0.0
        for i in range(m):
            val = val + CB[i] * A[i][j]

        val = round(val, 10)

        z.append(val)
        delta.append(c[j] - val)

    curata_numeric_vector(z)
    curata_numeric_vector(delta)

    print()
    print(f"Vectorii z si delta, iteratia {k}:")
    print("z = ", end='')
    afisare_vector_float(z, 6)
    print("delta = ", end='')
    afisare_vector_float(delta, 6)

    Z = []

    val = 0.0
    for i in range(m):
        val = val + CB[i] * XB[i]

    val = round(val, 10)
    Z.append(val)

    print()
    print(f"Valoare optima la iteratia curenta ({k}):")
    print(f"==> Z[{k}] = {Z[k]}")

    sol_multiple = False

    gata = TO(delta, B, opt)

    if gata:
        print()
        print(f"* Test optimalitate ==> \"True\" ==> Iteratia {k}: STOP")
        print()
        print("------------------------------------------------------")

        if n2 > 0:
            i = 0
            while i < m:
                if B[i] >= len(A[0]) - n2 and not este_zero(XB[i]):
                    break
                i = i + 1
            if i < m:
                print()
                print("Obs: Criteriu inexistenta solutie (variabila de penalizare PLS != 0)")
                print("==> Problema de optimizare PL nu are solutie")
                print()
                print("Terminare program")
                print()
                return

        prezentare_solutie(n, m, Z, B, XB, opt)
        verificare_solutie(n, m, Z, B, CB, XB, c, b, S, opt, tip_restrictie)

        if not sol_multiple:
            ms_list = solutii_multiple(B, delta)
            print()
            if len(ms_list) > 0:
                print(f"Obs: Solutii multiple PLS (delta == 0 pt. inca {len(ms_list)} variabile non-baza)")
                k1 = 0
                sol_multiple = True
                gata = False

                B1 = copie_vector(B)
                CB1 = copie_vector(CB)
                XB1 = copie_vector(XB)
                A1 = copie_matrice(A)
            else:
                print("Obs: Solutie unica (nu exista solutii multiple)")

        print()
        print("------------------------------------------------------")
    else:
        print()
        print(f"* Test optimalitate ==> \"False\" ==> Inca o iteratie")
        print()
        print("------------------------------------------------------")

    while not gata:
        if k >= MAX_ITER:
            print()
            print(f"Obs: S-a atins limita maxima de iteratii ({MAX_ITER}).")
            print("==> Oprire de siguranta (blocaj numeric / ciclu posibil).")
            print()
            print("Terminare program")
            print()
            return

        k = k + 1

        print()
        print(f"* Iteratia {k}:")
        print()
        print("Aplicare criterii identificare indecsi variabile de i/o baza B")

        if not sol_multiple:
            jj = idx_var_in(delta, B, opt)
        else:
            jj = ms_list[k1]

            if k1 > 0:
                B = copie_vector(B1)
                CB = copie_vector(CB1)
                XB = copie_vector(XB1)
                A = copie_matrice(A1)

        if jj is None:
            print()
            print("Obs: Nu s-a putut identifica o variabila valida de intrare in baza.")
            print("==> Oprire (blocaj numeric).")
            print()
            print("Terminare program")
            print()
            return

        if solutie_infinit_pe_coloana(A, jj):
            print()
            print("Obs: Criteriu de optim infinit verificat pe coloana pivot aleasa.")
            print("==> Problema de optimizare PL are solutie optim infinit")
            print()
            print("Terminare program")
            print()
            return

        ii = idx_var_out(A, XB, jj)

        if ii is None:
            print()
            print("Obs: Nu exista linie valida pentru testul raportului minim.")
            print("==> Problema de optimizare PL are solutie optim infinit")
            print()
            print("Terminare program")
            print()
            return

        p = A[ii][jj]

        print()
        print(f"==> Pivot = A[{ii}][{jj}] = ", end='')
        afisare_valoare_float(p, 6)
        print()

        if este_zero(p):
            print()
            print("Obs: Pivot nul sau prea mic numeric.")
            print("==> Oprire (blocaj numeric).")
            print()
            print("Terminare program")
            print()
            return

        B[ii] = jj
        CB[ii] = c[jj]

        xb_pivot_vechi = XB[ii]

        for i in range(m):
            if i != ii:
                XB[i] = XB[i] * p - xb_pivot_vechi * A[i][jj]
        for i in range(m):
            XB[i] = XB[i] / p

        for i in range(m):
            if i != ii:
                for j in range(total_var):
                    if j != jj:
                        A[i][j] = A[i][j] * p - A[ii][j] * A[i][jj]
        for i in range(m):
            if i != ii:
                for j in range(total_var):
                    if j != jj:
                        A[i][j] = A[i][j] / p

        for j in range(total_var):
            A[ii][j] = A[ii][j] / p

        for i in range(m):
            if i != ii:
                A[i][jj] = 0.0

        curata_numeric_vector(XB)
        curata_numeric_matrice(A)

        for j in range(total_var):
            val = 0.0
            for i in range(m):
                val = val + CB[i] * A[i][j]

            val = round(val, 10)

            z[j] = val
            delta[j] = c[j] - z[j]

        curata_numeric_vector(z)
        curata_numeric_vector(delta)

        print()
        print("Componentele Tabelului Simplex (TS) actualizat")
        print()
        print("Vectorii B, CB si XB:")
        for i in range(m):
            print(f"a{B[i] + 1}", end="   ")
            print(CB[i], end="   ")
            afisare_valoare_float(XB[i], 6)
            print()

        print()
        print("Matricea A:")
        for i in range(m):
            afisare_vector_float(A[i], 6)

        print()
        print(f"Vectorii z si delta, iteratia {k}:")
        print("z = ", end='')
        afisare_vector_float(z, 6)
        print("delta = ", end='')
        afisare_vector_float(delta, 6)

        val = 0.0
        for i in range(m):
            val = val + CB[i] * XB[i]

        val = round(val, 10)
        Z.append(val)

        print()
        print(f"Valoare optima la iteratia curenta ({k}):")
        print(f"==> Z[{k}] = {Z[k]}")
        print()

        if opt != "min" and Z[k] > Z[k - 1] + EPS:
            print(f"(Obs: Z[{k}] = {Z[k]} > Z[{k - 1}] = {Z[k - 1]} --> Ok.)")
        elif opt == "min" and Z[k] < Z[k - 1] - EPS:
            print(f"(Obs: Z[{k}] = {Z[k]} < Z[{k - 1}] = {Z[k - 1]} --> Ok.)")
        elif sol_multiple and egal(Z[k], Z[k - 1]):
            print(f"(Obs: Z[{k}] = {Z[k]} == Z[{k - 1}] = {Z[k - 1]}) --> Ok.")
        else:
            print(f"(Obs: Z[{k}] = {Z[k]} ??? Z[{k - 1}] = {Z[k - 1]}) --> Nu s-a optimizat")

        gata = TO(delta, B, opt)

        if gata:
            print()
            print(f"* Test optimalitate ==> \"True\" ==> Iteratia {k}: STOP")
            print()
            print("------------------------------------------------------")

            if n2 > 0:
                i = 0
                while i < m:
                    if B[i] >= len(A[0]) - n2 and not este_zero(XB[i]):
                        break
                    i = i + 1
                if i < m:
                    print()
                    print("Obs: Criteriu inexistenta solutie (variabila de penalizare PLS != 0)")
                    print("==> Problema de optimizare PL nu are solutie")
                    print()
                    print("Terminare program")
                    print()
                    return

            prezentare_solutie(n, m, Z, B, XB, opt)
            verificare_solutie(n, m, Z, B, CB, XB, c, b, S, opt, tip_restrictie)

            if not sol_multiple:
                ms_list = solutii_multiple(B, delta)
                if len(ms_list) > 0:
                    print(f"Obs: Solutii multiple PLS (delta == 0 pt. inca {len(ms_list)} variabile non-baza)")
                    k1 = 0
                    sol_multiple = True
                    gata = False

                    B1 = copie_vector(B)
                    CB1 = copie_vector(CB)
                    XB1 = copie_vector(XB)
                    A1 = copie_matrice(A)
                else:
                    print("Obs: Solutie unica (nu exista solutii multiple)")
            else:
                k1 = k1 + 1
                if k1 < len(ms_list):
                    gata = False

            print()
            print("------------------------------------------------------")
        else:
            print()
            print(f"* Test optimalitate ==> \"False\" ==> Inca o iteratie")
            print()
            print("------------------------------------------------------")

    print()
    print("Terminare program")
    print()

if __name__ == "__main__":
    main()