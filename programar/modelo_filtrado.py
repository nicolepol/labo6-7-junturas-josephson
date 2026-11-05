"""Modelo nodal completo del filtrado (ambiente + criogénico), sin plegar.

Cada línea se modela por separado (no se supone simetría), así que vale
tanto con el LO de la fuente flotante como a masa, y permite incluir el par
de sensado y la impedancia de la masa de la caja.

Topología (tesis, figs. 5.4a y 5.7a):
  ambiente:   por línea, R - C a caja - R - C a caja
  criogénico: por línea, R - R - R, con dos C ENTRE líneas
  juntura:    R_J || C_J entre los extremos de las dos líneas de corriente

Excitación: fuente de corriente ideal (Keithley 6220) entre la entrada de
la línea + (HI) y la de la línea - (LO). Salida: corriente por la juntura.
"""
import numpy as np
from scipy import linalg, optimize

C_PAR = 1e-12        # capacidad parásita a masa en cada nodo [F] (regulariza)
R_FLOT = 1e10        # LO "flotante": aislación a masa [Ohm]
R_CORTO = 1e-3       # LO a masa / juntura en voltaje cero [Ohm]


class Red:
    def __init__(self):
        self.nodos = {}
        self.R = []      # (a, b, R)
        self.C = []      # (a, b, C)

    def n(self, nombre):
        if nombre == "G":
            return -1
        if nombre not in self.nodos:
            self.nodos[nombre] = len(self.nodos)
        return self.nodos[nombre]

    def r(self, a, b, R):
        self.R.append((self.n(a), self.n(b), R))

    def c(self, a, b, C):
        self.C.append((self.n(a), self.n(b), C))

    def matrices(self):
        N = len(self.nodos)
        G = np.zeros((N, N)); Cm = np.eye(N) * C_PAR
        for M, lista, val in ((G, self.R, lambda x: 1 / x), (Cm, self.C, lambda x: x)):
            for a, b, x in lista:
                y = val(x)
                M[a, a] += y
                if b >= 0:
                    M[b, b] += y; M[a, b] -= y; M[b, a] -= y
        return G, Cm


def armar(R_ta, C_ta, R_cry=22.0, C_cry=47e-9, R_J=R_CORTO, C_J=50e-12,
          lo_a_masa=False, sensado=False, R_g=0.0):
    """Devuelve (A, B, Cout) del sistema de estados. Salida = I por la juntura."""
    red = Red()
    caja = "caja" if R_g > 0 else "G"
    pares = [("p", "m")] + ([("sp", "sm")] if sensado else [])
    for a, b in pares:
        for ln in (a, b):
            red.r(f"{ln}0", f"{ln}1", R_ta); red.c(f"{ln}1", caja, C_ta)
            red.r(f"{ln}1", f"{ln}2", R_ta); red.c(f"{ln}2", caja, C_ta)
            red.r(f"{ln}2", f"{ln}3", R_cry)
            red.r(f"{ln}3", f"{ln}4", R_cry)
        red.c(f"{a}3", f"{b}3", C_cry); red.c(f"{a}4", f"{b}4", C_cry)
    # extremos: las líneas de corriente terminan en Jp/Jm; las de sensado, también
    red.r("p4", "Jp", R_cry); red.r("m4", "Jm", R_cry)
    if sensado:
        red.r("sp4", "Jp", R_cry); red.r("sm4", "Jm", R_cry)
        red.r("sp0", "sm0", 1e9)                     # nanovoltímetro (alta Z)
        red.r("sp0", "G", 2 * R_FLOT); red.r("sm0", "G", 2 * R_FLOT)   # flotante, simétrico
    red.r("Jp", "Jm", R_J); red.c("Jp", "Jm", C_J)
    if lo_a_masa:
        red.r("m0", "G", R_CORTO)
    else:   # flotante: aislación simétrica, para no acoplar el modo común
        red.r("p0", "G", 2 * R_FLOT); red.r("m0", "G", 2 * R_FLOT)
    if R_g > 0:
        red.r("caja", "G", R_g)
    G, Cm = red.matrices()
    N = len(red.nodos)
    b = np.zeros(N); b[red.nodos["p0"]] = 1.0; b[red.nodos["m0"]] = -1.0
    Cout = np.zeros(N)
    Cout[red.nodos["Jp"]] = 1 / R_J; Cout[red.nodos["Jm"]] = -1 / R_J
    A = -linalg.solve(Cm, G); B = linalg.solve(Cm, b)
    return A, B, Cout, (G, Cm, b)


def H(sis, f):
    G, Cm, b = sis[3]; Cout = sis[2]
    s = 2j * np.pi * np.atleast_1d(f)
    return np.array([Cout @ np.linalg.solve(G + x * Cm, b) for x in s])


def fc(sis, rel=1 / np.sqrt(2)):
    dc = abs(H(sis, 1e-4)[0])
    g = lambda lf: abs(H(sis, 10**lf)[0]) / dc - rel
    return 10**optimize.brentq(g, -3, 8)


def _modos(sis):
    A, B, Cout = sis[:3]
    w, V = linalg.eig(A)
    coef = -(Cout @ V) * linalg.solve(V, B) / w
    yinf = np.real(coef.sum())
    keep = (np.abs(coef) > 1e-5 * abs(yinf)) & (np.real(w) < 0)       # descarto modos no excitados (p. ej. el modo común con LO flotante)
    return w[keep], coef[keep] / yinf


def residuo(sis, t):
    w, c = _modos(sis)
    t = np.atleast_1d(t)
    return np.real((c[None, :] * np.exp(np.outer(t, w))).sum(1))


def tau_lento(sis):
    w, _ = _modos(sis)
    return -1 / np.real(w).max()


def t_punto(sis, eps=0.01):
    """Tiempo por punto de una rampa en escalera para que el error en la
    juntura sea eps*paso: sum_k r(kT) = eps."""
    w, c = _modos(sis)
    tau = -1 / np.real(w).max()
    def err(T):
        K = int(np.ceil(40 * tau / T)) + 5
        k = np.arange(1, K + 1)
        return np.real((c[None, :] * np.exp(np.outer(k * T, w))).sum(1)).sum()
    g = lambda lT: np.log(max(abs(err(10**lT)), 1e-300)) - np.log(eps)
    return 10**optimize.brentq(g, np.log10(tau) - 4, np.log10(tau) + 4)
