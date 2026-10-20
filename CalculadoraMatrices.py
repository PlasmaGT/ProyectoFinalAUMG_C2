from __future__ import annotations

import random
import sys
import tkinter as tk
from dataclasses import dataclass
from fractions import Fraction
from tkinter import font as tkfont
from tkinter import ttk

MATRIZ_MAX = 8
PRESETS = (3, 4, 5, 6)


# =============================================================================
# 1. TEMA Y FUENTES
# =============================================================================
class T:
    """Paleta de colores activa. `T.aplicar("claro" | "oscuro")` cambia todos los valores."""
    BG = "#F4F5F7"            # fondo de la ventana
    SUPERFICIE = "#FFFFFF"    # tarjetas y barra lateral
    BORDE = "#E4E7EC"
    TEXTO = "#101828"
    TEXTO_2 = "#667085"
    TEXTO_3 = "#98A2B3"
    ACENTO = "#2563EB"
    ACENTO_HOVER = "#1D4ED8"
    ACENTO_SUAVE = "#EBF2FF"
    HOVER = "#F2F4F7"
    HOVER_2 = "#E4E7EC"
    CAMPO = "#F9FAFB"         # fondo de las celdas de entrada
    SEGMENTO = "#EEF0F3"
    ERROR = "#D92D20"
    ERROR_SUAVE = "#FEF3F2"
    ERROR_BORDE = "#FECDCA"
    FILA = "#FFF1C2"          # fila modificada en Gauss-Jordan
    PIVOTE = "#CFE0FF"        # celda pivote
    CORCHETE = "#344054"
    SEG_ACTIVO = "#FFFFFF"    # opción activa de un selector segmentado
    ACENTO_TEXTO = "#1D4ED8"  # acento para texto sobre fondos suaves
    DESACTIVADO = "#D0D5DD"
    SCROLL = "#D0D5DD"
    SCROLL_HOVER = "#98A2B3"
    SCROLL_PRESS = "#667085"

    @classmethod
    def aplicar(cls, nombre: str) -> None:
        for clave, valor in TEMAS[nombre].items():
            setattr(cls, clave, valor)


TEMAS: dict[str, dict[str, str]] = {"claro": {k: v for k, v in vars(T).items() if k.isupper()}}
TEMAS["oscuro"] = dict(
    BG="#0E1217", SUPERFICIE="#161B22", BORDE="#2A313B",
    TEXTO="#E6EAF0", TEXTO_2="#9AA4B2", TEXTO_3="#6B7685",
    ACENTO="#3B82F6", ACENTO_HOVER="#2F6FDB", ACENTO_SUAVE="#1B2A44",
    HOVER="#1F2630", HOVER_2="#2A3340", CAMPO="#0F141A", SEGMENTO="#0E1217",
    ERROR="#F97066", ERROR_SUAVE="#2A1517", ERROR_BORDE="#5C2A2E",
    FILA="#4A3B12", PIVOTE="#1E3A6B", CORCHETE="#C5CCD6",
    SEG_ACTIVO="#2A3340", ACENTO_TEXTO="#93C5FD", DESACTIVADO="#47505C",
    SCROLL="#3A424D", SCROLL_HOVER="#566070", SCROLL_PRESS="#6B7685",
)


F: dict[str, tkfont.Font] = {}


def _elegir_familia(preferidas: tuple[str, ...], por_defecto: str) -> str:
    disponibles = set(tkfont.families())
    for nombre in preferidas:
        if nombre in disponibles:
            return nombre
    return por_defecto


def crear_fuentes() -> None:
    """Crea las fuentes usando las que existan en el sistema."""
    base = tkfont.nametofont("TkDefaultFont").actual()["family"]
    ui = _elegir_familia(("Segoe UI", "SF Pro Text", "Helvetica Neue", "Inter",
                          "Ubuntu", "Noto Sans", "DejaVu Sans"), base)
    mono = _elegir_familia(("Cascadia Mono", "Consolas", "SF Mono", "Menlo",
                            "DejaVu Sans Mono", "Liberation Mono"), "Courier")
    F.update({
        "ui": tkfont.Font(family=ui, size=10),
        "ui_b": tkfont.Font(family=ui, size=10, weight="bold"),
        "peq": tkfont.Font(family=ui, size=9),
        "peq_b": tkfont.Font(family=ui, size=9, weight="bold"),
        "seccion": tkfont.Font(family=ui, size=8, weight="bold"),
        "h1": tkfont.Font(family=ui, size=20, weight="bold"),
        "h2": tkfont.Font(family=ui, size=12, weight="bold"),
        "marca": tkfont.Font(family=ui, size=16, weight="bold"),
        "valor": tkfont.Font(family=ui, size=28, weight="bold"),
        "operador": tkfont.Font(family=ui, size=22),
        "mono": tkfont.Font(family=mono, size=11),
        "mono_b": tkfont.Font(family=mono, size=11, weight="bold"),
        "mono_g": tkfont.Font(family=mono, size=13),
        "mono_g_b": tkfont.Font(family=mono, size=13, weight="bold"),
        "mono_s": tkfont.Font(family=mono, size=10),
    })


# =============================================================================
# 2. MOTOR MATEMÁTICO
# =============================================================================
SUBINDICES = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def sub(n: int) -> str:
    """3 -> '₃' (para escribir a₁₂, x₃, F₂...)."""
    return str(n).translate(SUBINDICES)


def dim_txt(M: list[list]) -> str:
    return f"{len(M)} × {len(M[0])}"


class ErrorMatematico(Exception):
    """Error 'esperable' (dimensiones incompatibles, matriz singular, etc.)."""

    def __init__(self, titulo: str, detalle: str):
        super().__init__(titulo)
        self.titulo = titulo
        self.detalle = detalle


@dataclass
class Paso:
    """Un bloque del procedimiento (o el resultado final).

    titulo        Encabezado corto.
    texto         Explicación en lenguaje natural (se muestra antes de la matriz).
    matriz        Lista de listas con Fraction o str (las str se muestran tal cual).
    nota          Cuentas / fórmulas (se muestra después de la matriz, en monoespaciado).
    valor         Valor grande destacado (ej. el determinante).
    resaltar      Filas a resaltar.   resaltar_cols: columnas a resaltar.
    pivote        (fila, columna) de la celda pivote.
    separador     Índice de columna antes del cual se dibuja la línea de la matriz aumentada.
    """
    titulo: str
    texto: str = ""
    matriz: list | None = None
    nota: str = ""
    valor: str = ""
    resaltar: tuple = ()
    resaltar_cols: tuple = ()
    pivote: tuple | None = None
    separador: int | None = None


def det_fraccion(M: list[list[Fraction]]) -> Fraction:
    """Determinante exacto por eliminación (la matriz vacía vale 1)."""
    n = len(M)
    A = [fila[:] for fila in M]
    det = Fraction(1)
    for c in range(n):
        p = next((i for i in range(c, n) if A[i][c] != 0), None)
        if p is None:
            return Fraction(0)
        if p != c:
            A[c], A[p] = A[p], A[c]
            det = -det
        det *= A[c][c]
        for i in range(c + 1, n):
            f = A[i][c] / A[c][c]
            if f:
                A[i] = [a - f * b for a, b in zip(A[i], A[c])]
    return det


def producto(A: list[list[Fraction]], B: list[list[Fraction]]) -> list[list[Fraction]]:
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]


