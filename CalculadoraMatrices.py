import tkinter as tk
from tkinter import messagebox, ttk
import numpy as np

# ============================================================================
# Configuración y Constantes de Diseño
# ============================================================================
WINDOW_TITLE = "Calculadora Avanzada de Matrices"
WINDOW_GEOMETRY = "1150x800"
WINDOW_MIN_SIZE = (1024, 750)

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
MATRIZ_MAX = 8


class CalculadoraMatricesApp:
    OPERACIONES = [
        "Suma (+)", "Resta (-)", "Multiplicación (x)",
        "Inversa (A^-1)", "Determinante (|A|)",
        "Matriz de cofactores (C)", "Gauss-Jordan"
    ]

    def __init__(self, root: tk.Tk):
        self.root = root
        self._configurar_ventana()
        self._crear_widgets()
        self.actualizar_vistas()

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
        style.configure("TButton", background=COLOR_ACENTO, foreground="#ffffff", font=FONT_NORMAL, borderwidth=0)
        style.map("TButton", background=[("active", COLOR_ACENTO_HOVER)])
        style.configure("Reset.TButton", background=COLOR_RESET)
        style.map("Reset.TButton", background=[("active", COLOR_RESET_HOVER)])
        style.configure("TCombobox", fieldbackground=COLOR_ENTRADA_BG, background=COLOR_BG_PANEL,
                        foreground=COLOR_ENTRADA_FG)
        style.configure("TSpinbox", fieldbackground=COLOR_ENTRADA_BG, background=COLOR_BG_PANEL,
                        foreground=COLOR_ENTRADA_FG)
        style.configure("TCheckbutton", background=COLOR_BG_PANEL, foreground=COLOR_TEXTO_PRINCIPAL)
        style.map("TCheckbutton", background=[("active", COLOR_BG_PANEL)])

    def _crear_widgets(self):
        main_frame = tk.Frame(self.root, bg=COLOR_BG_PRINCIPAL)
        main_frame.pack(fill="both", expand=True, padx=PADDING_X, pady=PADDING_Y)

        # Header
        header_frame = tk.Frame(main_frame, bg=COLOR_BG_PRINCIPAL)
        header_frame.pack(fill="x", pady=(0, 15))
        tk.Label(header_frame, text="Calculadora Avanzada de Matrices (Paso a Paso)", font=FONT_TITULO,
                 fg=COLOR_TEXTO_PRINCIPAL, bg=COLOR_BG_PRINCIPAL).pack(side="left")

        columns_container = tk.Frame(main_frame, bg=COLOR_BG_PRINCIPAL)
        columns_container.pack(fill="both", expand=True)

        # Columna Izquierda
        col_izquierda = tk.Frame(columns_container, bg=COLOR_BG_PRINCIPAL, width=320)
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

        self.frame_resultado = self._crear_contenedor_canvas(col_derecha, " 4. Procedimiento y Resultado ", 250)
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

        # --- OPCIONES PREDEFINIDAS ---
        preset_frame = tk.Frame(frame, bg=COLOR_BG_PANEL)
        preset_frame.pack(fill="x", pady=(0, 10))

        self.usar_preset_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(preset_frame, text="Fijar a matrices de:", variable=self.usar_preset_var,
                              command=self.actualizar_vistas)
        chk.pack(side="left", padx=(0, 5))

        self.combo_preset = ttk.Combobox(preset_frame, values=["3x3", "4x4", "5x5", "6x6"], state="readonly", width=5)
        self.combo_preset.current(0)
        self.combo_preset.pack(side="left")
        self.combo_preset.bind("<<ComboboxSelected>>", self.actualizar_vistas)
        # -----------------------------

        inner = tk.Frame(frame, bg=COLOR_BG_PANEL)
        inner.pack(fill="x", expand=True)
        inner.columnconfigure(1, weight=1)

        self.rows_a_var = tk.StringVar(value="2")
        self.cols_a_var = tk.StringVar(value="2")
        self.rows_a, self.cols_a = self._crear_bloque_dimensiones(inner, "Matriz A", 0, self.rows_a_var,
                                                                  self.cols_a_var)

        # Vincular actualización de filas A a columnas A en caso manual de Gauss
        self.rows_a_var.trace_add("write", lambda *args: self._forzar_reglas_matematicas())

        sep = tk.Frame(inner, bg=COLOR_BORDE, height=1)
        sep.grid(row=3, column=0, columnspan=2, sticky="ew", pady=12)

        self.rows_b_var = tk.StringVar(value="2")
        self.cols_b_var = tk.StringVar(value="2")
        self.rows_b, self.cols_b = self._crear_bloque_dimensiones(inner, "Matriz B", 4, self.rows_b_var,
                                                                  self.cols_b_var)

    def _crear_bloque_dimensiones(self, parent, titulo: str, start_row: int, var_rows, var_cols):
        tk.Label(parent, text=titulo, font=FONT_SUBTITULO, bg=COLOR_BG_PANEL, fg="#818cf8").grid(row=start_row,
                                                                                                 column=0, columnspan=2,
                                                                                                 sticky="w",
                                                                                                 pady=(0, 6))

        tk.Label(parent, text="Filas:", bg=COLOR_BG_PANEL, fg=COLOR_TEXTO_SECUNDARIO).grid(row=start_row + 1, column=0,
                                                                                           sticky="w", padx=(0, 8),
                                                                                           pady=3)
        rows = ttk.Spinbox(parent, from_=1, to=MATRIZ_MAX, width=6, font=FONT_NORMAL, textvariable=var_rows,
                           validate="key", validatecommand=(self.root.register(self.validar_solo_numeros), "%P"))
        rows.grid(row=start_row + 1, column=1, sticky="w", pady=3)

        tk.Label(parent, text="Cols:", bg=COLOR_BG_PANEL, fg=COLOR_TEXTO_SECUNDARIO).grid(row=start_row + 2, column=0,
                                                                                          sticky="w", padx=(0, 8),
                                                                                          pady=3)
        cols = ttk.Spinbox(parent, from_=1, to=MATRIZ_MAX, width=6, font=FONT_NORMAL, textvariable=var_cols,
                           validate="key", validatecommand=(self.root.register(self.validar_solo_numeros), "%P"))
        cols.grid(row=start_row + 2, column=1, sticky="w", pady=3)

        return rows, cols

    def _crear_contenedor_canvas(self, parent, titulo, height):
        frame = ttk.LabelFrame(parent, text=titulo, padding=12)
        frame.pack(fill="both", expand=True, pady=(0, 5))

        canvas = tk.Canvas(frame, bg=COLOR_BG_PANEL, height=height, highlightthickness=0)
        scrollable_frame = tk.Frame(canvas, bg=COLOR_BG_PANEL)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Scroll horizontal para los procedimientos largos
        h_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=h_scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")

        frame.scrollable_frame = scrollable_frame
        return frame

    def restablecer_todo(self):
        self.op_var.set(self.OPERACIONES[0])
        self.usar_preset_var.set(False)
        self.rows_a_var.set("2");
        self.cols_a_var.set("2")
        self.rows_b_var.set("2");
        self.cols_b_var.set("2")
        self.actualizar_vistas()
        self._limpiar_contenedor(self.scrollable_resultado_frame)

    def _forzar_reglas_matematicas(self):
        """Aplica las reglas sobre las dimensiones basado en la operación elegida."""
        op = self.op_var.get()
        es_unitaria = any(x in op for x in ["Inversa", "Determinante", "cofactores", "Gauss-Jordan"])

        # Bloquear matriz B si no se requiere
        estado_b = "disabled" if es_unitaria else "normal"
        self.rows_b.config(state=estado_b)
        self.cols_b.config(state=estado_b)

        if self.usar_preset_var.get():
            # MODO PREDEFINIDO ACTIVO
            self.combo_preset.config(state="readonly")
            n_str = self.combo_preset.get().split('x')[0]
            n = int(n_str)

            self.rows_a.config(state="normal");
            self.rows_a_var.set(str(n));
            self.rows_a.config(state="disabled")
            if "Gauss-Jordan" in op:
                self.cols_a.config(state="normal");
                self.cols_a_var.set(str(n + 1));
                self.cols_a.config(state="disabled")
            else:
                self.cols_a.config(state="normal");
                self.cols_a_var.set(str(n));
                self.cols_a.config(state="disabled")

            if not es_unitaria:
                self.rows_b.config(state="normal");
                self.rows_b_var.set(str(n));
                self.rows_b.config(state="disabled")
                self.cols_b.config(state="normal");
                self.cols_b_var.set(str(n));
                self.cols_b.config(state="disabled")
        else:
            # MODO MANUAL
            self.combo_preset.config(state="disabled")
            self.rows_a.config(state="normal")

            if "Gauss-Jordan" in op:
                # Regla de Gauss-Jordan (Columnas = Filas + 1)
                filas_a = self.rows_a_var.get()
                if filas_a.isdigit():
                    self.cols_a.config(state="normal")
                    self.cols_a_var.set(str(int(filas_a) + 1))
                self.cols_a.config(state="disabled")
            elif any(x in op for x in ["Inversa", "Determinante", "cofactores"]):
                # Matrices Cuadradas
                filas_a = self.rows_a_var.get()
                if filas_a.isdigit():
                    self.cols_a.config(state="normal")
                    self.cols_a_var.set(filas_a)
                self.cols_a.config(state="disabled")
            else:
                self.cols_a.config(state="normal")

    def actualizar_vistas(self, event=None):
        self._forzar_reglas_matematicas()
        self.construir_grids()

    def validar_solo_numeros(self, texto: str) -> bool:
        if texto == "" or texto.lstrip('-').replace('.', '', 1).isdigit():
            return True
        self.root.bell()
        return False

    def _obtener_dimension(self, variable, nombre: str):
        valor = variable.get().strip()
        if not valor: return None
        try:
            return int(valor)
        except ValueError:
            return None

    def _limpiar_contenedor(self, contenedor):
        for widget in contenedor.winfo_children():
            widget.destroy()

    def construir_grids(self):
        self._limpiar_contenedor(self.scrollable_frame)
        op = self.op_var.get()
        ra = self._obtener_dimension(self.rows_a_var, "Matriz A - Filas") or 2
        ca = self._obtener_dimension(self.cols_a_var, "Matriz A - Columnas") or 2
        self.entries_a = self._crear_grilla("Matriz A", ra, ca)

        es_unitaria = any(x in op for x in ["Inversa", "Determinante", "cofactores", "Gauss-Jordan"])
        if not es_unitaria:
            rb = self._obtener_dimension(self.rows_b_var, "Matriz B - Filas") or 2
            cb = self._obtener_dimension(self.cols_b_var, "Matriz B - Columnas") or 2
            self.entries_b = self._crear_grilla("Matriz B", rb, cb)

    def _crear_grilla(self, titulo: str, filas: int, columnas: int):
        sub = tk.LabelFrame(self.scrollable_frame, text=f" {titulo} ", font=FONT_SMALL, bg=COLOR_BG_ELEVATED,
                            fg=COLOR_TEXTO_PRINCIPAL, bd=1, relief="solid", padx=10, pady=10)
        sub.pack(side="left", padx=12, anchor="n")
        entries = []
        for i in range(filas):
            fila = []
            for j in range(columnas):
                e = tk.Entry(sub, width=6, font=FONT_NORMAL, justify="center", bg=COLOR_ENTRADA_BG, fg=COLOR_ENTRADA_FG,
                             insertbackground=COLOR_TEXTO_PRINCIPAL, relief="solid", bd=1)
                e.grid(row=i, column=j, padx=4, pady=4, ipady=4)
                e.insert(0, "0")
                fila.append(e)
            entries.append(fila)
        return entries

    def leer_matriz(self, entries):
        return np.array([[float(celda.get().strip() or "0") for celda in fila] for fila in entries])

    def _fmt(self, num):
        if abs(num) < 1e-10: num = 0.0
        return str(int(num)) if num == int(num) else f"{num:.2f}"

    def calcular(self):
        op = self.op_var.get()
        try:
            A = self.leer_matriz(self.entries_a)
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
            messagebox.showerror("Error de Datos", "Ingrese únicamente números válidos.")

    # =====================================================================
    # PROCEDIMIENTOS MATEMÁTICOS (PASO A PASO)
    # =====================================================================
    def _calcular_binaria(self, op, A, B):
        if A.shape != B.shape and "Multiplicación" not in op:
            messagebox.showerror("Error",
                                 f"Para sumar/restar, las dimensiones deben coincidir.\nA: {A.shape} B: {B.shape}")
            return

        pasos = []
        pasos.append(("Matriz A:", A))
        if not "Multiplicación" in op: pasos.append(("Matriz B:", B))

        if "Suma" in op:
            M_str = [[f"{self._fmt(A[i, j])} + {self._fmt(B[i, j])}" for j in range(A.shape[1])] for i in
                     range(A.shape[0])]
            pasos.append(("Sumando elementos equivalentes:", M_str))
            pasos.append(("Resultado Final:", A + B))

        elif "Resta" in op:
            M_str = [[f"{self._fmt(A[i, j])} - {self._fmt(B[i, j])}" for j in range(A.shape[1])] for i in
                     range(A.shape[0])]
            pasos.append(("Restando elementos equivalentes:", M_str))
            pasos.append(("Resultado Final:", A - B))

        elif "Multiplicación" in op:
            if A.shape[1] != B.shape[0]:
                messagebox.showerror("Error",
                                     f"Las columnas de A ({A.shape[1]}) deben ser igual a las filas de B ({B.shape[0]}).")
                return
            pasos.append(("Matriz B:", B))
            M_str = []
            for i in range(A.shape[0]):
                fila_str = []
                for j in range(B.shape[1]):
                    terms = [f"({self._fmt(A[i, k])} * {self._fmt(B[k, j])})" for k in range(A.shape[1])]
                    fila_str.append(" + ".join(terms))
                M_str.append(fila_str)
            pasos.append(("Multiplicando Fila(A) x Columna(B):", M_str))
            pasos.append(("Resultado Final:", np.dot(A, B)))

        self._mostrar_pasos(pasos)

    def _calcular_determinante(self, A):
        if A.shape[0] != A.shape[1]:
            messagebox.showerror("Error", "La matriz debe ser cuadrada.")
            return
        pasos = [("Matriz Original:", A)]
        n = A.shape[0]
        if n == 1:
            pasos.append(("Resultado:", np.array([[A[0, 0]]])))
        elif n == 2:
            formula = f"({self._fmt(A[0, 0])} * {self._fmt(A[1, 1])}) - ({self._fmt(A[0, 1])} * {self._fmt(A[1, 0])})"
            pasos.append(("Fórmula 2x2 (ad - bc):", formula))
            pasos.append(("Resultado Final:", np.array([[np.linalg.det(A)]])))
        else:
            partes = []
            for j in range(n):
                signo = "+" if j % 2 == 0 else "-"
                partes.append(f"{signo} {self._fmt(A[0, j])} * det(M_1{j + 1})")
            pasos.append(("Expansión por cofactores (Fila 1):", " ".join(partes)))
            pasos.append(("Resultado Final:", np.array([[np.linalg.det(A)]])))
        self._mostrar_pasos(pasos)

    def _calcular_cofactores(self, A):
        if A.shape[0] != A.shape[1]:
            messagebox.showerror("Error", "La matriz debe ser cuadrada.")
            return
        pasos = [("Matriz Original:", A)]
        cofactores = np.zeros_like(A, dtype=float)
        M_str = []
        for i in range(A.shape[0]):
            fila_str = []
            for j in range(A.shape[1]):
                menor = np.delete(np.delete(A, i, 0), j, 1)
                det_menor = np.linalg.det(menor) if menor.size > 0 else 1
                cof = ((-1) ** (i + j)) * det_menor
                cofactores[i, j] = cof
                signo = "+" if (i + j) % 2 == 0 else "-"
                fila_str.append(f"{signo} det(M{i + 1}{j + 1})")
            M_str.append(fila_str)
        pasos.append(("Aplicando cálculo de menores y ley de signos:", M_str))
        pasos.append(("Matriz de Cofactores Final:", cofactores))
        self._mostrar_pasos(pasos)

    def _generar_pasos_gauss(self, matriz_inicial):
        """Motor común de pasos para Gauss-Jordan e Inversa"""
        M = matriz_inicial.astype(float)
        filas, columnas = M.shape
        lead = 0
        pasos = [("Matriz Inicial", M.copy())]

        for r in range(filas):
            if lead >= columnas: break
            i = r
            while M[i, lead] == 0:
                i += 1
                if i == filas:
                    i = r
                    lead += 1
                    if lead == columnas: break
            if lead < columnas:
                if i != r:
                    M[[i, r]] = M[[r, i]]
                    pasos.append((f"Intercambio Fila {r + 1} por Fila {i + 1}", M.copy()))

                lv = M[r, lead]
                if lv != 0 and lv != 1:
                    M[r] = M[r] / lv
                    pasos.append((f"Fila {r + 1} = Fila {r + 1} / {self._fmt(lv)}", M.copy()))

                for idx in range(filas):
                    if idx != r:
                        lv_idx = M[idx, lead]
                        if lv_idx != 0:
                            M[idx] = M[idx] - lv_idx * M[r]
                            signo = "+" if lv_idx < 0 else "-"
                            pasos.append(
                                (f"Fila {idx + 1} = Fila {idx + 1} {signo} ({self._fmt(abs(lv_idx))} * Fila {r + 1})",
                                 M.copy()))
            lead += 1
        return pasos, M

    def _calcular_gauss_jordan(self, A):
        pasos, matriz_final = self._generar_pasos_gauss(A)
        pasos.append(("Matriz Resultante (Forma Escalonada Reducida)", matriz_final))
        self._mostrar_pasos(pasos)

    def _calcular_inversa(self, A):
        n = A.shape[0]
        if n != A.shape[1]:
            messagebox.showerror("Error", "La matriz debe ser cuadrada.")
            return
        if np.linalg.det(A) == 0:
            messagebox.showerror("Error", "La matriz es singular (determinante 0) y no tiene inversa.")
            return

        I = np.eye(n)
        M_aumentada = np.hstack((A, I))  # [ A | I ]

        pasos_gj, M_final = self._generar_pasos_gauss(M_aumentada)

        # Reescribimos el titulo inicial para contexto
        pasos_gj[0] = ("Matriz Aumentada Original [ A | I ]", M_aumentada)

        Inv_result = M_final[:, n:]  # Extraemos solo la parte derecha (la inversa)
        pasos_gj.append(("La Inversa es el lado derecho de la matriz aumentada [ I | A^-1 ]:", Inv_result))
        self._mostrar_pasos(pasos_gj)

    def _mostrar_pasos(self, pasos):
        self._limpiar_contenedor(self.scrollable_resultado_frame)

        for idx, (descripcion, contenido) in enumerate(pasos):
            frame_paso = tk.Frame(self.scrollable_resultado_frame, bg=COLOR_BG_PANEL)
            frame_paso.pack(fill="x", pady=10, padx=12, anchor="w")

            prefijo = f"Paso {idx + 1}: " if len(pasos) > 2 else ""
            lbl = tk.Label(frame_paso, text=f"{prefijo}{descripcion}", font=FONT_SUBTITULO, bg=COLOR_BG_PANEL,
                           fg=COLOR_ACENTO)
            lbl.pack(anchor="w", pady=(0, 6))

            if isinstance(contenido, str):
                lbl_txt = tk.Label(frame_paso, text=contenido, font=FONT_NORMAL, bg=COLOR_BG_PANEL,
                                   fg=COLOR_TEXTO_PRINCIPAL, justify="left")
                lbl_txt.pack(anchor="w", padx=10)
            else:
                frame_matriz = tk.Frame(frame_paso, bg=COLOR_BG_PANEL)
                frame_matriz.pack(anchor="w", padx=10)

                is_numpy = isinstance(contenido, np.ndarray)
                filas = contenido.shape[0] if is_numpy else len(contenido)
                columnas = contenido.shape[1] if is_numpy else (len(contenido[0]) if filas > 0 else 0)

                for i in range(filas):
                    for j in range(columnas):
                        if is_numpy:
                            val_str = self._fmt(contenido[i, j])
                            w = 8
                        else:
                            val_str = contenido[i][j]
                            # Ancho adaptativo basado en la longitud de la cadena para la ecuación
                            w = max(8, len(val_str) + 2)

                        # Usar Entry readonly funciona bien como celda de display adaptable
                        e = tk.Entry(frame_matriz, width=w, font=FONT_NORMAL, justify="center", bg=COLOR_RESULTADO_BG,
                                     fg=COLOR_RESULTADO_FG, relief="solid", bd=1)
                        e.insert(0, val_str)
                        e.config(state="readonly", readonlybackground=COLOR_RESULTADO_BG)
                        e.grid(row=i, column=j, padx=2, pady=2, ipady=3)


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculadoraMatricesApp(root)
    root.mainloop()