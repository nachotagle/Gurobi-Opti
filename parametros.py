#productos:
#1:anotar nombre para facilidad
#2:anotar nombre para facilidad
#3:anotar nombre para facilidad

# Dimensiones
T = 365  # días
M = 3    # productos (1: Cu conc, 2: Mo conc, 3: Au conc)
K = 2    # relaves

I_days = range(1, T+1)
I_prod = range(1, M+1)
I_tail = range(1, K+1)

# m³ de agua fresca por t de producto
# ~30–40 m3/t conc Cu (ver supuestos); Mo y Au similares o algo mayores
a = {1: 34.0, 2: 40.0, 3: 36.0}

# tCO2e por t de producto (inferencia desde 4.6 tCO2e/t Cu refinado)
w = {1: 1.2, 2: 1.5, 3: 1.3}

# Precios de venta "en planta" (US$/t producto)
g = {1: 4500.0, 2: 9000.0, 3: 6000.0}
# Sobre-demanda con descuento (u < g)
u = {1: 4000.0, 2: 8200.0, 3: 5400.0}

# Costos de producción (US$/t producto) e inventario (US$/t·día)
c = {1: 1200.0, 2: 2000.0, 3: 1500.0}
m = {1: 0.30, 2: 0.30, 3: 0.30}

# Volumen por t en bodega (m³/t, densidad aparente ~1 t/m³)
n = {1: 1.0, 2: 1.0, 3: 1.0}

# Límites de producción diarios (t/día de producto)
# Orden de magnitud para una planta mediana: Cu conc 1500–2500 t/d, Mo 20–40, Au 30–70
Jmin = {1: 1200.0, 2: 15.0, 3: 25.0}
Jmax = {1: 2200.0, 2: 45.0, 3: 70.0}

# Demanda suficiente (no restrictiva)
d = {(i, t): Jmax[i] * 2 for i in I_prod for t in I_days}

# Fracción del agua de proceso a cada relave (suman ≈1)
F = {1: 0.55, 2: 0.45}

# Capacidades y costos hídricos
# Qmax en m³/día de bombeo desde cada relave
Qmax = {1: 200_000.0, 2: 200_000.0}
# Capacidad de cada relave (m³)
Hmax = {1: 3_000_000.0, 2: 3_000_000.0}
# Inventario inicial de agua en relaves (m³)
I0 = {1: 500_000.0, 2: 500_000.0}
# Costo por m³ bombeado desde relave (US$/m³) — energía/opex
C = {1: 0.12, 2: 0.12}
# Costo fijo por activar bomba
activacion_fija = {1: 0.0, 2: 0.0}

# Embalse y agua externa
Vmax = 5_000_000.0   # m³
L0 = 500_000.0       # m³
P = 2.0              # US$/m³ de agua externa (desalada/traída)
Pmax = 5_000_000.0   # US$/día (presupuesto diario)

# Emisiones: umbral anual y multa (US$/tCO2e)
# B es umbral DIARIO en tu modelo (V[t] = sum_i x w - B). Si quieres anual,
# puedes repartir un presupuesto anual entre 365 días:
B_anual = 300_000.0             # tCO2e/año (ejemplo)
B = B_anual / 365.0             # ~ 822 tCO2e/día
mu = 5.0                        # impuesto verde Chile ~5 US$/tCO2e

# Capacidad total de almacenamiento (m³)
N = 2_000_000.0

# Big-M
Mbig = 1e6

# Inventario inicial por producto (t) en t=0 (para tu regla con IM0)
IM0 = {1: 0.0, 2: 0.0, 3: 0.0}

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