class Motor:
    """Realiza cada operación y devuelve (resultado, pasos)."""

    def __init__(self, decimales: bool = False):
        self.decimales = decimales

    # ---- formato ------------------------------------------------------------
    def fmt(self, x) -> str:
        if isinstance(x, str):
            return x
        if self.decimales:
            v = round(float(x), 4)
            if v == 0:
                v = 0.0
            s = f"{v:.4f}".rstrip("0").rstrip(".")
        else:
            s = str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"
        return s.replace("-", "−")

    def copia(self, x) -> str:
        """Texto con '-' normal, apto para pegar en Excel u otras apps."""
        return self.fmt(x).replace("−", "-")

    def t(self, x) -> str:
        """Número listo para usarse en un producto: negativos y fracciones entre paréntesis."""
        s = self.fmt(x)
        return f"({s})" if (x < 0 or "/" in s) else s

    def _coef(self, x: Fraction) -> str:
        """Coeficiente de una operación de filas: '' si vale 1, '3·', '(1/2)·'."""
        if abs(x) == 1:
            return ""
        s = self.fmt(abs(x))
        return f"({s})·" if "/" in s else f"{s}·"

    # ---- utilidades ----------------------------------------------------------
    @staticmethod
    def _menor(A, i, j):
        n = len(A)
        return [[A[r][c] for c in range(n) if c != j] for r in range(n) if r != i]

    @staticmethod
    def _cuadrada(A):
        if len(A) != len(A[0]):
            raise ErrorMatematico(
                "La matriz no es cuadrada",
                f"La matriz A es {dim_txt(A)} y esta operación necesita una matriz con "
                f"el mismo número de filas que de columnas.")

    def _expr_det2(self, m, completo=True) -> str:
        a, b, c, d = m[0][0], m[0][1], m[1][0], m[1][1]
        s = f"{self.t(a)}·{self.t(d)} − {self.t(b)}·{self.t(c)}"
        if completo:
            s += f" = {self.fmt(a * d)} − {self.t(b * c)}"
        return s

    # ---- punto de entrada ---------------------------------------------------
    def resolver(self, op: str, A, B=None) -> tuple[Paso, list[Paso]]:
        if op == "suma":
            return self._suma_resta(A, B, "+")
        if op == "resta":
            return self._suma_resta(A, B, "−")
        if op == "mult":
            return self._multiplicacion(A, B)
        if op == "inversa":
            return self._inversa(A)
        if op == "det":
            return self._determinante(A)
        if op == "cof":
            return self._cofactores(A)
        if op == "gauss":
            return self._gauss_jordan(A)
        raise ValueError(f"Operación desconocida: {op}")

    # ---- suma y resta -------------------------------------------------------
    def _suma_resta(self, A, B, signo):
        if (len(A), len(A[0])) != (len(B), len(B[0])):
            raise ErrorMatematico(
                "Dimensiones distintas",
                f"A es {dim_txt(A)} y B es {dim_txt(B)}. Para sumar o restar, las dos "
                f"matrices deben tener exactamente el mismo tamaño.")
        palabra = "suma" if signo == "+" else "resta"
        m, n = len(A), len(A[0])
        pasos = [
            Paso("Regla",
                 f"Las dos matrices son {m} × {n}, así que se pueden {'sumar' if signo == '+' else 'restar'}. "
                 f"Se opera cada elemento de A con el elemento que ocupa la misma posición en B:  "
                 f"cᵢⱼ = aᵢⱼ {signo} bᵢⱼ"),
            Paso(f"Aplicar la {palabra} en cada posición",
                 matriz=[[f"{self.fmt(A[i][j])} {signo} {self.t(B[i][j])}" for j in range(n)]
                         for i in range(m)]),
        ]
        R = [[A[i][j] + B[i][j] if signo == "+" else A[i][j] - B[i][j] for j in range(n)]
             for i in range(m)]
        return Paso("A + B" if signo == "+" else "A − B", matriz=R), pasos

    # ---- multiplicación -----------------------------------------------------
    def _multiplicacion(self, A, B):
        m, n, p = len(A), len(A[0]), len(B[0])
        if n != len(B):
            raise ErrorMatematico(
                "Dimensiones incompatibles",
                f"A es {dim_txt(A)} y B es {dim_txt(B)}. Para multiplicar, el número de "
                f"columnas de A ({n}) debe ser igual al número de filas de B ({len(B)}).")
        pasos = [Paso(
            "Comprobar dimensiones",
            f"A es {m} × {n} y B es {n} × {p}. Como las columnas de A ({n}) coinciden con las "
            f"filas de B ({n}), se pueden multiplicar y el resultado será {m} × {p}.\n"
            f"Cada elemento cᵢⱼ es la suma de multiplicar la fila i de A por la columna j de B, "
            f"elemento a elemento.")]

        prods = [self.t(A[0][k]) + "·" + self.t(B[k][0]) for k in range(n)]
        vals = [A[0][k] * B[k][0] for k in range(n)]
        total = sum(vals)
        pasos.append(Paso(
            f"Ejemplo: elemento c{sub(1)}{sub(1)}",
            "Fila 1 de A por columna 1 de B:",
            nota=f"{' + '.join(prods)} = {' + '.join(self.t(v) if i else self.fmt(v) for i, v in enumerate(vals))}"
                 f" = {self.fmt(total)}"))

        celdas = []
        for i in range(m):
            fila = []
            for j in range(p):
                terminos = [f"{self.t(A[i][k])}·{self.t(B[k][j])}" for k in range(n)]
                una_linea = " + ".join(terminos)
                fila.append(una_linea if len(una_linea) <= 24 else "\n+ ".join(terminos))
            celdas.append(fila)
        pasos.append(Paso("Operación en cada posición", matriz=celdas))
        return Paso("A × B", matriz=producto(A, B)), pasos

    # ---- determinante -------------------------------------------------------
    @staticmethod
    def _mejor_linea(A):
        """Fila o columna con más ceros (la más cómoda para desarrollar)."""
        n = len(A)
        mejor = ("fila", 0, sum(1 for v in A[0] if v == 0))
        for i in range(n):
            z = sum(1 for v in A[i] if v == 0)
            if z > mejor[2]:
                mejor = ("fila", i, z)
        for j in range(n):
            z = sum(1 for i in range(n) if A[i][j] == 0)
            if z > mejor[2]:
                mejor = ("columna", j, z)
        return mejor

    def _determinante(self, A):
        self._cuadrada(A)
        n = len(A)
        d = det_fraccion(A)
        pasos = [Paso("Matriz original", matriz=A)]

        if n == 1:
            pasos.append(Paso("Matriz 1 × 1",
                              "El determinante de una matriz de un solo elemento es ese mismo elemento."))
        elif n == 2:
            a, b, c, e = A[0][0], A[0][1], A[1][0], A[1][1]
            pasos.append(Paso(
                "Fórmula para matrices 2 × 2",
                "Se multiplica la diagonal principal (↘) y se le resta el producto de la "
                "diagonal secundaria (↙):",
                nota="|A| = a·d − b·c"))
            pasos.append(Paso(
                "Sustituir los valores",
                nota=f"|A| = {self.t(a)}·{self.t(e)} − {self.t(b)}·{self.t(c)}\n"
                     f"    = {self.fmt(a * e)} − {self.t(b * c)}\n"
                     f"    = {self.fmt(d)}"))
        else:
            tipo, idx, ceros = self._mejor_linea(A)
            if ceros:
                motivo = f"tiene {ceros} cero{'s' if ceros != 1 else ''} (cada cero anula su término y ahorra cuentas)"
            else:
                motivo = "ninguna fila ni columna tiene ceros, así que se toma la primera fila"
            pasos.append(Paso(
                f"Elegir la {tipo} para desarrollar",
                f"Se desarrolla por la {tipo} {idx + 1} porque {motivo}.\n"
                f"Fórmula: |A| = Σ (−1)^(i+j) · aᵢⱼ · det(Mᵢⱼ), donde Mᵢⱼ es la matriz que "
                f"queda al quitar la fila i y la columna j.",
                matriz=A,
                resaltar=(idx,) if tipo == "fila" else (),
                resaltar_cols=(idx,) if tipo == "columna" else ()))

            aportes = []
            for pos in range(n):
                i, j = (idx, pos) if tipo == "fila" else (pos, idx)
                a = A[i][j]
                if a == 0:
                    continue
                menor = self._menor(A, i, j)
                dm = det_fraccion(menor)
                signo = 1 if (i + j) % 2 == 0 else -1
                aporte = signo * a * dm
                aportes.append(aporte)
                nom = f"{sub(i + 1)}{sub(j + 1)}"
                if len(menor) == 2:
                    linea_det = f"det(M{nom}) = {self._expr_det2(menor)} = {self.fmt(dm)}"
                else:
                    linea_det = (f"det(M{nom}) = {self.fmt(dm)}   "
                                 f"(se calcula con el mismo método, de forma recursiva)")
                pasos.append(Paso(
                    f"Término {len(aportes)}: elemento a{nom}",
                    f"a{nom} = {self.fmt(a)}. Su signo es (−1)^({i + 1}+{j + 1}) = "
                    f"{'+1' if signo > 0 else '−1'}. Se quita la fila {i + 1} y la columna {j + 1} "
                    f"y queda el menor M{nom}:",
                    matriz=menor,
                    nota=f"{linea_det}\n"
                         f"aporte = ({'+1' if signo > 0 else '−1'})·{self.t(a)}·{self.t(dm)} = {self.fmt(aporte)}"))

            if aportes:
                suma = " + ".join(self.t(v) if k else self.fmt(v) for k, v in enumerate(aportes))
                pasos.append(Paso("Sumar los aportes",
                                  "Los elementos que valen 0 no aportan nada. El determinante es la suma de los aportes:",
                                  nota=f"|A| = {suma} = {self.fmt(d)}"))
            else:
                pasos.append(Paso("Todos los elementos son 0",
                                  "Como todos los elementos de esa línea valen 0, el determinante es 0."))

        nota = ("Como |A| = 0, la matriz es singular: no tiene inversa y sus filas "
                "(o columnas) son linealmente dependientes.") if d == 0 else \
               "Como |A| ≠ 0, la matriz es invertible."
        return Paso("Determinante |A|", valor=self.fmt(d), texto=nota), pasos

    # ---- cofactores ---------------------------------------------------------
    def _cofactores(self, A):
        self._cuadrada(A)
        n = len(A)
        pasos = [Paso("Matriz original", matriz=A)]

        if n == 1:
            pasos.append(Paso("Matriz 1 × 1",
                              "Al quitar la única fila y la única columna queda una matriz vacía, "
                              "cuyo determinante se define como 1. Por eso el cofactor es 1."))
            return Paso("Matriz de cofactores C", matriz=[[Fraction(1)]]), pasos

        menores = [[self._menor(A, i, j) for j in range(n)] for i in range(n)]
        valores = [[det_fraccion(menores[i][j]) for j in range(n)] for i in range(n)]
        signos = [[1 if (i + j) % 2 == 0 else -1 for j in range(n)] for i in range(n)]

        if n == 2:
            pasos.append(Paso(
                "Menores Mᵢⱼ",
                "Al quitar una fila y una columna de una matriz 2 × 2 queda un solo número: "
                "ese es el menor de la posición contraria.",
                matriz=valores))
        else:
            pasos.append(Paso(
                "Menores Mᵢⱼ",
                "El menor Mᵢⱼ es el determinante de la matriz que queda al quitar la fila i y la columna j."))
            if n == 3:
                pasos.append(Paso(
                    "Determinante de cada menor (2 × 2)",
                    "Cada menor es una matriz 2 × 2, se resuelve con a·d − b·c:",
                    matriz=[[self._expr_det2(menores[i][j], completo=False) for j in range(n)]
                            for i in range(n)]))
            pasos.append(Paso("Valor de cada menor", matriz=valores))

        pasos.append(Paso(
            "Ley de signos",
            "Cada posición lleva el signo (−1)^(i+j): se alternan + y − como un tablero de "
            "ajedrez, empezando con + arriba a la izquierda.",
            matriz=[["+" if s > 0 else "−" for s in fila] for fila in signos]))

        C = [[signos[i][j] * valores[i][j] for j in range(n)] for i in range(n)]
        pasos.append(Paso(
            "Multiplicar cada menor por su signo",
            "Cᵢⱼ = (−1)^(i+j) · Mᵢⱼ",
            matriz=[[f"({'+1' if signos[i][j] > 0 else '−1'})·{self.t(valores[i][j])}"
                     for j in range(n)] for i in range(n)]))
        return Paso("Matriz de cofactores C", matriz=C), pasos

    # ---- Gauss-Jordan (motor común) --------------------------------------------
    def _gauss(self, M0, columnas_pivote: int, separador: int | None):
        """Reduce M0 a la forma escalonada reducida. Devuelve (pasos, M, columnas_pivote_usadas)."""
        M = [fila[:] for fila in M0]
        m = len(M)
        pasos: list[Paso] = []
        pivotes: list[int] = []
        r = 0
        for c in range(columnas_pivote):
            if r >= m:
                break
            p = next((i for i in range(r, m) if M[i][c] != 0), None)
            if p is None:
                pasos.append(Paso(
                    f"Columna {c + 1} sin pivote",
                    f"Desde la fila {r + 1} hacia abajo todos los valores de la columna {c + 1} "
                    f"son 0, así que no hay pivote en ella. Se continúa con la siguiente columna."))
                continue

            if p != r:
                M[r], M[p] = M[p], M[r]
                pasos.append(Paso(
                    f"F{sub(r + 1)} ↔ F{sub(p + 1)}",
                    f"El valor de la posición ({r + 1}, {c + 1}) es 0. Se intercambian las filas "
                    f"{r + 1} y {p + 1} para conseguir un pivote distinto de cero.",
                    matriz=[f[:] for f in M], resaltar=(r, p), separador=separador))

            piv = M[r][c]
            if piv != 1:
                M[r] = [x / piv for x in M[r]]
                pasos.append(Paso(
                    f"F{sub(r + 1)} ← F{sub(r + 1)} ÷ {self.t(piv)}",
                    f"Se divide toda la fila {r + 1} entre el pivote {self.fmt(piv)} para que el "
                    f"pivote pase a valer 1.",
                    matriz=[f[:] for f in M], resaltar=(r,), pivote=(r, c), separador=separador))

            for k in range(m):
                if k != r and M[k][c] != 0:
                    f = M[k][c]
                    M[k] = [a - f * b for a, b in zip(M[k], M[r])]
                    op = "−" if f > 0 else "+"
                    pasos.append(Paso(
                        f"F{sub(k + 1)} ← F{sub(k + 1)} {op} {self._coef(f)}F{sub(r + 1)}",
                        f"Se hace 0 el valor {self.fmt(f)} de la posición ({k + 1}, {c + 1}) "
                        f"{'restando' if f > 0 else 'sumando'} {self.fmt(abs(f))} "
                        f"{'vez' if abs(f) == 1 else 'veces'} la fila {r + 1}.",
                        matriz=[g[:] for g in M], resaltar=(k,), pivote=(r, c), separador=separador))
            pivotes.append(c)
            r += 1
        return pasos, M, pivotes

    def _despeje(self, nombre: str, const: Fraction, terminos: list[tuple[Fraction, str]]) -> str:
        """Escribe  nombre = const + coef·var + ...  sin signos feos."""
        s = self.fmt(const) if (const != 0 or not terminos) else ""
        for coef, var in terminos:
            mag = self.fmt(abs(coef))
            parte = var if abs(coef) == 1 else (f"({mag})·{var}" if "/" in mag else f"{mag}·{var}")
            if s == "":
                s = parte if coef > 0 else f"−{parte}"
            else:
                s += f" {'−' if coef < 0 else '+'} {parte}"
        return f"{nombre} = {s}"

    def _gauss_jordan(self, A):
        m, cols = len(A), len(A[0])
        n = m                      # número de incógnitas
        if cols != n + 1:
            raise ErrorMatematico(
                "Tamaño no válido para Gauss-Jordan",
                f"Un sistema de {n} ecuaciones con {n} incógnitas necesita una matriz aumentada "
                f"de {n} × {n + 1} (la última columna son los términos independientes). "
                f"Se recibió una matriz {dim_txt(A)}.")
        pasos = [Paso(
            "Matriz aumentada [ A | b ]",
            f"Cada fila es una ecuación: las primeras {n} columnas son los coeficientes de "
            f"{', '.join('x' + sub(i + 1) for i in range(n))} y la última columna son los términos "
            f"independientes.\nSe aplican operaciones elementales sobre las filas (F₁, F₂, …) hasta "
            f"obtener 1 en la diagonal y 0 en el resto.",
            matriz=A, separador=n)]
        ops, M, pivotes = self._gauss(A, n, n)
        pasos += ops or [Paso("Sin operaciones", "La matriz ya está en forma reducida.")]

        incompatible = next((fila for fila in M if all(v == 0 for v in fila[:n]) and fila[n] != 0), None)
        if incompatible is not None:
            titulo = "Sistema sin solución"
            texto = (f"Una fila quedó como 0 = {self.fmt(incompatible[n])}, lo cual es imposible. "
                     f"Las ecuaciones se contradicen entre sí.")
        else:
            libres = [c for c in range(n) if c not in pivotes]
            if not libres:
                titulo = "Solución única"
                texto = "\n".join(f"x{sub(i + 1)} = {self.fmt(M[i][n])}" for i in range(n))
            else:
                titulo = "Infinitas soluciones"
                por_variable = {f: f"x{sub(f + 1)} = libre (cualquier número real)" for f in libres}
                for fila, c in enumerate(pivotes):
                    terminos = [(-M[fila][f], f"x{sub(f + 1)}") for f in libres if M[fila][f] != 0]
                    por_variable[c] = self._despeje(f"x{sub(c + 1)}", M[fila][n], terminos)
                texto = "\n".join(por_variable[c] for c in range(n))
        return Paso(titulo, texto=texto, matriz=M, separador=n), pasos

    # ---- inversa ------------------------------------------------------------
    def _inversa(self, A):
        self._cuadrada(A)
        n = len(A)
        d = det_fraccion(A)
        if d == 0:
            raise ErrorMatematico(
                "La matriz no tiene inversa",
                "Su determinante es 0 (matriz singular). Una matriz solo es invertible si su "
                "determinante es distinto de cero.")
        I = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]
        aumentada = [A[i] + I[i] for i in range(n)]
        pasos = [
            Paso("Comprobar que existe la inversa",
                 f"Se calcula el determinante: |A| = {self.fmt(d)}. Como es distinto de cero, "
                 f"la matriz es invertible."),
            Paso("Matriz aumentada [ A | I ]",
                 "A la derecha de A se coloca la matriz identidad. Se aplican operaciones sobre "
                 "las filas hasta convertir la parte izquierda en la identidad; la parte derecha "
                 "se transforma entonces en A⁻¹.",
                 matriz=aumentada, separador=n),
        ]
        ops, M, _ = self._gauss(aumentada, n, n)
        pasos += ops or [Paso("Sin operaciones", "La matriz ya es la identidad: su inversa es ella misma.")]
        inv = [fila[n:] for fila in M]
        pasos.append(Paso("Leer la inversa",
                          "A la izquierda quedó la identidad [ I | A⁻¹ ]. La parte derecha es la inversa.",
                          matriz=M, separador=n))
        pasos.append(Paso("Comprobación: A · A⁻¹ = I",
                          "Al multiplicar la matriz original por su inversa debe resultar la identidad:",
                          matriz=producto(A, inv)))
        return Paso("Matriz inversa A⁻¹", matriz=inv), pasos


