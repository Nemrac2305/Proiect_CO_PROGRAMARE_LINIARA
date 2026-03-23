PROCEDURE Main()
    // [Citire și normalizare - verificăm că putem aplica ASP (toți bi >= 0)](https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=15)
    CITESTE n, m, tip_optim, C, A, B, tip_restrictie

PENTRU i = 1 LA m EXECUTA
        DACA B[i] < 0 ATUNCI
            B[i] = -B[i]
            A[i] = -A[i]
            tip_restrictie[i] = Inverseaza(tip_restrictie[i])
        SFARSIT_DACA
SFARSIT_PENTRU

// [Standardizare (R2) și Big-M](https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=10)
    M = Valoare_Foarte_Mare   // poate fi considerata 1000
    A_standard, C_standard, Baza_Initiala = Standardizeaza(A, C, tip_restrictie, M)

// Algoritmul Simplex Primal
    GATA = FALSE

CAT TIMP GATA == FALSE EXECUTA
        // [Calcul Delta](https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=10)
        PENTRU j = 1 LA total_variabile EXECUTA
            Z[j] = SUMA(C_standard[Baza_Initiala[i]] * A_standard[i][j], pentru i = 1..m)
            Delta[j] = C_standard[j] - Z[j]
        SFARSIT_PENTRU

// Test Optimalitate
        DACA (tip_optim == "MAX" SI TOATE Delta[j] <= 0) SAU
            (tip_optim == "MIN" SI TOATE Delta[j] >= 0) ATUNCI

// Verificare Optim Multiplu
            EXISTA_OPTIM_MULTIPLU = FALSE

PENTRU j = 1 LA total_variabile EXECUTA
                DACA j NU APARTINE Baza_Initiala SI Delta[j] == 0 ATUNCI
                    EXISTA_OPTIM_MULTIPLU = TRUE
                SFARSIT_DACA
            SFARSIT_PENTRU

GATA = TRUE

DACA EXISTA_OPTIM_MULTIPLU == TRUE ATUNCI
                STARE = "OPTIM_MULTIPLU"
            ALTFEL
                STARE = "OPTIM_GASIT"
            SFARSIT_DACA

ALTFEL
            // Criteriul de intrare în bază
            DACA tip_optim == "MAX" ATUNCI
                j_pivot = Index_Maxim_Delta(Delta)
            ALTFEL
                j_pivot = Index_Minim_Delta(Delta)
            SFARSIT_DACA

// Test Optim Infinit
            DACA TOATE_ELEMENTELE_DIN_COLOANA(A_standard, j_pivot) <= 0 ATUNCI
                GATA = TRUE
                STARE = "OPTIM_INFINIT"
            ALTFEL
                // Criteriul de ieșire din bază
                // Aici se aplică [Regula lui Charnes](https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=10) în caz de egalitate a raportului
                i_pivot = Identifica_Pivot_Charnes(A_standard, B, j_pivot)

// [Regula dreptunghiului (Transformarea Gauss-Jordan)](https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=11)
                Pivotare(A_standard, B, Baza_Initiala, i_pivot, j_pivot)
            SFARSIT_DACA
        SFARSIT_DACA
    SFARSIT_CAT_TIMP

// [Verificările V1, V2, V3 și afișare](https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=7)
    DACA STARE == "OPTIM_GASIT" SAU STARE == "OPTIM_MULTIPLU" ATUNCI

// [V1: Verificarea nenegativitatii (admisibilitatea)](https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=7)
        // Se verifica conditia: Pentru orice x_j din solutia optima, x_j >= 0
        VALID_V1 = Verifica_Nenegativitate(Baza_Initiala, B)

// [V2: Verificarea valorii functiei obiectiv](https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=7)
        // Calcul f(x1, x2, x3) = 79*x1 + 84*x2 + 81*x3 si compararea cu tabelul
        f_tabel = Calcul_Z_Optim()
        f_verificat = SUMA(C_initial[j] * X_optim[j])
        VALID_V2 = (f_tabel == f_verificat)

// [V3: Verificare matriceală (legătura între I0 și Istop)](https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=7)
        // S * XB(Istop) = B(I0)
        S = Extrage_Matrice_S(A_initial, Baza_Finala)
        XB = Extrage_Coloana_Termeni_Liberi_Finala()
        VALID_V3 = (S * XB == B_Initial)

[Afiseaza_Rezultate_Validate(VALID_V1, VALID_V2, VALID_V3)](https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=5)
    SFARSIT_DACA
SF_PROCEDURE


PROCEDURE Pivotare(A, B, Baza, i_p, j_p)
    Valoare_Pivot = A[i_p][j_p]

A[i_p] = A[i_p] / Valoare_Pivot
    B[i_p] = B[i_p] / Valoare_Pivot

PENTRU i = 1 LA m EXECUTA
        DACA i != i_p ATUNCI
            Factor = A[i][j_p]

// [Recalculare prin Regula Dreptunghiului (Diagonale)]((https://www.overleaf.com/read/wnvjynzvzrgw#267030&pagenumber=10)
            // Element_Nou = (Element * Pivot - Diagonala_Secundara) / Pivot
            A[i] = A[i] - Factor * A[i_p]
            B[i] = B[i] - Factor * B[i_p]
        SFARSIT_DACA
    SFARSIT_PENTRU

Baza[i_p] = j_p
SF_PROCEDURE
