from gurobipy import Model, GRB, quicksum
from typing import Dict, Any, Iterable


# Importar los parametros desde excel
# Para que funcione, se debe tener instalada la libreria openpyxl y XlsxWriter
# Tambien al ejecutar el main.py los excel deben estar cerrados
from excel import read_params_from_excel, write_solution_to_excel
params = read_params_from_excel("parametros_reales.xlsx")

# Tipos para claridad
Index = Iterable[int]


def build_model(params: Dict[str, Any]):
    # === Conjuntos ===
    T = params["T"]
    I_days = range(1, T + 1)            # t ∈ {1,…,T}
    I_prod = range(1, params["M"] + 1)  # i ∈ {1,…,M}
    I_tail = range(1, params["K"] + 1)  # k ∈ {1,…,K}

    # === Modelo ===
    m = Model("relaves_minimizacion_agua")

    # === Variables ===
    # Agua y operaciones hídricas
    L = m.addVars(I_days, name="L", lb=0.0)                                # L_t
    I = m.addVars(I_tail, I_days, name="I", lb=0.0)                        # I_{k,t}
    G = m.addVars(I_tail, I_days, name="G", lb=0.0)                        # G_{k,t}
    D = m.addVars(I_days, name="D", lb=0.0)                                # D_t
    U = m.addVars(I_tail, I_days, name="U", lb=0.0)                        # U_{k,t}
    E = m.addVars(I_days, name="E", lb=0.0)                                # E_t
    Q = m.addVars(I_days, vtype=GRB.BINARY, name="Q")                      # Q_{t}
    y = m.addVars(I_tail, I_days, vtype=GRB.BINARY, name="y")              # y_{k,t}

    # Producción y ventas
    x = m.addVars(I_prod, I_days, name="x", lb=0.0)                         # x_{i,t}
    IM = m.addVars(I_prod, I_days, name="IM", lb=0.0)                       # IM_{i,t}
    S = m.addVars(I_prod, I_days, name="S", lb=0.0)                         # S_{i,t} (dentro demanda)
    So = m.addVars(I_prod, I_days, name="So", lb=0.0)                       # So_{i,t} (sobre demanda)
    bwt = m.addVars(I_days, vtype=GRB.CONTINUOUS, name="bwt")               # costo extra por bombeo externo


    # Emisiones
    V = m.addVar(name="V", lb=0.0)                                          # V (exceso anual, no negativo)
    R = m.addVar(vtype=GRB.BINARY, name="R")                                # R (paga multa)

    # Flujo de caja
    A = m.addVars(I_days, name="A", lb=-GRB.INFINITY)                       # A_t (puede ser real, sin cota)

    # === Restricciones ===
    # 1. Embalse: L_t = L_{t-1} + sum_k G_{k,t} + E_t - D_t
    m.addConstr(L[1] == params["L0"] + quicksum(G[k,1] for k in I_tail) + E[1] - D[1], name="bal_L_t1")
    for t in range(2, T+1):
        m.addConstr(L[t] == L[t-1] + quicksum(G[k,t] for k in I_tail) + E[t] - D[t], name=f"bal_L_{t}")

    # 2. Relaves: I_{k,t} = I_{k,t-1} + U_{k,t} - G_{k,t}
    for k in I_tail:
        m.addConstr(I[k,1] == params["I0"][k] + U[k,1] - G[k,1], name=f"bal_I_{k}_t1")
        for t in range(2, T+1):
            m.addConstr(I[k,t] == I[k,t-1] + U[k,t] - G[k,t], name=f"bal_I_{k}_{t}")

    # 3. Agua usada en faenas: D_t = sum_i x_{i,t} * a_i
    for t in I_days:
        m.addConstr(D[t] == quicksum(x[i,t] * params["a"][i] for i in I_prod), name=f"agua_faena_{t}")

    # 4. Capacidades min y max de producción
    for i in I_prod:
        for t in I_days:
            m.addConstr(x[i,t] >= params["Jmin"][i], name=f"xmin_{i}_{t}")
            m.addConstr(x[i,t] <= params["Jmax"][i], name=f"xmax_{i}_{t}")

    # 5. Capacidad máxima embalse: L_t <= Vmax  (no negatividad ya en lb=0)
    for t in I_days:
        m.addConstr(L[t] <= params["Vmax"], name=f"cap_embalse_{t}")

    # 6. Capacidad máxima relave: I_{k,t} <= Hmax_k
    for k in I_tail:
        for t in I_days:
            m.addConstr(I[k,t] <= params["Hmax"][k], name=f"cap_relave_{k}_{t}")

    # 7. Caudales y bombeo
    for k in I_tail:
        for t in I_days:
            m.addConstr(U[k,t] == params["F"][k] * quicksum(x[i,t]*params["a"][i] for i in I_prod), name=f"T_def_{k}_{t}")
            m.addConstr(G[k,t] <= y[k,t] * params["Qmax"][k], name=f"B_Qmax_{k}_{t}")

    # 8. Bombeo de Aguas Externas
    for t in I_days:
        m.addConstr(E[t] <= params["Mbig"] * Q[t], name=f"Q_le_MQ_{t}")

    # 9. Satisfacción de demanda
    for i in I_prod:
        for t in I_days:
            m.addConstr(S[i,t] <= params["d"][i,t], name=f"H_in_le_d_{i}_{t}")

    # 10. Presupuesto máximo para bombas y agua externa (diario)
    for t in I_days:
        term_bombas = quicksum(params["Cv"][k]*G[k,t] + params["Cf"][k]*y[k,t] for k in I_tail)
        m.addConstr(term_bombas + params["P"]*E[t] <= params["Pmax"], name=f"presupuesto_{t}")
    
    # 11. Exceso de emisiones diario (V >= emisiones_diarias - umbral_diario)
    for t in I_days:
        m.addConstr(V >= quicksum(x[i,t]*params["w"][i] for i in I_prod) - params["B"], name=f"V_def_{t}")

    # 12. Multa por exceso de emisiones (uso de M grande para activar R)
    for t in I_days:
        m.addConstr(V <= params["Mbig"] * R, name=f"V_le_MR_{t}")

    # 13. Inventario del producto i
    for i in I_prod:
        # IM_{i,1} = x_{i,1} - So_{i,1} - S_{i,1}
        m.addConstr(IM[i,1] == params["IM0"][i] + x[i,1] - So[i,1] - S[i,1], name=f"IM_init_{i}")
        for t in range(2, T+1):
            m.addConstr(IM[i,t] == IM[i,t-1] + x[i,t] - So[i,t] - S[i,t], name=f"IM_flow_{i}_{t}")
    for t in I_days:
        m.addConstr(quicksum(IM[i,t]*params["n"][i] for i in I_prod) <= params["N"], name=f"cap_almacen_{t}")

    # 14. Flujo neto de caja diario
    for t in I_days:
        ventas_normales = quicksum(S[i,t]*params["g"][i] for i in I_prod)
        ventas_extra = quicksum(So[i,t]*params["u"][i] for i in I_prod)
        costo_inv = quicksum(IM[i,t]*params["Ca"][i] for i in I_prod)
        costo_bombas = quicksum(params["Cv"][k]*G[k,t] + params["Cf"][k]*y[k,t] for k in I_tail)
        costo_agua_ext = params["P"]*E[t] + params["Pf"]*Q[t]
        costo_prod = quicksum(x[i,t]*params["Cp"][i] for i in I_prod)
        m.addConstr(A[t] == ventas_normales + ventas_extra - costo_inv - costo_bombas - costo_agua_ext - costo_prod,
                    name=f"flujo_caja_{t}")


    for t in I_days:
        m.addConstr(
            bwt[t] == params["cw"] * quicksum(G[k,t] for k in I_tail),
            name=f"beneficio_recirculacion_{t}"
        )


    # === Función Objetivo ===
    m.setObjective(quicksum(A[t]+bwt[t] for t in I_days) - (params["mv"] * V + params["mf"] * R), GRB.MAXIMIZE)

    return m

if __name__ == "__main__":

    model = build_model(params)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        print("Z* =", model.objVal)
        print("GAP =", model.MIPGap)

        # Exportador a Excel
        if write_solution_to_excel is not None:
            try:
                write_solution_to_excel(model, filename="solution.xlsx", include_zeros=True)
            except Exception as e:
                print("Warning: could not write solution to Excel:", e)