# =============================================================================
# 3. COMPONENTES VISUALES
# =============================================================================
class Boton(tk.Frame):
    """Botón plano. estilos: 'primario', 'secundario', 'fantasma'."""

    @staticmethod
    def _estilos():
        return {
            "primario": dict(bg=T.ACENTO, fg="#FFFFFF", hover=T.ACENTO_HOVER, borde=T.ACENTO),
            "secundario": dict(bg=T.SUPERFICIE, fg=T.TEXTO, hover=T.HOVER, borde=T.BORDE),
            "fantasma": dict(bg=T.SUPERFICIE, fg=T.ACENTO_TEXTO, hover=T.ACENTO_SUAVE, borde=T.SUPERFICIE),
        }

    def __init__(self, parent, texto, comando, estilo="secundario", padx=18, pady=8, fuente=None):
        e = self._estilos()[estilo]
        super().__init__(parent, bg=e["bg"], highlightthickness=1,
                         highlightbackground=e["borde"], highlightcolor=e["borde"], cursor="hand2")
        self.lbl = tk.Label(self, text=texto, bg=e["bg"], fg=e["fg"], font=fuente or F["ui_b"],
                            padx=padx, pady=pady, cursor="hand2")
        self.lbl.pack()
        for w in (self, self.lbl):
            w.bind("<Enter>", lambda ev: self._pintar(e["hover"]))
            w.bind("<Leave>", lambda ev: self._pintar(e["bg"]))
            w.bind("<Button-1>", lambda ev: comando())

    def _pintar(self, color):
        self.configure(bg=color)
        self.lbl.configure(bg=color)

    def set_texto(self, texto):
        self.lbl.configure(text=texto)


