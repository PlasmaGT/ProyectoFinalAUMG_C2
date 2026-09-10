# Por: Manuel Sicajau

import tkinter as tk
from tkinter import messagebox, ttk
import numpy as np

# ============================================================================
# Configuración y Constantes de Diseño
# ============================================================================
WINDOW_TITLE = "Calculadora Avanzada de Matrices"
WINDOW_GEOMETRY = "1100x750"
WINDOW_MIN_SIZE = (1024, 700)

COLOR_BG_PRINCIPAL = "#090d16"
COLOR_BG_PANEL = "#131b2e"
COLOR_BG_ELEVATED = "#1e293b"
COLOR_TEXTO_PRINCIPAL = "#f8fafc"
COLOR_TEXTO_SECUNDARIO = "#94a3b8"
COLOR_ACENTO = "#6366f1"
COLOR_ACENTO_HOVER = "#4f46e5"
COLOR_ENTRADA_BG = "#1a233a"
COLOR_ENTRADA_FG = "#ffffff"
COLOR_BORDE = "#2a3650"
COLOR_RESET = "#f43f5e"
COLOR_RESET_HOVER = "#e11d48"
COLOR_RESULTADO_BG = "#0f172a"
COLOR_RESULTADO_FG = "#38bdf8"

FONT_FAMILIA = "Segoe UI"
FONT_TITULO = (FONT_FAMILIA, 16, "bold")
FONT_SUBTITULO = (FONT_FAMILIA, 11, "bold")
FONT_NORMAL = (FONT_FAMILIA, 10)
FONT_SMALL = (FONT_FAMILIA, 9)

PADDING_X = 24
PADDING_Y = 20
MATRIZ_MAX = 6


