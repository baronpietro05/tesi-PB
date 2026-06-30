"""
alb_helpers.py
==============
Funzioni di supporto per l'Assembly Line Balancing.

Implementa le due euristiche di Assembly Line Balancing:
  - RPW  (Ranked Positional Weight)
  - LCR  (Largest Candidate Rule)

Le funzioni sono pensate per essere importate e richiamate dalle celle del
notebook `assembly_line_balancing.ipynb`.

Parametri del caso studio:
  - Cycle Time            CT = 420 s
  - Work Content (atteso) WC = 1905 s
"""

from collections import deque

import pandas as pd

# Parametri di default del caso studio
CT_DEFAULT = 420   # Cycle Time massimo per stazione [s]
WC_ATTESO = 1905   # Work Content complessivo atteso [s]


# ---------------------------------------------------------------------------
# 1. Lettura e strutturazione dei dati
# ---------------------------------------------------------------------------

def task_num(task):
    """Estrae la parte numerica di un ID task: 'T12' -> 12.

    Serve per ordinare i task in modo *naturale* (T2 prima di T10) ed evitare
    l'ordinamento puramente alfabetico ('T10' < 'T2')."""
    return int(str(task)[1:])


def parse_predecessors(value):
    """Trasforma la cella 'Predecessori' in una lista Python di ID task.

        '-' / '–' / vuoto   -> []
        'T11, T17'          -> ['T11', 'T17']
    """
    if value is None:
        return []
    s = str(value).strip()
    if s in ("", "-", "–", "—", "nan", "None"):
        return []
    # accetta sia la virgola sia il punto e virgola come separatore
    parts = [p.strip() for p in s.replace(";", ",").split(",")]
    return [p for p in parts if p]


def load_tasks(xlsx_path, sheet_name=0):
    """Carica la tabella dei task dal file Excel.

    Restituisce un DataFrame con le colonne:
        Task | Attività | Tempo | Predecessori (lista Python)

    Il foglio ha un titolo in riga 1 e una riga vuota: l'intestazione vera è
    nella terza riga (header=2). Vengono mantenute solo le righe il cui ID
    rispetta il pattern 'T<numero>'.
    """
    raw = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=2)
    raw = raw[raw["ID"].astype(str).str.match(r"^T\d+$", na=False)].copy()

    df = pd.DataFrame({
        "Task": raw["ID"].astype(str).str.strip(),
        "Attività": raw["Attività"].astype(str).str.strip(),
        "Tempo": raw["Tempo standard MOST (s)"].astype(int),
        "Predecessori": raw["Predecessori"].apply(parse_predecessors),
    }).reset_index(drop=True)
    return df


def build_dicts(df):
    """Dai dati tabellari costruisce i tre dizionari di lavoro.

    Ritorna (times, predecessors, successors):
        times        : {task -> tempo}
        predecessors : {task -> [predecessori immediati]}
        successors   : {task -> [successori immediati]}
    """
    times = dict(zip(df["Task"], df["Tempo"]))
    predecessors = {t: list(p) for t, p in zip(df["Task"], df["Predecessori"])}

    successors = {t: [] for t in times}
    for t, preds in predecessors.items():
        for p in preds:
            successors[p].append(t)
    return times, predecessors, successors


# ---------------------------------------------------------------------------
# Verifica di aciclicità: ordinamento topologico (algoritmo di Kahn)
# ---------------------------------------------------------------------------