class Segmentado(tk.Frame):
    """Selector con varias opciones en una sola barra (valor, texto)."""

    def __init__(self, parent, opciones, valor, comando):
        super().__init__(parent, bg=T.SEGMENTO, padx=2, pady=2)
        self.comando = comando
        self.etiquetas = {}
        self.valor = None
        for val, texto in opciones:
            lbl = tk.Label(self, text=texto, font=F["peq_b"], padx=4, pady=5, cursor="hand2")
            lbl.pack(side="left", expand=True, fill="x")
            lbl.bind("<Button-1>", lambda e, v=val: self._elegir(v))
            self.etiquetas[val] = lbl
        self.set(valor)

    def set(self, valor):
        self.valor = valor
        for v, lbl in self.etiquetas.items():
            if v == valor:
                lbl.configure(bg=T.SEG_ACTIVO, fg=T.TEXTO)
            else:
                lbl.configure(bg=T.SEGMENTO, fg=T.TEXTO_2)

    def _elegir(self, valor):
        if valor != self.valor:
            self.set(valor)
            self.comando(valor)


class Contador(tk.Frame):
    """Etiqueta + [−] valor [+]."""

    def __init__(self, parent, texto, valor, minimo, maximo, comando, bg):
        super().__init__(parent, bg=bg)
        self.minimo, self.maximo, self.valor = minimo, maximo, valor
        self.comando = comando
        self.activo = True
        tk.Label(self, text=texto, font=F["ui"], bg=bg, fg=T.TEXTO_2).pack(side="left")
        grupo = tk.Frame(self, bg=bg)
        grupo.pack(side="right")
        self.b_menos = self._crear_boton(grupo, "−", -1)
        self.lbl_valor = tk.Label(grupo, text=str(valor), width=3, font=F["ui_b"], bg=bg, fg=T.TEXTO)
        self.lbl_valor.pack(side="left")
        self.b_mas = self._crear_boton(grupo, "+", +1)
        self._refrescar()

    def _crear_boton(self, parent, simbolo, paso):
        b = tk.Label(parent, text=simbolo, width=2, font=F["ui_b"], pady=2)
        b.pack(side="left")
        b.bind("<Button-1>", lambda e: self._click(paso))
        b.bind("<Enter>", lambda e: b.configure(bg=T.HOVER_2) if self._puede(paso) else None)
        b.bind("<Leave>", lambda e: self._refrescar())
        return b

    def _puede(self, paso):
        if not self.activo:
            return False
        return self.valor + paso >= self.minimo and self.valor + paso <= self.maximo

    def _click(self, paso):
        if self._puede(paso):
            self.valor += paso
            self._refrescar()
            self.comando(self.valor)

    def _refrescar(self):
        self.lbl_valor.configure(text=str(self.valor), fg=T.TEXTO if self.activo else T.TEXTO_3)
        for b, paso in ((self.b_menos, -1), (self.b_mas, +1)):
            if self._puede(paso):
                b.configure(bg=T.HOVER, fg=T.TEXTO, cursor="hand2")
            else:
                b.configure(bg=T.CAMPO, fg=T.DESACTIVADO, cursor="arrow")

    def set(self, valor):
        self.valor = valor
        self._refrescar()

    def set_max(self, maximo):
        self.maximo = maximo
        self._refrescar()

    def set_enabled(self, activo):
        self.activo = activo
        self._refrescar()


