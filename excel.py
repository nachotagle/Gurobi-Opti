from typing import Optional
import pandas as pd
import pandas as pd

def read_params_from_excel(filename: str = "parametros_reales.xlsx", **kwargs):
    try:
        xl = pd.ExcelFile(filename)
    except Exception as e:
        print("openpyxl is required to read Excel files. Install with: pip install openpyxl")
        return {}

    # ---- Escalares ----
    esc = pd.read_excel(filename, sheet_name="Escalares")
    scal = {str(r["Parámetro"]).strip(): r["Valor"] for _, r in esc.iterrows()}

    T   = int(scal["T"])
    M   = int(scal["M"])
    K   = int(scal["K"])
    Vmax= float(scal["Vmax"])
    L0  = float(scal["L0"])
    B   = float(scal.get("B", 0.0))
    m   = float(scal.get("m", 0.0))
    P   = float(scal.get("P", 0.0))
    Pmax= float(scal.get("Pmax", 1e9))
    N   = float(scal.get("N", 1e12))

    # ---- PorProducto ----
    prod = pd.read_excel(filename, sheet_name="PorProducto")
    prod.columns = [str(c).strip() for c in prod.columns]
    def to_map(col):
        return {int(r["Producto"]): float(r[col]) for _, r in prod.iterrows()}
    a   = to_map("a (m³ agua/ton)")
    w   = to_map("w (ton SO2/ton)")
    g   = to_map("g (US$/ton)")
    u   = to_map("u (US$/ton)")
    Cp  = to_map("Cp (US$/ton)")
    Ca  = to_map("Ca (US$/ton·día)")
    n   = to_map("n (m³/ton)")
    Jmin= to_map("Jmin (ton/día)")
    Jmax= to_map("Jmax (ton/día)")
    IM0 = to_map("IM0 (ton)")

    # ---- PorRelave ----
    rel = pd.read_excel(filename, sheet_name="PorRelave")
    rel.columns = [str(c).strip() for c in rel.columns]
    def to_map_tail(col):
        return {int(r["Relave"]): float(r[col]) for _, r in rel.iterrows()}
    F   = to_map_tail("F (fracción de agua)")
    Qmax= to_map_tail("Qmax (m³)")
    Hmax= to_map_tail("Hmax (m³)")
    I0  = to_map_tail("I0 (m³)")
    Cv  = to_map_tail("Cv (US$/m³)")
    Cf  = to_map_tail("Cf (US$)")

    # ---- Demanda (formato ancho: columnas Prod1, Prod2, ...) ----
    d = {}
    if "Demanda" in xl.sheet_names:
        dem = pd.read_excel(filename, sheet_name="Demanda")
        dem.columns = [str(c).strip() for c in dem.columns]    
        if "Dia" in dem.columns:
            for _, row in dem.iterrows():
                t = int(row["Dia"])
                for c in dem.columns:
                    if c.lower().startswith("prod"):
                        i = int(c.replace("Prod", "").strip())
                        val = float(row[c])
                        d[(i, t)] = val

    if not d:
        # fallback: demanda no restrictiva
        I_prod = range(1, M+1); I_days = range(1, T+1)
        for i in I_prod:
            for t in I_days:
                d[(i,t)] = 2.0 * Jmax[i]

    # ---- Big-M razonable para ventas
    Mbig = max((N / max(n[i], 1e-9)) + Jmax[i] for i in range(1, M+1))

    print(f"[Excel] Cargado: T={T}, M={M}, K={K} | hojas={xl.sheet_names}")
    return {
        "T": T, "M": M, "K": K,
        "Vmax": Vmax, "L0": L0, "B": B, "m": m, "P": P, "Pmax": Pmax, "N": N,
        "a": a, "w": w, "g": g, "u": u, "Cp": Cp, "Ca": Ca, "n": n, "Jmin": Jmin, "Jmax": Jmax, "IM0": IM0,
        "F": F, "Qmax": Qmax, "Hmax": Hmax, "I0": I0, "Cv": Cv, "Cf": Cf,
        "d": d, "Mbig": Mbig
    }

