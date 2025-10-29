from gurobipy import Model, GRB, quicksum
from typing import Dict, Any, Iterable


##importa los parametros desde excel o desde el modulo de python
# try to read params from Excel first
from excel import read_params_from_excel, write_solution_to_excel
params = read_params_from_excel("parametros_reales.xlsx")
if not params:
    # fallback to python module if excel read failed
    from parametrosReales import params as params_module
    params = params_module



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
    L = m.addVars(I_days, name="L", lb=0.0)                                # Lt
    I = m.addVars(I_tail, I_days, name="I", lb=0.0)                        # I_{k,t}
    Bk = m.addVars(I_tail, I_days, name="B", lb=0.0)                       # B_{k,t}
    D = m.addVars(I_days, name="D", lb=0.0)                                # D_t
    Tkt = m.addVars(I_tail, I_days, name="T", lb=0.0)                      # T_{k,t}
    E = m.addVars(I_days, name="E", lb=0.0)                                # E_t
    y = m.addVars(I_tail, I_days, vtype=GRB.BINARY, name="y")              # y_{k,t}

    # Producción y ventas
    x = m.addVars(I_prod, I_days, name="x", lb=0.0)                         # x_{i,t}
    IM = m.addVars(I_prod, I_days, name="IM", lb=0.0)                       # IM_{i,t}
    H_in = m.addVars(I_prod, I_days, name="H_in", lb=0.0)                   # H_{i,t} (dentro demanda)
    h_over = m.addVars(I_prod, I_days, name="h_over", lb=0.0)               # h_{i,t} (sobre demanda)
    z = m.addVars(I_prod, I_days, vtype=GRB.BINARY, name="z")               # z_{i,t}

    # Emisiones
    V = m.addVars(I_days, name="V", lb=0.0)                                 # V_t (exceso diario, no negativo)
    R = m.addVar(vtype=GRB.BINARY, name="R")                                # R (paga multa)

    # Flujo de caja
    A = m.addVars(I_days, name="A", lb=-GRB.INFINITY)                       # A_t (puede ser real, sin cota)

    # === Restricciones ===
    # 1. Embalse: L_t = L_{t-1} + sum_k B_{k,t} + E_t - D_t
    m.addConstr(L[1] == params["L0"] + quicksum(Bk[k,1] for k in I_tail) + E[1] - D[1], name="bal_L_t1")
    for t in range(2, T+1):
        m.addConstr(L[t] == L[t-1] + quicksum(Bk[k,t] for k in I_tail) + E[t] - D[t], name=f"bal_L_{t}")

    # 2. Relaves: I_{k,t} = I_{k,t-1} + T_{k,t} - B_{k,t}
    for k in I_tail:
        m.addConstr(I[k,1] == params["I0"][k] + Tkt[k,1] - Bk[k,1], name=f"bal_I_{k}_t1")
        for t in range(2, T+1):
            m.addConstr(I[k,t] == I[k,t-1] + Tkt[k,t] - Bk[k,t], name=f"bal_I_{k}_{t}")

    # 3. Agua usada en faenas: D_t = sum_i x_{i,t} * a_i
    for t in I_days:
        m.addConstr(D[t] == quicksum(x[i,t] * params["a"][i] for i in I_prod), name=f"agua_faena_{t}")

    # 4. Capacidades min y max de producción
    for i in I_prod:
        for t in I_days:
            m.addConstr(x[i,t] >= params["Jmin"][i], name=f"xmin_{i}_{t}")
            m.addConstr(x[i,t] <= params["Jmax"][i], name=f"xmax_{i}_{t}")

    # 5. Capacidad máxima embalse: 0 <= L_t <= Vmax  (no negatividad ya en lb=0)
    for t in I_days:
        m.addConstr(L[t] <= params["Vmax"], name=f"cap_embalse_{t}")

    # 6. Capacidad máxima relave: 0 <= I_{k,t} <= Hmax_k
    for k in I_tail:
        for t in I_days:
            m.addConstr(I[k,t] <= params["Hmax"][k], name=f"cap_relave_{k}_{t}")

    # 7. Caudales y bombeo
    for k in I_tail:
        for t in I_days:
            m.addConstr(Tkt[k,t] == params["F"][k] * quicksum(x[i,t]*params["a"][i] for i in I_prod), name=f"T_def_{k}_{t}")
            m.addConstr(Bk[k,t] <= y[k,t] * params["Qmax"][k], name=f"B_Qmax_{k}_{t}")
            m.addConstr(Bk[k,t] <= I[k,t], name=f"B_le_I_{k}_{t}")

    # 8. Agua externa: E_t = D_t - sum_k B_{k,t}
    for t in I_days:
        m.addConstr(E[t] == D[t] - quicksum(Bk[k,t] for k in I_tail), name=f"E_def_{t}")

    # 9. Demanda y disponibilidad para ventas
    for i in I_prod:
        for t in I_days:
            m.addConstr(H_in[i,t] <= params["d"][i,t], name=f"H_in_le_d_{i}_{t}")
            # H_in + h_over ≤ IM_{i,t-1} + x_{i,t}
            if t == 1:
                # IM_{i,0} no está definido en el texto; usamos IM[i,1] vía restricción 14.
                # Aquí seguimos la fórmula del documento literalmente: usamos IM[i,0] + x[i,1].
                # Para mantener consistencia, igualamos IM[i,0] a 0 implícitamente (no definido en el texto).
                # Alternativamente, se puede pasar IM0[i] en params; si existe, úsese.
                IM0i = params.get("IM0", {}).get(i, 0.0)
                m.addConstr(H_in[i,t] + h_over[i,t] <= IM0i + x[i,t], name=f"ventas_disp_{i}_{t}")
            else:
                m.addConstr(H_in[i,t] + h_over[i,t] <= IM[i,t-1] + x[i,t], name=f"ventas_disp_{i}_{t}")

    # 10. Presupuesto máximo para bombas y agua externa (diario)
    for t in I_days:
        term_bombas = quicksum(params["C"][k]*Bk[k,t] + params["f"][k]*y[k,t] for k in I_tail)
        m.addConstr(term_bombas + params["P"]*E[t] <= params["Pmax"], name=f"presupuesto_{t}")
    
    # 11. Exceso de emisiones diario (V_t = emisiones_diarias - umbral_diario)
    for t in I_days:
        m.addConstr(V[t] >= quicksum(x[i,t]*params["w"][i] for i in I_prod) - params["B"], name=f"V_def_{t}")

    # 12. Multa por exceso de emisiones (uso de M grande para activar R)
    for t in I_days:
        m.addConstr(V[t] <= params["Mbig"] * R, name=f"V_le_MR_{t}")

    # 13. Ventas dentro/sobre demanda
    for i in I_prod:
        for t in I_days:
            m.addConstr(H_in[i,t] <= params["d"][i,t], name=f"H_in_d_{i}_{t}")
            m.addConstr(h_over[i,t] <= params["Mbig"] * z[i,t], name=f"hover_le_Mz_{i}_{t}")
            # El documento usa I_{i,t}; aquí se usa IM[i,t]
            m.addConstr(h_over[i,t] + H_in[i,t] <= IM[i,t], name=f"ventas_le_IM_{i}_{t}")

    # 14. Inventario del producto i
    for i in I_prod:
        # IM_{i,1} = x_{i,1} - h_{i,1} - H_{i,1}
        m.addConstr(IM[i,1] == x[i,1] - h_over[i,1] - H_in[i,1], name=f"IM_init_{i}")
        for t in range(2, T+1):
            m.addConstr(IM[i,t] == IM[i,t-1] + x[i,t] - h_over[i,t] - H_in[i,t], name=f"IM_flow_{i}_{t}")
    for t in I_days:
        m.addConstr(quicksum(IM[i,t]*params["n"][i] for i in I_prod) <= params["N"], name=f"cap_almacen_{t}")

    # 15. Flujo neto de caja diario
    for t in I_days:
        ventas_normales = quicksum(H_in[i,t]*params["g"][i] for i in I_prod)
        ventas_extra = quicksum(h_over[i,t]*params["u"][i] for i in I_prod)
        costo_inv = quicksum(IM[i,t]*params["m"][i] for i in I_prod)
        costo_bombas = quicksum(params["C"][k]*Bk[k,t] + params["f"][k]*y[k,t] for k in I_tail)
        costo_agua_ext = params["P"]*E[t]
        costo_prod = quicksum(x[i,t]*params["c"][i] for i in I_prod)
        multa = params["mu"] * V[t]
        m.addConstr(A[t] == ventas_normales + ventas_extra - costo_inv - costo_bombas - costo_agua_ext - costo_prod - multa,
                    name=f"flujo_caja_{t}")

    # === Función Objetivo ===
    m.setObjective(quicksum(A[t] for t in I_days), GRB.MAXIMIZE)

    return m