class ScrollFrame(tk.Frame):
    """Zona con scroll (vertical y opcionalmente horizontal). El contenido va en `.inner`."""

    def __init__(self, parent, bg, horizontal=True, on_resize=None):
        super().__init__(parent, bg=bg)
        self.horizontal = horizontal
        self.on_resize = on_resize
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0,
                                yscrollincrement=28, xscrollincrement=28)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb = ttk.Scrollbar(self, orient="vertical", style="Minimal.Vertical.TScrollbar",
                                 command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=lambda a, b: self._ajustar_barra(self.vsb, a, b, 0, 1))
        if horizontal:
            self.hsb = ttk.Scrollbar(self, orient="horizontal", style="Minimal.Horizontal.TScrollbar",
                                     command=self.canvas.xview)
            self.canvas.configure(xscrollcommand=lambda a, b: self._ajustar_barra(self.hsb, a, b, 1, 0))

        self.inner = tk.Frame(self.canvas, bg=bg)
        self._ventana = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._al_cambiar_contenido)
        self.canvas.bind("<Configure>", self._al_cambiar_vista)

        for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_all(evento, self._rueda, add="+")

    @staticmethod
    def _ajustar_barra(barra, lo, hi, fila, columna):
        """Muestra la barra solo cuando hace falta."""
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            barra.grid_remove()
        else:
            barra.grid(row=fila, column=columna, sticky="ns" if columna else "ew")
        barra.set(lo, hi)

    def _ancho_ventana(self):
        ancho = self.canvas.winfo_width()
        if self.horizontal:
            ancho = max(ancho, self.inner.winfo_reqwidth())
        return ancho

    def _al_cambiar_contenido(self, _e=None):
        self.canvas.itemconfigure(self._ventana, width=self._ancho_ventana())
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _al_cambiar_vista(self, e):
        self.canvas.itemconfigure(self._ventana, width=self._ancho_ventana())
        if self.on_resize:
            self.on_resize(e.width)

    def _dentro(self, widget):
        while widget is not None:
            if widget is self:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _rueda(self, e):
        if not self.winfo_exists():          # un tema anterior ya destruido
            return
        try:
            bajo_el_cursor = self.winfo_containing(e.x_root, e.y_root)
        except (KeyError, tk.TclError):
            return
        if not self._dentro(bajo_el_cursor):
            return
        if e.num == 4:
            d = -1
        elif e.num == 5:
            d = 1
        else:
            d = -1 if e.delta > 0 else 1
        if self.horizontal and (e.state & 0x0001):          # Shift + rueda = horizontal
            if self.canvas.xview() != (0.0, 1.0):
                self.canvas.xview_scroll(d * 2, "units")
        elif self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(d * 2, "units")

    def asegurar_visible(self, widget):
        """Desplaza la vista si `widget` queda muy abajo."""
        self.update_idletasks()
        total = max(1, self.inner.winfo_height())
        arriba = widget.winfo_rooty() - self.inner.winfo_rooty()
        visible_desde = self.canvas.yview()[0] * total
        if arriba - visible_desde > self.canvas.winfo_height() * 0.55:
            self.canvas.yview_moveto(max(0.0, (arriba - 24) / total))


class MatrizVista(tk.Canvas):
    """Dibuja una matriz con corchetes. Admite celdas de texto largas y multilínea."""

    MARGEN_X = 14
    MARGEN_Y = 4
    PAD_X = 12
    PAD_Y = 6

    def __init__(self, parent, celdas, bg, fuente=None, fuente_b=None, resaltar=(),
                 resaltar_cols=(), pivote=None, separador=None):
        fuente = fuente or F["mono"]
        fuente_b = fuente_b or F["mono_b"]
        alto_linea = fuente.metrics("linespace")
        m, n = len(celdas), len(celdas[0])
        lineas = [[celda.split("\n") for celda in fila] for fila in celdas]
        anchos = [max(44, max(fuente.measure(l) for i in range(m) for l in lineas[i][j]) + 2 * self.PAD_X)
                  for j in range(n)]
        altos = [max(len(lineas[i][j]) for j in range(n)) * alto_linea + 2 * self.PAD_Y for i in range(m)]
        ancho = sum(anchos) + 2 * self.MARGEN_X
        alto = sum(altos) + 2 * self.MARGEN_Y
        super().__init__(parent, width=ancho, height=alto, bg=bg, highlightthickness=0, bd=0)

        xs = [self.MARGEN_X]
        for a in anchos:
            xs.append(xs[-1] + a)
        ys = [self.MARGEN_Y]
        for h in altos:
            ys.append(ys[-1] + h)

        for i in resaltar:                                        # fondos
            self.create_rectangle(xs[0] - 4, ys[i] + 1, xs[-1] + 4, ys[i + 1] - 1, fill=T.FILA, outline="")
        for j in resaltar_cols:
            self.create_rectangle(xs[j] + 1, ys[0] - 2, xs[j + 1] - 1, ys[-1] + 2, fill=T.FILA, outline="")
        if pivote is not None:
            i, j = pivote
            self.create_rectangle(xs[j] + 2, ys[i] + 2, xs[j + 1] - 2, ys[i + 1] - 2, fill=T.PIVOTE, outline="")

        for i in range(m):                                        # textos
            for j in range(n):
                es_pivote = pivote == (i, j)
                self.create_text((xs[j] + xs[j + 1]) / 2, (ys[i] + ys[i + 1]) / 2,
                                 text="\n".join(lineas[i][j]), justify="center",
                                 font=fuente_b if es_pivote else fuente,
                                 fill=T.ACENTO_TEXTO if es_pivote else T.TEXTO)

        if separador is not None and 0 < separador < n:           # línea de matriz aumentada
            self.create_line(xs[separador], 6, xs[separador], alto - 6, fill=T.TEXTO_3, dash=(3, 3))

        b = 7                                                     # corchetes
        izq, der = xs[0] - 2, xs[-1] + 2
        self.create_line(izq + b, 2, izq, 2, izq, alto - 2, izq + b, alto - 2, fill=T.CORCHETE, width=2)
        self.create_line(der - b, 2, der, 2, der, alto - 2, der - b, alto - 2, fill=T.CORCHETE, width=2)


# =============================================================================
# 4. APLICACIÓN
# =============================================================================
@dataclass(frozen=True)
class Operacion:
    clave: str
    nombre: str
    simbolo: str
    ayuda: str
    binaria: bool = False


OPERACIONES = [
    Operacion("suma", "Suma", "+",
              "Suma cada elemento de A con el de la misma posición en B. Ambas matrices deben tener el mismo tamaño.",
              True),
    Operacion("resta", "Resta", "−",
              "Resta cada elemento de B al de la misma posición en A. Ambas matrices deben tener el mismo tamaño.",
              True),
    Operacion("mult", "Multiplicación", "×",
              "El número de columnas de A debe coincidir con el número de filas de B.", True),
    Operacion("inversa", "Inversa", "A⁻¹",
              "Solo existe para matrices cuadradas con determinante distinto de cero."),
    Operacion("det", "Determinante", "|A|",
              "Matriz cuadrada. Se desarrolla por la fila o columna con más ceros."),
    Operacion("cof", "Cofactores", "C",
              "Matriz cuadrada. Cada elemento es su menor con el signo (−1)^(i+j)."),
    Operacion("gauss", "Gauss-Jordan", "GJ",
              "Resuelve un sistema de n ecuaciones con n incógnitas. La última columna contiene los "
              "términos independientes."),
]
OP_POR_CLAVE = {op.clave: op for op in OPERACIONES}


class EntradaInvalida(Exception):
    def __init__(self, entrada, nombre, fila, col):
        super().__init__("Valor no válido")
        self.entrada, self.nombre, self.fila, self.col = entrada, nombre, fila, col