def topological_order(times, predecessors):
    """Ordinamento topologico dei task (Kahn).

    Solleva ValueError se il grafo delle precedenze contiene un ciclo,
    altrimenti restituisce una lista di task in ordine topologico valido.
    """
    indeg = {t: len(predecessors[t]) for t in times}
    succ = {t: [] for t in times}
    for t, preds in predecessors.items():
        for p in preds:
            succ[p].append(t)

    # coda dei task senza predecessori, ordinata per ID per ottenere un
    # risultato deterministico
    queue = deque(sorted([t for t in times if indeg[t] == 0], key=task_num))
    order = []
    while queue:
        n = queue.popleft()
        order.append(n)
        nuovi = []
        for m in succ[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                nuovi.append(m)
        # reinserimento ordinato -> output deterministico
        for m in sorted(nuovi, key=task_num):
            queue.append(m)

    if len(order) != len(times):
        raise ValueError("Il grafo delle precedenze contiene un ciclo!")
    return order


# ---------------------------------------------------------------------------
# 2. Metodo RPW: pesi posizionali
# ---------------------------------------------------------------------------

def all_successors(task, successors):
    """Insieme di TUTTI i successori diretti e indiretti di `task` (DFS)."""
    seen = set()
    stack = list(successors[task])
    while stack:
        s = stack.pop()
        if s not in seen:
            seen.add(s)
            stack.extend(successors[s])
    return seen


def positional_weights(times, successors):
    """Peso posizionale di ogni task:  PW(i) = t_i + somma dei tempi di tutti
    i successori (diretti e indiretti) di i.  Ritorna un dizionario {task -> PW}."""
    pw = {}
    for t in times:
        succ = all_successors(t, successors)
        pw[t] = times[t] + sum(times[s] for s in succ)
    return pw


def rpw_weight_table(times, successors):
    """Tabella (DataFrame) dei pesi posizionali, ordinata per peso decrescente.

    Colonne: Task | Tempo | Tempo successori | Peso posizionale | N. successori
    """
    pw = positional_weights(times, successors)
    rows = []
    for t in times:
        succ = all_successors(t, successors)
        rows.append({
            "Task": t,
            "Tempo": times[t],
            "Tempo successori": sum(times[s] for s in succ),
            "Peso posizionale": pw[t],
            "N. successori": len(succ),
        })
    df = pd.DataFrame(rows)
    df = df.sort_values(
        by=["Peso posizionale", "Tempo", "Task"],
        ascending=[False, False, True],
        key=lambda col: col.map(task_num) if col.name == "Task" else col,
    ).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rango"
    return df


# ---------------------------------------------------------------------------
# Criteri di ordinamento (priorità) dei task
# ---------------------------------------------------------------------------

def order_rpw(times, pw):
    """Ordine RPW: peso posizionale decrescente.
    Spareggio: tempo decrescente, poi ID crescente (risultato deterministico)."""
    return sorted(times, key=lambda t: (-pw[t], -times[t], task_num(t)))


def order_lcr(times):
    """Ordine LCR: tempo standard decrescente.
    Spareggio: ID crescente (criterio stabile)."""
    return sorted(times, key=lambda t: (-times[t], task_num(t)))


# ---------------------------------------------------------------------------
# 3. Assegnazione dei task alle stazioni (logica condivisa RPW / LCR)
# ---------------------------------------------------------------------------

def assign_stations(order, times, predecessors, CT=CT_DEFAULT):
    """Assegna i task alle stazioni rispettando precedenze e Cycle Time.

    `order` è la lista dei task in ordine di PRIORITÀ (dal più al meno
    prioritario). La logica è identica per RPW e LCR: cambia solo l'ordine
    fornito in input. (La configurazione AS-IS, invece, è un layout fisso dato:
    vedi `ASIS_STATIONS`.)

    Per ogni stazione si inserisce ripetutamente il task più prioritario che:
      * non è già assegnato,
      * ha tutti i predecessori già assegnati o presenti nella stazione corrente
            set(predecessors[task]).issubset(assigned ∪ current),
      * non fa superare il Cycle Time
            station_time + times[task] <= CT.
    Quando nessun task entra più, la stazione si chiude.

    Ritorna una lista di stazioni; ogni stazione è la lista dei task
    nell'ordine di inserimento.
    """
    assigned = set()
    stations = []

    while len(assigned) < len(times):
        current = []
        station_time = 0

        while True:
            placed = False
            for task in order:                      # scansione per priorità
                if task in assigned or task in current:
                    continue
                if not set(predecessors[task]).issubset(assigned.union(current)):
                    continue
                if station_time + times[task] > CT:
                    continue
                # task assegnabile: lo inserisco e ricomincio dalla priorità più alta
                current.append(task)
                station_time += times[task]
                placed = True
                break
            if not placed:
                break

        if not current:
            raise RuntimeError(
                "Impossibile assegnare i task rimanenti: controllare CT e precedenze."
            )
        assigned.update(current)
        stations.append(current)

    return stations


# ---------------------------------------------------------------------------
# Configurazione AS-IS: layout reale della linea (baseline), 6 stazioni fisse
# ---------------------------------------------------------------------------
# La linea AS-IS NON è prodotta da un algoritmo: è il layout attuale, definito
# da blocchi sequenziali di task (non ottimizzati). Viene usata come baseline di
# confronto per misurare il miglioramento ottenuto con RPW e LCR.
ASIS_STATIONS = [
    ["T1",  "T2",  "T3",  "T4",  "T5",  "T6",  "T7",  "T8"],
    ["T9",  "T10", "T11", "T12", "T13", "T14", "T15"],
    ["T16", "T17", "T18", "T19", "T20", "T21", "T22", "T23"],
    ["T24", "T25", "T26", "T27", "T28", "T29", "T30", "T31"],
    ["T32", "T33", "T34", "T35"],
    ["T36", "T37", "T38", "T39", "T40"],
]


def asis_stations():
    """Configurazione AS-IS (copia indipendente delle stazioni predefinite)."""
    return [list(s) for s in ASIS_STATIONS]


# ---------------------------------------------------------------------------
# 4./5. Tabelle delle stazioni e indicatori (KPI)
# ---------------------------------------------------------------------------

def station_table(stations, times, CT=CT_DEFAULT, total_row=True):
    """Tabella per-stazione: task assegnati, tempo stazione, tempo morto,
    saturazione [%]. Se `total_row` è True aggiunge una riga di totale finale."""
    rows = []
    for i, st in enumerate(stations, start=1):
        Ts = sum(times[t] for t in st)
        rows.append({
            "Stazione": f"S{i}",
            "Task assegnati": " – ".join(st),
            "Tempo stazione (s)": Ts,
            "Tempo morto (s)": CT - Ts,
            "Saturazione (%)": round(Ts / CT * 100, 2),
        })
    df = pd.DataFrame(rows)

    if total_row:
        totale = {
            "Stazione": "Totale",
            "Task assegnati": "",
            "Tempo stazione (s)": int(df["Tempo stazione (s)"].sum()),
            "Tempo morto (s)": int(df["Tempo morto (s)"].sum()),
            "Saturazione (%)": "",
        }
        df = pd.concat([df, pd.DataFrame([totale])], ignore_index=True)
    return df


def kpi(stations, times, CT=CT_DEFAULT, WC=None):
    """Indicatori sintetici di una configurazione.

        N            = numero di stazioni
        Idle Time    = N * CT - WC
        Efficienza   = WC / (N * CT)
        Balance Delay = 1 - Efficienza
    """
    N = len(stations)
    if WC is None:
        WC = sum(times.values())
    idle = N * CT - WC
    eff = WC / (N * CT)
    return {
        "Numero stazioni": N,
        "Idle Time (s)": idle,
        "Efficienza": round(eff, 4),
        "Balance Delay": round(1 - eff, 4),
    }


def kpi_comparison(configs, times, CT=CT_DEFAULT, WC=None):
    """Tabella KPI di confronto fra più configurazioni.

    `configs` è un dizionario {nome_metodo -> lista_stazioni}, ad esempio
    {"AS-IS": st_asis, "RPW": st_rpw, "LCR": st_lcr}.
    """
    rows = []
    for nome, stations in configs.items():
        k = kpi(stations, times, CT=CT, WC=WC)
        rows.append({"Metodo": nome, **k})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 6. Esportazione Excel multi-foglio
# ---------------------------------------------------------------------------

def export_excel(path, sheets):
    """Salva un file Excel con più fogli.

    `sheets` è un dizionario {nome_foglio -> DataFrame}. L'indice viene scritto
    solo se ha un nome (es. la tabella RPW indicizzata per 'Rango').
    """
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            write_index = bool(df.index.name)
            df.to_excel(writer, sheet_name=str(name)[:31], index=write_index)
    return path