def write_solution_to_excel(m, filename: str = "solution.xlsx", include_zeros: bool = True, sheet_name: str = "Solution"):
	import xlsxwriter#libreria para crear excel
	
	parsed = {}  
	max_day = 0

	for v in m.getVars():
		name = v.VarName
		if "[" in name and name.endswith("]"):
			base, idxs = name.split("[", 1)
			idxs = idxs[:-1]
			parts = [p.strip() for p in idxs.split(",")]
			indices = []
			for p in parts:
				try:
					indices.append(int(p))
				except Exception:
					indices.append(p)
			key = tuple(indices)
		else:
			base = name
			key = tuple()

		val = None
		try:
			val = v.X
		except Exception:
			try:
				val = v.getAttr("X")
			except Exception:
				val = None

		if val is None:
			continue
		if not include_zeros and abs(val) < 1e-12:
			continue

		parsed.setdefault(base, {})[key] = val
		if len(key) >= 1 and isinstance(key[-1], int):
			if key[-1] > max_day:
				max_day = key[-1]

	if max_day == 0:
		try:
			wb = xlsxwriter.Workbook(filename)
			ws = wb.add_worksheet(sheet_name)
		except Exception as e:
			print("No se pudo crear el excel", e)
			return

		status = getattr(m, "status", None)
		try:
			obj = m.objVal
		except Exception:
			try:
				obj = m.getAttr("ObjVal")
			except Exception:
				obj = None

		ws.write(0, 0, "Z*")
		ws.write(0, 1, obj if obj is not None else "(n/a)")
		ws.write(1, 0, "Model status:")
		ws.write(1, 1, str(status))

		start_row = 3
		ws.write(start_row, 0, "Variable")
		for j, base in enumerate(sorted(parsed.keys()), start=1):
			ws.write(start_row, j, base)

		for j, base in enumerate(sorted(parsed.keys()), start=1):
			vals = parsed[base]
			if vals:
				first = next(iter(vals.values()))
				ws.write(start_row + 1, j, first)

		try:
			wb.close()
			print(f"Solucion en {filename}")
		except Exception as e:
			print("No se pudo guardar", e)
		return

	columns = [] 
	for base, table in parsed.items():
		prefixes = set()
		has_day = False
		for k in table.keys():
			if len(k) >= 1 and isinstance(k[-1], int):
				has_day = True
				prefixes.add(k[:-1])
			else:
				
				prefixes.add(k)
		if has_day:
			for p in sorted(prefixes):
				columns.append((base, p))

	# crea el archivo Excel
	try:
		wb = xlsxwriter.Workbook(filename)
		ws = wb.add_worksheet(sheet_name)
	except Exception as e:
		print("No se pudo crear el excel", e)
		return

	
	status = getattr(m, "status", None)
	try:
		obj = m.objVal
	except Exception:
		try:
			obj = m.getAttr("ObjVal")
		except Exception:
			obj = None

	ws.write(0, 0, "Z*")
	ws.write(0, 1, obj if obj is not None else "(n/a)")
	ws.write(1, 0, "Model status:")
	ws.write(1, 1, str(status))


	status = getattr(m, "status", None)
	try:
		obj = m.objVal
	except Exception:
		try:
			obj = m.getAttr("ObjVal")
		except Exception:
			obj = None

	try:
		gap = m.MIPGap
	except Exception:
		try:
			gap = m.getAttr("MIPGap")
		except Exception:
			gap = None

	ws.write(0, 0, "Z*")
	ws.write(0, 1, obj if obj is not None else "(n/a)")
	ws.write(1, 0, "Model status:")
	ws.write(1, 1, str(status))
	ws.write(2, 0, "GAP:")
	ws.write(2, 1, gap if gap is not None else "(n/a)")

	start_row = 3
	ws.write(start_row, 0, "Day")
	for j, (base, pk) in enumerate(columns, start=1):
		if pk == ():
			colname = base
		else:
			colname = base + "_" + "_".join(str(x) for x in pk)
		ws.write(start_row, j, colname)

	for day in range(1, max_day + 1):
		ws.write(start_row + day, 0, day)
		for j, (base, pk) in enumerate(columns, start=1):
			key = pk + (day,) if pk != () else (day,)
			val = parsed.get(base, {}).get(key, None)
			if val is None:
				continue
			if abs(val - round(val)) < 1e-9:
				ws.write(start_row + day, j, int(round(val)))
			else:
				ws.write(start_row + day, j, float(val))

	try:
		wb.close()
		print(f"Solucion en {filename}")
	except Exception as e:
		print("No se pudo guardar", e)

