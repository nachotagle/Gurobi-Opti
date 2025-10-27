# -*- coding: utf-8 -*-
"""
Parámetros ARTIFICIALES de prueba para el modelo de relaves.
Coloca este archivo en el mismo directorio que `modelo_gurobi_relaves.py`.
"""

# Dimensiones
T = 20  # días
M = 3   # productos
K = 2   # relaves

# Conjuntos explícitos (opcionales, solo para claridad si alguien imprime)
I_days = range(1, T+1)
I_prod = range(1, M+1)
I_tail = range(1, K+1)

# Coeficientes de agua por producto (m^3 por unidad producida)
a = {1: 1.2, 2: 0.8, 3: 1.6}

# Emisiones por unidad (ton CO2e por unidad producida)
w = {1: 0.020, 2: 0.030, 3: 0.015}

# Precios de venta (normal) y sobre-demanda
# u < g para reflejar descuento por ventas adicionales

g = {1: 100.0, 2: 90.0, 3: 110.0}
u = {1: 85.0, 2: 78.0, 3: 95.0}

# Costos de producción e inventario
c = {1: 20.0, 2: 16.0, 3: 22.0}
m = {1: 0.20, 2: 0.20, 3: 0.20}

# Volumen por unidad en bodega (para la restricción de capacidad N)
n = {1: 1.0, 2: 1.0, 3: 1.0}

# Límites de producción diarios
Jmin = {1: 40.0, 2: 35.0, 3: 45.0}
Jmax = {1: 100.0, 2: 90.0, 3: 110.0}

# Demanda amplia para no restringir (puedes reemplazar por series reales)
d = {(i, t): Jmax[i] * 2 for i in I_prod for t in I_days}

# Parámetros de relaves
F = {1: 0.20, 2: 0.25}   # fracción de D_t que va a cada relave
Qmax = {1: 1e6, 2: 1e6}  # caudal máximo bombeo desde cada relave
Hmax = {1: 1e7, 2: 1e7}  # capacidad de cada relave
I0 = {1: 0.0, 2: 0.0}    # inventario inicial de agua en relaves
C = {1: 0.10, 2: 0.12}   # costo por m^3 bombeado
activacion_fija = {1: 0.0, 2: 0.0}  # costo fijo por activar bomba (y)

# Embalse y agua externa
Vmax = 1e7   # capacidad máxima del embalse
L0 = 0.0     # agua inicial en embalse
P = 0.25     # costo por m^3 de agua externa
Pmax = 1e12  # presupuesto diario (alto para no activar)

# Emisiones (umbral anual) y penalidad
B = 0.0    # umbral; lo ponemos 0 para simplificar la prueba
mu = 0.0   # multa por excedente diario (apagada en demo)

# Capacidad de almacenamiento total
N = 1e9

# Big-M para activaciones
Mbig = 1e6

# Parámetros opcionales: inventarios iniciales por producto en t=0
IM0 = {1: 0.0, 2: 0.0, 3: 0.0}

# === Diccionario principal ===
params = {
    "T": T, "M": M, "K": K,
    "Vmax": Vmax, "P": P, "Pmax": Pmax, "N": N, "Mbig": Mbig,
    "L0": L0, "mu": mu,
    "Hmax": Hmax, "Qmax": Qmax, "C": C, "f": activacion_fija, "F": F, "I0": I0,
    "a": a, "w": w, "g": g, "u": u, "n": n, "m": m, "c": c,
    "Jmin": Jmin, "Jmax": Jmax, "d": d,
    "B": B,
    "IM0": IM0,
}
