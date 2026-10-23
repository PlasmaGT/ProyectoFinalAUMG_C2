# 🧮 Calculadora de Matrices

Calculadora de matrices de escritorio en Python que muestra el **procedimiento paso a paso**, no solo el resultado. Usa fracciones exactas y no requiere dependencias externas.

## Características

- **7 operaciones:** suma, resta, multiplicación, inversa, determinante, cofactores y Gauss-Jordan
- **Procedimiento explicado** con las matrices intermedias de cada paso
- **Fracciones exactas** (`3/4`), con opción de ver decimales
- **Tema claro y oscuro**
- **Copiar resultado** listo para pegar en Excel
- **Manual integrado** (`F1`)

## Instalación

Requiere Python 3.9+ y Tkinter (incluido en Windows y macOS; en Linux: `sudo apt install python3-tk`).

```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
python CalculadoraMatrices.py
```

## Uso

1. Elige la operación en la barra lateral.
2. Define el tamaño (3×3 a 6×6, o libre hasta 8×8).
3. Escribe los valores: enteros, decimales (`2.5`) o fracciones (`3/4`).
4. Pulsa **Calcular** (`Ctrl + Enter`).

| Tecla | Acción |
|---|---|
| `Enter` | Siguiente celda |
| `↑` `↓` | Moverse entre filas |
| `Ctrl + Enter` | Calcular |
| `F1` | Manual |

## Operaciones

| Operación | Requisito |
|---|---|
| Suma / Resta | Mismo tamaño |
| Multiplicación | Columnas de A = filas de B |
| Inversa | Cuadrada, \|A\| ≠ 0 |
| Determinante | Cuadrada |
| Cofactores | Cuadrada |
| Gauss-Jordan | Matriz aumentada n × (n+1) |

## Uso del motor sin interfaz

```python
from fractions import Fraction
from CalculadoraMatrices import Motor

A = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
resultado, pasos = Motor().resolver("det", A)
print(resultado.valor)  # −2
```