if __name__ == "__main__":


    def print_solution(m):
        """Imprime el objetivo (si está) y el valor de todas las variables encontradas en la solución."""
        # intentar obtener número de soluciones
        try:
            sol_count = int(m.SolCount)
        except Exception:
            sol_count = 0

        if sol_count == 0 and m.status != GRB.OPTIMAL:
            print("No se encontró solución (SolCount=0). Estado del modelo:", m.status)
            return

        # Imprimir objetivo cuando esté disponible
        try:
            print("\nObjetivo:", m.objVal)
        except Exception:
            try:
                print("\nObjetivo (atributo ObjVal):", m.getAttr("ObjVal"))
            except Exception:
                pass

        # Imprimir variables ordenadas por nombre
        vars_list = list(m.getVars())
        vars_list.sort(key=lambda v: v.VarName)

        print("\nValores de variables (nombre: valor):")
        for v in vars_list:
            try:
                val = v.X
            except Exception:
                try:
                    val = v.getAttr("X")
                except Exception:
                    val = None

            if val is None:
                # no hay valor disponible para esta variable en la solución
                continue

            # mostrar enteros/binaries como enteros si están cerca de un entero
            try:
                vtype = v.VType
            except Exception:
                vtype = None

            if vtype in (GRB.BINARY, GRB.INTEGER) or abs(val - round(val)) < 1e-6:
                print(f"{v.VarName}: {int(round(val))}")
            else:
                print(f"{v.VarName}: {float(val):.6f}")


    model = build_model(params)
    # model.Params.OutputFlag = 0  # Silenciar salida si se desea
    model.optimize()
    
    # Impresión rápida de valor objetivo (si el modelo es factible)
    if model.status == GRB.OPTIMAL:
        #print_solution(model)
        print("Z* =", model.objVal)
        # Export to Excel if helper is available
        if write_solution_to_excel is not None:
            try:
                write_solution_to_excel(model, filename="solution.xlsx", include_zeros=False)
            except Exception as e:
                print("Warning: could not write solution to Excel:", e)
        