class CalculadoraMatricesApp:
    ANCHO_BARRA = 296

    def __init__(self, root: tk.Tk):
        self.root = root
        self.tema = "oscuro"                 # tema con el que arranca la app
        T.aplicar(self.tema)
        root.title("Calculadora de Matrices")
        root.geometry("1200x800")
        root.minsize(980, 640)
        root.configure(bg=T.BG)
        crear_fuentes()
        self._estilos_ttk()

        self.motor = Motor()
        self.op = "suma"
        self.preset: int | None = None
        self.dims = {"ra": 2, "ca": 2, "rb": 2, "cb": 2}
        self.entradas_a: list[list[tk.Entry]] = []
        self.entradas_b: list[list[tk.Entry]] = []
        self._cache = {"A": [], "B": []}
        self._ultimo = None                  # (op, A, B) del último cálculo
        self._texto_copia = ""
        self._wrap_labels: list[tk.Label] = []
        self._wrap = 700

        self._construir_ui()
        root.bind("<Control-Return>", lambda e: self.calcular())
        self._cambio_estructura()

    # ------------------------------------------------------------------ estilos
    def _estilos_ttk(self):
        st = ttk.Style(self.root)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        for orient in ("Vertical", "Horizontal"):
            nombre = f"Minimal.{orient}.TScrollbar"
            try:
                st.layout(nombre, [(f"{orient}.Scrollbar.trough", {
                    "sticky": "nswe",
                    "children": [(f"{orient}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
            except tk.TclError:
                pass
            st.configure(nombre, background=T.SCROLL, troughcolor=T.BG, bordercolor=T.BG,
                         lightcolor=T.SCROLL, darkcolor=T.SCROLL, relief="flat", gripcount=0, width=10)
            st.map(nombre, background=[("pressed", T.SCROLL_PRESS), ("active", T.SCROLL_HOVER)])

    # ---------------------------------------------------------------- estructura
    def _construir_ui(self):
        cont = self._cont = tk.Frame(self.root, bg=T.BG)
        cont.pack(fill="both", expand=True)

        barra = tk.Frame(cont, bg=T.SUPERFICIE, width=self.ANCHO_BARRA)
        barra.pack(side="left", fill="y")
        barra.pack_propagate(False)
        tk.Frame(cont, bg=T.BORDE, width=1).pack(side="left", fill="y")

        scroll_barra = ScrollFrame(barra, T.SUPERFICIE, horizontal=False)
        scroll_barra.pack(fill="both", expand=True)
        self._construir_barra(scroll_barra.inner)

        self.main = ScrollFrame(cont, T.BG, horizontal=True, on_resize=self._ajustar_wrap)
        self.main.pack(side="left", fill="both", expand=True)
        self._construir_pagina(self.main.inner)

    # ----------------------------------------------------------------- barra lateral
    def _seccion(self, parent, texto, pady=(22, 8)):
        tk.Label(parent, text=texto, font=F["seccion"], bg=T.SUPERFICIE, fg=T.TEXTO_3,
                 anchor="w").pack(fill="x", pady=pady)

    def _construir_barra(self, parent):
        cuerpo = tk.Frame(parent, bg=T.SUPERFICIE)
        cuerpo.pack(fill="both", expand=True, padx=20, pady=(26, 20))

        tk.Label(cuerpo, text="Matrices", font=F["marca"], bg=T.SUPERFICIE, fg=T.TEXTO,
                 anchor="w").pack(fill="x")
        tk.Label(cuerpo, text="Calculadora paso a paso", font=F["peq"], bg=T.SUPERFICIE,
                 fg=T.TEXTO_2, anchor="w").pack(fill="x")

        # --- Operación
        self._seccion(cuerpo, "OPERACIÓN")
        self.items_op = {}
        for op in OPERACIONES:
            self.items_op[op.clave] = self._crear_item_operacion(cuerpo, op)

        # --- Tamaño
        self._seccion(cuerpo, "TAMAÑO")
        self.seg_preset = Segmentado(
            cuerpo, [(None, "Libre")] + [(n, f"{n}×{n}") for n in PRESETS], None, self._preset_cambiado)
        self.seg_preset.pack(fill="x")

        dims = tk.Frame(cuerpo, bg=T.SUPERFICIE)
        dims.pack(fill="x", pady=(14, 0))
        dims.columnconfigure(0, weight=1)
        self.contadores = {}

        bloque_a = tk.Frame(dims, bg=T.SUPERFICIE)
        bloque_a.grid(row=0, column=0, sticky="ew")
        tk.Label(bloque_a, text="Matriz A", font=F["ui_b"], bg=T.SUPERFICIE, fg=T.TEXTO,
                 anchor="w").pack(fill="x", pady=(0, 6))
        self.contadores["ra"] = self._crear_contador(bloque_a, "Filas", "ra")
        self.contadores["ca"] = self._crear_contador(bloque_a, "Columnas", "ca")

        self.bloque_b = tk.Frame(dims, bg=T.SUPERFICIE)
        self.bloque_b.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        tk.Label(self.bloque_b, text="Matriz B", font=F["ui_b"], bg=T.SUPERFICIE, fg=T.TEXTO,
                 anchor="w").pack(fill="x", pady=(0, 6))
        self.contadores["rb"] = self._crear_contador(self.bloque_b, "Filas", "rb")
        self.contadores["cb"] = self._crear_contador(self.bloque_b, "Columnas", "cb")

        # --- Formato
        self._seccion(cuerpo, "FORMATO DE NÚMEROS")
        Segmentado(cuerpo, [(False, "Fracciones"), (True, "Decimales")], self.motor.decimales,
                   self._formato_cambiado).pack(fill="x")

        # --- Tema
        self._seccion(cuerpo, "TEMA")
        Segmentado(cuerpo, [("claro", "Claro"), ("oscuro", "Oscuro")], self.tema,
                   self._tema_cambiado).pack(fill="x")

    def _crear_contador(self, parent, texto, clave):
        c = Contador(parent, texto, self.dims[clave], 1, MATRIZ_MAX,
                     lambda v, k=clave: self._dim_cambiada(k, v), bg=T.SUPERFICIE)
        c.pack(fill="x", pady=3)
        return c

    def _crear_item_operacion(self, parent, op: Operacion):
        fila = tk.Frame(parent, bg=T.SUPERFICIE, cursor="hand2")
        fila.pack(fill="x", pady=1)
        barra = tk.Frame(fila, bg=T.SUPERFICIE, width=3)
        barra.pack(side="left", fill="y")
        simbolo = tk.Label(fila, text=op.simbolo, width=4, font=F["ui_b"], bg=T.SUPERFICIE,
                           fg=T.TEXTO_2, pady=8, cursor="hand2")
        simbolo.pack(side="left")
        nombre = tk.Label(fila, text=op.nombre, font=F["ui"], bg=T.SUPERFICIE, fg=T.TEXTO,
                          anchor="w", cursor="hand2")
        nombre.pack(side="left", fill="x", expand=True)
        partes = (fila, barra, simbolo, nombre)
        for w in partes:
            w.bind("<Button-1>", lambda e, c=op.clave: self._seleccionar_operacion(c))
            w.bind("<Enter>", lambda e, c=op.clave: self._estilo_item(c, hover=True))
            w.bind("<Leave>", lambda e, c=op.clave: self._estilo_item(c))
        return partes

    def _estilo_item(self, clave, hover=False):
        fila, barra, simbolo, nombre = self.items_op[clave]
        if clave == self.op:
            bg, bg_barra, fg_s, fg_n = T.ACENTO_SUAVE, T.ACENTO, T.ACENTO_TEXTO, T.ACENTO_TEXTO
        else:
            bg = T.HOVER if hover else T.SUPERFICIE
            bg_barra, fg_s, fg_n = bg, T.TEXTO_2, T.TEXTO
        fila.configure(bg=bg)
        barra.configure(bg=bg_barra)
        simbolo.configure(bg=bg, fg=fg_s)
        nombre.configure(bg=bg, fg=fg_n, font=F["ui_b"] if clave == self.op else F["ui"])

    # ------------------------------------------------------------------ página
    def _construir_pagina(self, parent):
        pagina = tk.Frame(parent, bg=T.BG)
        pagina.pack(fill="both", expand=True, padx=32, pady=(28, 28))

        self.lbl_titulo = tk.Label(pagina, font=F["h1"], bg=T.BG, fg=T.TEXTO, anchor="w")
        self.lbl_titulo.pack(fill="x")
        self.lbl_ayuda = tk.Label(pagina, font=F["ui"], bg=T.BG, fg=T.TEXTO_2, anchor="w",
                                  justify="left", wraplength=760)
        self.lbl_ayuda.pack(fill="x", pady=(4, 18))

        # Tarjeta de datos
        datos = self._tarjeta(pagina)
        cab = tk.Frame(datos, bg=T.SUPERFICIE)
        cab.pack(fill="x", pady=(0, 14))
        tk.Label(cab, text="DATOS", font=F["seccion"], bg=T.SUPERFICIE, fg=T.TEXTO_3).pack(side="left")
        Boton(cab, "Limpiar", self.limpiar, "fantasma", padx=10, pady=2,
              fuente=F["peq_b"]).pack(side="right")
        Boton(cab, "Ejemplo", self.rellenar_ejemplo, "fantasma", padx=10, pady=2,
              fuente=F["peq_b"]).pack(side="right", padx=(0, 4))

        self.zona_datos = tk.Frame(datos, bg=T.SUPERFICIE)
        self.zona_datos.pack(fill="x")

        pie = tk.Frame(datos, bg=T.SUPERFICIE)
        pie.pack(fill="x", pady=(20, 0))
        Boton(pie, "Calcular", self.calcular, "primario", padx=30, pady=10).pack(side="left")
        tk.Label(pie, text="Ctrl + Enter", font=F["peq"], bg=T.SUPERFICIE,
                 fg=T.TEXTO_3).pack(side="left", padx=14)

        # Zona de resultados
        self.zona_resultados = tk.Frame(pagina, bg=T.BG)
        self.zona_resultados.pack(fill="x", pady=(4, 0))

    def _tarjeta(self, parent, pady=(0, 18)):
        externa = tk.Frame(parent, bg=T.SUPERFICIE, highlightthickness=1,
                           highlightbackground=T.BORDE, highlightcolor=T.BORDE)
        externa.pack(fill="x", pady=pady)
        interna = tk.Frame(externa, bg=T.SUPERFICIE)
        interna.pack(fill="both", expand=True, padx=24, pady=20)
        return interna

    # ------------------------------------------------------------ reglas de tamaño
    def _seleccionar_operacion(self, clave):
        if clave == self.op:
            return
        self.op = clave
        self._cambio_estructura()

    def _preset_cambiado(self, valor):
        self.preset = valor
        self._cambio_estructura()

    def _dim_cambiada(self, clave, valor):
        self.dims[clave] = valor
        self._cambio_estructura()

    def _formato_cambiado(self, decimales):
        self.motor.decimales = decimales
        if self._ultimo:
            self._resolver_y_mostrar()

    def _tema_cambiado(self, nombre):
        """Cambia entre tema claro y oscuro reconstruyendo la interfaz sin perder datos ni resultado."""
        if nombre == self.tema:
            return
        if self.entradas_a:
            self._cache["A"] = self._valores(self.entradas_a)
        if self.entradas_b:
            self._cache["B"] = self._valores(self.entradas_b)
        ultimo = self._ultimo
        self.tema = nombre
        T.aplicar(nombre)
        self.root.configure(bg=T.BG)
        self._estilos_ttk()
        self._cont.destroy()
        self.entradas_a, self.entradas_b = [], []
        self._construir_ui()
        self._cambio_estructura()
        if ultimo:
            self._ultimo = ultimo
            self._resolver_y_mostrar()

    def _cambio_estructura(self):
        self._aplicar_reglas()
        self._construir_grids()
        op = OP_POR_CLAVE[self.op]
        self.lbl_titulo.configure(text=op.nombre)
        self.lbl_ayuda.configure(text=op.ayuda)
        for clave in self.items_op:
            self._estilo_item(clave)
        self._ultimo = None
        self._mostrar_vacio()

    def _aplicar_reglas(self):
        """Fuerza las dimensiones que exige la operación y bloquea los contadores afectados."""
        op, d, p = self.op, self.dims, self.preset
        max_cols = MATRIZ_MAX + 1 if op == "gauss" else MATRIZ_MAX
        d["ra"] = max(1, min(d["ra"], MATRIZ_MAX))
        d["rb"] = max(1, min(d["rb"], MATRIZ_MAX))
        d["ca"] = max(1, min(d["ca"], max_cols))
        d["cb"] = max(1, min(d["cb"], MATRIZ_MAX))
        bloqueados: set[str] = set()

        if p:
            d["ra"] = p
            d["ca"] = p + 1 if op == "gauss" else p
            d["rb"] = d["cb"] = p
            bloqueados = {"ra", "ca", "rb", "cb"}
        elif op in ("inversa", "det", "cof"):
            d["ca"] = d["ra"]
            bloqueados = {"ca"}
        elif op == "gauss":
            d["ca"] = d["ra"] + 1
            bloqueados = {"ca"}
        elif op in ("suma", "resta"):
            d["rb"], d["cb"] = d["ra"], d["ca"]
            bloqueados = {"rb", "cb"}
        elif op == "mult":
            d["rb"] = d["ca"]
            bloqueados = {"rb"}

        for clave, c in self.contadores.items():
            c.set(d[clave])
            c.set_max(max_cols if clave == "ca" else MATRIZ_MAX)
            c.set_enabled(clave not in bloqueados)
        self.seg_preset.set(p)

        if OP_POR_CLAVE[op].binaria:
            self.bloque_b.grid()
        else:
            self.bloque_b.grid_remove()

    # ------------------------------------------------------------- celdas de entrada
    def _valores(self, entradas):
        return [[e.get() for e in fila] for fila in entradas]

    def _construir_grids(self):
        if self.entradas_a:
            self._cache["A"] = self._valores(self.entradas_a)
        if self.entradas_b:
            self._cache["B"] = self._valores(self.entradas_b)
        for w in self.zona_datos.winfo_children():
            w.destroy()

        d = self.dims
        self.entradas_a = self._crear_grilla("A", d["ra"], d["ca"], self._cache["A"])
        self.entradas_b = []
        op = OP_POR_CLAVE[self.op]
        if op.binaria:
            tk.Label(self.zona_datos, text=op.simbolo, font=F["operador"], bg=T.SUPERFICIE,
                     fg=T.TEXTO_3).pack(side="left", padx=26, pady=(40, 0), anchor="n")
            self.entradas_b = self._crear_grilla("B", d["rb"], d["cb"], self._cache["B"])

    def _crear_grilla(self, nombre, filas, cols, previos):
        marco = tk.Frame(self.zona_datos, bg=T.SUPERFICIE)
        marco.pack(side="left", anchor="n")
        cab = tk.Frame(marco, bg=T.SUPERFICIE)
        cab.pack(fill="x", pady=(0, 10))
        tk.Label(cab, text=f"Matriz {nombre}", font=F["ui_b"], bg=T.SUPERFICIE, fg=T.TEXTO).pack(side="left")
        tk.Label(cab, text=f"{filas} × {cols}", font=F["peq"], bg=T.SUPERFICIE,
                 fg=T.TEXTO_3).pack(side="left", padx=8)

        rejilla = tk.Frame(marco, bg=T.SUPERFICIE)
        rejilla.pack()
        entradas: list[list[tk.Entry]] = []
        for i in range(filas):
            fila = []
            for j in range(cols):
                e = tk.Entry(rejilla, width=5, font=F["mono"], justify="center", relief="flat", bd=0,
                             fg=T.TEXTO, insertbackground=T.TEXTO, highlightthickness=1)
                self._estilo_entrada(e)
                e.grid(row=i, column=j, padx=3, pady=3, ipady=6)
                try:
                    e.insert(0, previos[i][j])
                except IndexError:
                    e.insert(0, "0")
                e.bind("<FocusIn>", lambda ev, w=e: self._al_enfocar(w))
                e.bind("<Key>", lambda ev, w=e: self._estilo_entrada(w))
                e.bind("<Control-Return>", lambda ev: (self.calcular(), "break")[1])
                e.bind("<Return>", lambda ev, i=i, j=j, ent=entradas: self._mover(ent, i, j + 1, True))
                e.bind("<Down>", lambda ev, i=i, j=j, ent=entradas: self._mover(ent, i + 1, j))
                e.bind("<Up>", lambda ev, i=i, j=j, ent=entradas: self._mover(ent, i - 1, j))
                fila.append(e)
            entradas.append(fila)
        return entradas

    @staticmethod
    def _estilo_entrada(e, error=False):
        if error:
            e.configure(bg=T.ERROR_SUAVE, highlightbackground=T.ERROR, highlightcolor=T.ERROR)
        else:
            e.configure(bg=T.CAMPO, highlightbackground=T.BORDE, highlightcolor=T.ACENTO)

    @staticmethod
    def _al_enfocar(e):
        e.after_idle(lambda: e.select_range(0, "end"))

    @staticmethod
    def _mover(entradas, i, j, avanzar=False):
        """Mueve el foco entre celdas. Con avanzar=True salta a la siguiente fila al llegar al final."""
        if avanzar and entradas and j >= len(entradas[0]):
            i, j = i + 1, 0
        if 0 <= i < len(entradas) and 0 <= j < len(entradas[0]):
            entradas[i][j].focus_set()
        return "break"

    def limpiar(self):
        for entradas in (self.entradas_a, self.entradas_b):
            for fila in entradas:
                for e in fila:
                    self._estilo_entrada(e)
                    e.delete(0, "end")
                    e.insert(0, "0")
        self._cache = {"A": [], "B": []}
        self._ultimo = None
        self._mostrar_vacio()

    def rellenar_ejemplo(self):
        for entradas in (self.entradas_a, self.entradas_b):
            for fila in entradas:
                for e in fila:
                    self._estilo_entrada(e)
                    e.delete(0, "end")
                    e.insert(0, str(random.choice([-3, -2, -1, 1, 2, 3, 4, 5, 6])))

    @staticmethod
    def _parsear(texto: str) -> Fraction:
        t = texto.strip().replace(",", ".").replace("−", "-").replace(" ", "")
        return Fraction(t) if t else Fraction(0)

    def _leer(self, entradas, nombre):
        M = []
        for i, fila in enumerate(entradas):
            valores = []
            for j, e in enumerate(fila):
                try:
                    valores.append(self._parsear(e.get()))
                except (ValueError, ZeroDivisionError):
                    raise EntradaInvalida(e, nombre, i + 1, j + 1)
            M.append(valores)
        return M

    # ------------------------------------------------------------------- cálculo
    def calcular(self):
        for entradas in (self.entradas_a, self.entradas_b):
            for fila in entradas:
                for e in fila:
                    self._estilo_entrada(e)
        try:
            A = self._leer(self.entradas_a, "A")
            B = self._leer(self.entradas_b, "B") if OP_POR_CLAVE[self.op].binaria else None
        except EntradaInvalida as err:
            self._estilo_entrada(err.entrada, error=True)
            err.entrada.focus_set()
            self._mostrar_error(
                "Hay un valor que no es un número",
                f"La celda de la fila {err.fila}, columna {err.col} de la matriz {err.nombre} no es válida. "
                f"Puedes escribir enteros (3), decimales (2.5) o fracciones (3/4).")
            return
        self._ultimo = (self.op, A, B)
        self._resolver_y_mostrar()

    def _resolver_y_mostrar(self):
        op, A, B = self._ultimo
        try:
            resultado, pasos = self.motor.resolver(op, A, B)
        except ErrorMatematico as err:
            self._mostrar_error(err.titulo, err.detalle)
            return
        self._mostrar(resultado, pasos)

    # ------------------------------------------------------------------ resultados
    def _ajustar_wrap(self, ancho_vista):
        self._wrap = max(320, ancho_vista - 230)
        self._wrap_labels = [l for l in self._wrap_labels if l.winfo_exists()]
        for l in self._wrap_labels:
            l.configure(wraplength=self._wrap)

    def _texto(self, parent, texto, fuente, fg, bg=None, ancho=None):
        bg = bg or T.SUPERFICIE
        lbl = tk.Label(parent, text=texto, font=fuente, fg=fg, bg=bg, anchor="w", justify="left",
                       wraplength=ancho or self._wrap)
        if ancho is None:
            self._wrap_labels.append(lbl)
        return lbl

    def _limpiar_resultados(self):
        for w in self.zona_resultados.winfo_children():
            w.destroy()
        self._wrap_labels = []

    def _mostrar_vacio(self):
        self._limpiar_resultados()
        tk.Label(self.zona_resultados,
                 text="Introduce los datos y pulsa Calcular para ver el resultado y el procedimiento.",
                 font=F["ui"], bg=T.BG, fg=T.TEXTO_3).pack(pady=30)

    def _mostrar_error(self, titulo, detalle):
        self._limpiar_resultados()
        caja = tk.Frame(self.zona_resultados, bg=T.ERROR_SUAVE, highlightthickness=1,
                        highlightbackground=T.ERROR_BORDE)
        caja.pack(fill="x")
        interior = tk.Frame(caja, bg=T.ERROR_SUAVE)
        interior.pack(fill="x", padx=22, pady=16)
        tk.Label(interior, text=titulo, font=F["ui_b"], fg=T.ERROR, bg=T.ERROR_SUAVE,
                 anchor="w").pack(fill="x")
        self._texto(interior, detalle, F["ui"], T.TEXTO, bg=T.ERROR_SUAVE).pack(anchor="w", pady=(4, 0))

    def _celdas(self, matriz):
        return [[x if isinstance(x, str) else self.motor.fmt(x) for x in fila] for fila in matriz]

    def _vista_matriz(self, parent, paso: Paso, grande=False):
        return MatrizVista(
            parent, self._celdas(paso.matriz), bg=T.SUPERFICIE,
            fuente=F["mono_g"] if grande else F["mono"],
            fuente_b=F["mono_g_b"] if grande else F["mono_b"],
            resaltar=paso.resaltar, resaltar_cols=paso.resaltar_cols,
            pivote=paso.pivote, separador=paso.separador)

    def _mostrar(self, resultado: Paso, pasos: list[Paso]):
        self._limpiar_resultados()
        zona = self.zona_resultados

        # --- Tarjeta de resultado
        card = self._tarjeta(zona)
        cab = tk.Frame(card, bg=T.SUPERFICIE)
        cab.pack(fill="x")
        tk.Label(cab, text="RESULTADO", font=F["seccion"], bg=T.SUPERFICIE, fg=T.TEXTO_3).pack(side="left")
        self.btn_copiar = Boton(cab, "Copiar", self._copiar, "fantasma", padx=10, pady=2, fuente=F["peq_b"])
        self.btn_copiar.pack(side="right")
        tk.Label(card, text=resultado.titulo, font=F["h2"], bg=T.SUPERFICIE, fg=T.TEXTO,
                 anchor="w").pack(fill="x", pady=(6, 10))
        if resultado.valor:
            tk.Label(card, text=resultado.valor, font=F["valor"], bg=T.SUPERFICIE, fg=T.ACENTO_TEXTO,
                     anchor="w").pack(fill="x")
        if resultado.matriz:
            self._vista_matriz(card, resultado, grande=True).pack(anchor="w")
        if resultado.texto:
            es_lista = not resultado.valor
            self._texto(card, resultado.texto, F["mono"] if es_lista else F["ui"],
                        T.TEXTO if es_lista else T.TEXTO_2).pack(anchor="w", pady=(12 if resultado.matriz else 4, 0))

        if resultado.matriz:
            self._texto_copia = "\n".join("\t".join(self.motor.copia(x) for x in fila)
                                          for fila in resultado.matriz)
        else:
            self._texto_copia = resultado.valor.replace("−", "-")

        # --- Tarjeta de procedimiento
        proc = self._tarjeta(zona)
        cab2 = tk.Frame(proc, bg=T.SUPERFICIE)
        cab2.pack(fill="x", pady=(0, 4))
        tk.Label(cab2, text="PROCEDIMIENTO", font=F["seccion"], bg=T.SUPERFICIE,
                 fg=T.TEXTO_3).pack(side="left")
        tk.Label(cab2, text=f"{len(pasos)} paso{'s' if len(pasos) != 1 else ''}", font=F["peq"],
                 bg=T.SUPERFICIE, fg=T.TEXTO_3).pack(side="right")

        for idx, paso in enumerate(pasos, 1):
            tk.Frame(proc, bg=T.BORDE, height=1).pack(fill="x", pady=(14, 0))
            self._crear_paso(proc, idx, paso)

        self.main.asegurar_visible(zona)

    def _crear_paso(self, parent, idx, paso: Paso):
        fila = tk.Frame(parent, bg=T.SUPERFICIE)
        fila.pack(fill="x", pady=(14, 0))

        insignia = tk.Canvas(fila, width=28, height=28, bg=T.SUPERFICIE, highlightthickness=0)
        insignia.create_oval(1, 1, 27, 27, fill=T.ACENTO_SUAVE, outline="")
        insignia.create_text(14, 14, text=str(idx), font=F["peq_b"], fill=T.ACENTO_TEXTO)
        insignia.pack(side="left", anchor="n", padx=(0, 14))

        cuerpo = tk.Frame(fila, bg=T.SUPERFICIE)
        cuerpo.pack(side="left", fill="x", expand=True)
        tk.Label(cuerpo, text=paso.titulo, font=F["ui_b"], bg=T.SUPERFICIE, fg=T.TEXTO,
                 anchor="w").pack(fill="x", pady=(3, 0))
        if paso.texto:
            self._texto(cuerpo, paso.texto, F["ui"], T.TEXTO_2).pack(anchor="w", pady=(4, 0))
        if paso.matriz:
            self._vista_matriz(cuerpo, paso).pack(anchor="w", pady=(10, 0))
        if paso.nota:
            self._texto(cuerpo, paso.nota, F["mono_s"], T.TEXTO).pack(anchor="w", pady=(10, 0))

    def _copiar(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self._texto_copia)
        self.btn_copiar.set_texto("Copiado")
        self.root.after(1500, lambda: self.btn_copiar.winfo_exists() and self.btn_copiar.set_texto("Copiar"))


def main():
    if sys.platform == "win32":                 # texto nítido en pantallas de alta resolución
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk()
    CalculadoraMatricesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()