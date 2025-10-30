# parametros_reales.py
# Parámetros reales extraídos del informe Datos_E3.pdf

T = 365  # días
M = 2    # productos (1: Cu, 2: Fe)
K = 2    # relaves

I_days = range(1, T+1)
I_prod = range(1, M+1)
I_tail = range(1, K+1)

# m³ de agua fresca usados en faena al producir una ton del producto i
a = {1: 116.9, 2: 28.6}

# cantidad de contaminante SO2 por ton de producto (emisiones)
w = {1: 0.0756, 2: 0.0017}

# Precios de venta "en planta" (US$/ton producto)
g = {1: 11002, 2: 105.56} # Normal
u = {1: 11002, 2: 105.56} # Por sobre demanda (Por ahora igual)

# Costos de producción (US$/ton producto) e almacenaje (US$/ton·día)
Cp = {1: 4585.6, 2: 50.9}   # Costo de producción
Ca = {1: 0.001392, 2: 0.03104} # Costo de almacenaje

# Volumen por ton en bodega (m³/ton)
n = {1: 0.348, 2: 0.776}

# Límites de producción diarios (ton/día de producto)
Jmin = {1: 784.9, 2: 3534.34}
Jmax = {1: 1569.8, 2: 7068.68}

di = {1: 1412.82, 2: 6361.81}
d = {(i, t): di[i] for i in I_prod for t in I_days}  # Demanda suficiente (no restrictiva)

# Fracción de agua a cada relave
F = {1: 0.3, 2: 0.4}

# Capacidad maxima de transporte de agua desde relaves (m³)
Qmax = {1: 136272, 2: 136272}

# Capacidad maxima de almacenamiento de agua de cada relave (m³)
Hmax = {1: 1643000000, 2: 790000}

# Cantidad inicial de agua por relave (m³)
I0 = {1: 1363690000, 2: 655700}

# Costo variable y fijo por m³ bombeado desde relave (US$/m³) — energía/opex
Cv = {1: 32.7, 2: 10.9}   # Costo variable
Cf = {1: 69.9, 2: 75.3}   # Costo fijo

# Capacidad maxima de almacenamiento de agua en el embalse (m³)
Vmax = 6000000

# Almacenamiento inicial de agua en embalse (m³)
L0 = 4290000

# Costo y presupuesto del bombeo de agua externa (US$/m³ y US$/día)
P = 5.45      # Costo agua externa
Pmax = 1e7   # Presupuesto máximo diario

# Umbra de emisiones diarias permitidas (ton SO2/año)
B = 110 * 365

# Multa por exceso de emisiones (US$/ton SO2)
m = 0

# Maximo de almacenamiento en inventario de productos (ton)
N = 1e6

# Inventario inicial por producto (ton)
IM0 = {1: 0, 2: 0}

Mbig = 1e6


params = {
    "T": T, "M": M, "K": K,
    "Vmax": Vmax, "P": P, "Pmax": Pmax, "N": N, "Mbig": Mbig,
    "L0": L0, "m": m,
    "Hmax": Hmax, "Qmax": Qmax, "Cv": Cv, "Cf": Cf, "F": F, "I0": I0,
    "a": a, "w": w, "g": g, "u": u, "n": n, "Ca": Ca, "Cp": Cp,
    "Jmin": Jmin, "Jmax": Jmax, "d": d,
    "B": B,
    "IM0": IM0,
}