class CalculadoraMatricesApp:
    # Nuevas operaciones agregadas
    OPERACIONES = [
        "Suma (+)", "Resta (-)", "Multiplicación (x)",
        "Inversa (A^-1)", "Determinante (|A|)",
        "Matriz de cofactores (C)", "Gauss-Jordan"
    ]

    def __init__(self, root: tk.Tk):
        self.root = root
        self._configurar_ventana()
        self._crear_widgets()
        self.construir_grids()

    def _configurar_ventana(self):
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_GEOMETRY)
        self.root.minsize(*WINDOW_MIN_SIZE)
        self.root.configure(bg=COLOR_BG_PRINCIPAL)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=COLOR_BG_PRINCIPAL, foreground=COLOR_TEXTO_PRINCIPAL)
        style.configure("TLabelFrame", background=COLOR_BG_PANEL, bordercolor=COLOR_BORDE, relief="solid",
                        borderwidth=1)
        style.configure("TLabelFrame.Label", background=COLOR_BG_PANEL, foreground="#818cf8", font=FONT_SUBTITULO)
        style.configure("TLabel", background=COLOR_BG_PANEL, foreground=COLOR_TEXTO_PRINCIPAL, font=FONT_NORMAL)

        style.configure("TButton", background=COLOR_ACENTO, foreground="#ffffff", font=FONT_NORMAL, borderwidth=0,
                        focusthickness=2, focuscolor=COLOR_ACENTO)
        style.map("TButton", background=[("active", COLOR_ACENTO_HOVER), ("pressed", COLOR_ACENTO_HOVER)])

        style.configure("Reset.TButton", background=COLOR_RESET, foreground="#ffffff", font=FONT_NORMAL, borderwidth=0)
        style.map("Reset.TButton", background=[("active", COLOR_RESET_HOVER), ("pressed", COLOR_RESET_HOVER)])

        style.configure("TCombobox", fieldbackground=COLOR_ENTRADA_BG, background=COLOR_BG_PANEL,
                        foreground=COLOR_ENTRADA_FG, arrowcolor=COLOR_TEXTO_PRINCIPAL)
        style.configure("TSpinbox", fieldbackground=COLOR_ENTRADA_BG, background=COLOR_BG_PANEL,
                        foreground=COLOR_ENTRADA_FG)
        style.configure("TScrollbar", background=COLOR_BG_PANEL, troughcolor=COLOR_BG_PRINCIPAL,
                        bordercolor=COLOR_BG_PANEL, arrowcolor=COLOR_TEXTO_PRINCIPAL)

    def _crear_widgets(self):
        main_frame = tk.Frame(self.root, bg=COLOR_BG_PRINCIPAL)
        main_frame.pack(fill="both", expand=True, padx=PADDING_X, pady=PADDING_Y)

        # Header
        header_frame = tk.Frame(main_frame, bg=COLOR_BG_PRINCIPAL)
        header_frame.pack(fill="x", pady=(0, 15))

        tk.Label(header_frame, text="Calculadora Avanzada de Matrices", font=FONT_TITULO, fg=COLOR_TEXTO_PRINCIPAL,
                 bg=COLOR_BG_PRINCIPAL).pack(side="left")
        tk.Label(header_frame, text="Versión 26.9.5", font=FONT_SMALL, fg=COLOR_TEXTO_SECUNDARIO,
                 bg=COLOR_BG_PRINCIPAL).pack(side="right", anchor="s")

        columns_container = tk.Frame(main_frame, bg=COLOR_BG_PRINCIPAL)
        columns_container.pack(fill="both", expand=True)

        # Columna Izquierda
        col_izquierda = tk.Frame(columns_container, bg=COLOR_BG_PRINCIPAL)
        col_izquierda.pack(side="left", fill="y", padx=(0, 15))

        self._crear_selector_operacion(col_izquierda)
        self._crear_selector_dimensiones(col_izquierda)

        acciones_frame = tk.Frame(col_izquierda, bg=COLOR_BG_PRINCIPAL)
        acciones_frame.pack(fill="x", pady=(10, 0))

        self.btn_generar = ttk.Button(acciones_frame, text="Generar Campos de Matrices", command=self.construir_grids)
        self.btn_generar.pack(fill="x", pady=(0, 8), ipady=6)

        self.btn_reset = ttk.Button(acciones_frame, text="Restablecer / Limpiar", style="Reset.TButton",
                                    command=self.restablecer_todo)
        self.btn_reset.pack(fill="x", ipady=6)

        # Columna Derecha
        col_derecha = tk.Frame(columns_container, bg=COLOR_BG_PRINCIPAL)
        col_derecha.pack(side="right", fill="both", expand=True)

        self.frame_grids = self._crear_contenedor_canvas(col_derecha, " 3. Inserción de Datos ", 180)
        self.scrollable_frame = self.frame_grids.scrollable_frame

        self.btn_calcular = ttk.Button(col_derecha, text="Calcular Resultado", command=self.calcular)
        self.btn_calcular.pack(fill="x", pady=12, ipady=8)

        self.frame_resultado = self._crear_contenedor_canvas(col_derecha, " 4. Resultado ", 150)
        self.scrollable_resultado_frame = self.frame_resultado.scrollable_frame

    def _crear_selector_operacion(self, parent):
        frame = ttk.LabelFrame(parent, text=" 1. Operación Matriz ", padding=15)
        frame.pack(fill="x", pady=(0, 12))

        self.op_var = tk.StringVar(value=self.OPERACIONES[0])
        self.combo_op = ttk.Combobox(frame, textvariable=self.op_var, values=self.OPERACIONES, state="readonly",
                                     font=FONT_NORMAL)
        self.combo_op.pack(fill="x")
        self.combo_op.bind("<<ComboboxSelected>>", self.actualizar_vistas)

    def _crear_selector_dimensiones(self, parent):
        frame = ttk.LabelFrame(parent, text=" 2. Dimensiones ", padding=15)
        frame.pack(fill="x", pady=(0, 12))

        inner = tk.Frame(frame, bg=COLOR_BG_PANEL)
        inner.pack(fill="x", expand=True)
        inner.columnconfigure(1, weight=1)

        self.rows_a, self.cols_a = self._crear_bloque_dimensiones(inner, "Matriz A", 0)

        sep = tk.Frame(inner, bg=COLOR_BORDE, height=1)
        sep.grid(row=3, column=0, columnspan=2, sticky="ew", pady=12)

        self.rows_b, self.cols_b = self._crear_bloque_dimensiones(inner, "Matriz B", 4)

    def _crear_bloque_dimensiones(self, parent, titulo: str, start_row: int):
        tk.Label(parent, text=titulo, font=FONT_SUBTITULO, bg=COLOR_BG_PANEL, fg="#818cf8").grid(row=start_row,
                                                                                                 column=0, columnspan=2,
                                                                                                 sticky="w",
                                                                                                 pady=(0, 6))

        tk.Label(parent, text="Filas:", bg=COLOR_BG_PANEL, fg=COLOR_TEXTO_SECUNDARIO).grid(row=start_row + 1, column=0,
                                                                                           sticky="w", padx=(0, 8),
                                                                                           pady=3)
        rows = self._crear_spinbox(parent)
        rows.grid(row=start_row + 1, column=1, sticky="w", pady=3)

        tk.Label(parent, text="Cols:", bg=COLOR_BG_PANEL, fg=COLOR_TEXTO_SECUNDARIO).grid(row=start_row + 2, column=0,
                                                                                          sticky="w", padx=(0, 8),
                                                                                          pady=3)
        cols = self._crear_spinbox(parent)
        cols.grid(row=start_row + 2, column=1, sticky="w", pady=3)

        return rows, cols

    def _crear_spinbox(self, contenedor):
        spinbox = ttk.Spinbox(
            contenedor, from_=1, to=MATRIZ_MAX, width=6, font=FONT_NORMAL,
            validate="key", validatecommand=(self.root.register(self.validar_solo_numeros), "%P")
        )
        spinbox.set(2)
        return spinbox

    def _crear_contenedor_canvas(self, parent, titulo, height):
        frame = ttk.LabelFrame(parent, text=titulo, padding=12)
        frame.pack(fill="both", expand=True, pady=(0, 5))

        canvas = tk.Canvas(frame, bg=COLOR_BG_PANEL, height=height, highlightthickness=0)
        scrollable_frame = tk.Frame(canvas, bg=COLOR_BG_PANEL)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        if titulo.strip().startswith("3"):
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        else:
            canvas.pack(side="left", fill="both", expand=True)

        frame.scrollable_frame = scrollable_frame
        return frame

    def restablecer_todo(self):
        self.op_var.set(self.OPERACIONES[0])
        for spin in (self.rows_a, self.cols_a, self.rows_b, self.cols_b):
            spin.set(2)
        self.actualizar_vistas()
        self._limpiar_contenedor(self.scrollable_resultado_frame)

    def actualizar_vistas(self, event=None):
        op = self.op_var.get()
        # Se deshabilita la Matriz B si es una operación unitaria
        es_unitaria = any(x in op for x in ["Inversa", "Determinante", "cofactores", "Gauss-Jordan"])
        estado = "disabled" if es_unitaria else "normal"
        self.rows_b.config(state=estado)
        self.cols_b.config(state=estado)
        self.construir_grids()

    def validar_solo_numeros(self, texto: str) -> bool:
        if texto == "" or texto.lstrip('-').replace('.', '', 1).isdigit():
            return True
        self.root.bell()
        return False

    def _obtener_dimension(self, widget, nombre: str):
        valor = widget.get().strip()
        if not valor:
            messagebox.showerror("Error de Dimensión", f"El campo '{nombre}' está vacío.")
            return None
        try:
            num = int(valor)
        except ValueError:
            messagebox.showerror("Error de Dimensión", f"El campo '{nombre}' acepta solo números enteros.")
            return None
        if not (1 <= num <= MATRIZ_MAX):
            messagebox.showerror("Error de Dimensión", f"El campo '{nombre}' debe estar entre 1 y {MATRIZ_MAX}.")
            return None
        return num

    def _limpiar_contenedor(self, contenedor):
        for widget in contenedor.winfo_children():
            widget.destroy()

    def construir_grids(self):
        self._limpiar_contenedor(self.scrollable_frame)

        op = self.op_var.get()
        ra = self._obtener_dimension(self.rows_a, "Matriz A - Filas") or 2
        ca = self._obtener_dimension(self.cols_a, "Matriz A - Columnas") or 2
        self.entries_a = self._crear_grilla("Matriz A", ra, ca)

        es_unitaria = any(x in op for x in ["Inversa", "Determinante", "cofactores", "Gauss-Jordan"])
        if not es_unitaria:
            rb = self._obtener_dimension(self.rows_b, "Matriz B - Filas") or 2
            cb = self._obtener_dimension(self.cols_b, "Matriz B - Columnas") or 2
            self.entries_b = self._crear_grilla("Matriz B", rb, cb)

    def _crear_grilla(self, titulo: str, filas: int, columnas: int):
        sub = tk.LabelFrame(
            self.scrollable_frame, text=f" {titulo} ", font=FONT_SMALL,
            bg=COLOR_BG_ELEVATED, fg=COLOR_TEXTO_PRINCIPAL, bd=1, relief="solid", padx=10, pady=10
        )
        sub.pack(side="left", padx=12, anchor="n")

        entries = []
        for i in range(filas):
            fila = []
            for j in range(columnas):
                e = tk.Entry(
                    sub, width=6, font=FONT_NORMAL, justify="center",
                    bg=COLOR_ENTRADA_BG, fg=COLOR_ENTRADA_FG, insertbackground=COLOR_TEXTO_PRINCIPAL,
                    relief="solid", bd=1
                )
                e.grid(row=i, column=j, padx=4, pady=4, ipady=4)
                e.insert(0, "0")
                fila.append(e)
            entries.append(fila)
        return entries

    def leer_matriz(self, entries):
        return np.array([[float(celda.get().strip() or "0") for celda in fila] for fila in entries])

    def calcular(self):
        op = self.op_var.get()
        try:
            A = self.leer_matriz(self.entries_a)
            # Enrutamiento de las nuevas operaciones
            if "Inversa" in op:
                self._calcular_inversa(A)
            elif "Determinante" in op:
                self._calcular_determinante(A)
            elif "cofactores" in op:
                self._calcular_cofactores(A)
            elif "Gauss-Jordan" in op:
                self._calcular_gauss_jordan(A)
            else:
                B = self.leer_matriz(self.entries_b)
                self._calcular_binaria(op, A, B)
        except ValueError:
            messagebox.showerror("Error de Datos", "Ingrese únicamente números válidos en las casillas.")

    def _calcular_inversa(self, A):
        if A.shape[0] != A.shape[1]:
            messagebox.showerror("Error de Dimensión", f"La matriz A de tamaño {A.shape} no es cuadrada.")
            return
        try:
            resultado = np.linalg.inv(A)
            self._mostrar_resultado_matriz(resultado)
        except np.linalg.LinAlgError:
            messagebox.showerror("Error Matemático", "La matriz es singular (determinante 0) y no tiene inversa.")

    def _calcular_determinante(self, A):
        if A.shape[0] != A.shape[1]:
            messagebox.showerror("Error de Dimensión", "Para calcular el determinante, la matriz debe ser cuadrada.")
            return
        det = np.linalg.det(A)
        # Se envuelve el resultado en un array 2D para mantener compatibilidad gráfica
        self._mostrar_resultado_matriz(np.array([[det]]))

    def _calcular_cofactores(self, A):
        if A.shape[0] != A.shape[1]:
            messagebox.showerror("Error de Dimensión", "Para la matriz de cofactores, la matriz debe ser cuadrada.")
            return
        cofactores = np.zeros_like(A, dtype=float)
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                menor = np.delete(np.delete(A, i, 0), j, 1)
                det_menor = np.linalg.det(menor) if menor.size > 0 else 1
                cofactores[i, j] = ((-1)**(i+j)) * det_menor
        self._mostrar_resultado_matriz(cofactores)

    def _calcular_gauss_jordan(self, A):
        M = A.astype(float)
        filas, columnas = M.shape
        lead = 0
        for r in range(filas):
            if lead >= columnas:
                break
            i = r
            while M[i, lead] == 0:
                i += 1
                if i == filas:
                    i = r
                    lead += 1
                    if lead == columnas:
                        break
            if lead < columnas:
                # Intercambio de filas si es necesario
                M[[i, r]] = M[[r, i]]
                lv = M[r, lead]
                if lv != 0:
                    M[r] = M[r] / lv
                for i in range(filas):
                    if i != r:
                        lv = M[i, lead]
                        M[i] = M[i] - lv * M[r]
            lead += 1
        self._mostrar_resultado_matriz(M)

    def _calcular_binaria(self, op, A, B):
        if "Suma" in op:
            self._operar_matrices(A, B, lambda x, y: x + y, "sumar")
        elif "Resta" in op:
            self._operar_matrices(A, B, lambda x, y: x - y, "restar")
        elif "Multiplicación" in op:
            if A.shape[1] != B.shape[0]:
                messagebox.showerror("Error de Dimensiones",
                                     f"Columnas de A ({A.shape[1]}) deben coincidir con filas de B ({B.shape[0]}).")
                return
            self._mostrar_resultado_matriz(np.dot(A, B))

    def _operar_matrices(self, A, B, funcion, verbo):
        if A.shape != B.shape:
            messagebox.showerror("Error de Dimensiones",
                                 f"Para {verbo}, las dimensiones deben coincidir.\nA: {A.shape} vs B: {B.shape}")
            return
        self._mostrar_resultado_matriz(funcion(A, B))

    def _mostrar_resultado_matriz(self, res):
        self._limpiar_contenedor(self.scrollable_resultado_frame)

        filas, columnas = res.shape
        for i in range(filas):
            for j in range(columnas):
                val = res[i, j]
                # Evita notación científica en cero exacto
                if abs(val) < 1e-10:
                    val = 0.0
                val_str = str(int(val)) if val == int(val) else f"{val:.4f}"

                e = tk.Entry(
                    self.scrollable_resultado_frame, width=8, font=FONT_NORMAL, justify="center",
                    bg=COLOR_RESULTADO_BG, fg=COLOR_RESULTADO_FG, relief="solid", bd=1,
                    state="readonly", readonlybackground=COLOR_RESULTADO_BG
                )
                e.config(state="normal")
                e.insert(0, val_str)
                e.config(state="readonly")
                e.grid(row=i, column=j, padx=4, pady=4, ipady=4)


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculadoraMatricesApp(root)
    root.mainloop()