"""
plot_precedence_graph.py
========================
Genera il grafo delle precedenze dei task (T1..T40) del caso Assembly Line
Balancing usando Graphviz, a partire dai dati nel file Excel.

Riusa le funzioni di `alb_helpers.py` (load_tasks, build_dicts,
topological_order) per leggere i dati e verificare che il grafo sia aciclico
prima di disegnarlo.

Uso:
    python plot_precedence_graph.py
    python plot_precedence_graph.py --xlsx tabella_attivita_tempo_standard_MOST.xlsx \
                                    --out grafo_precedenze --fmt png --rankdir LR

Richiede:
    pip install graphviz   +   binario Graphviz (brew install graphviz)
"""

import argparse
import sys

from graphviz import Digraph

from alb_helpers import (
    load_tasks,
    build_dicts,
    topological_order,
    task_num,
)

# File Excel di default con la tabella attività/tempi/precedenze
XLSX_DEFAULT = "tabella_attivita_tempo_standard_MOST.xlsx"


def build_graph(predecessors, times=None, rankdir="LR", show_time=True,
                fmt="png"):
    """Costruisce l'oggetto Digraph del grafo delle precedenze.

    `predecessors` : {task -> [predecessori immediati]}
    `times`        : {task -> tempo}  (opzionale, mostrato dentro il nodo)
    `rankdir`      : 'LR' (orizzontale, come il disegno a mano) o 'TB'
    `show_time`    : se True ed esiste `times`, scrive il tempo nel nodo
    """
    g = Digraph("precedenze", format=fmt)
    # `pad` aggiunge un bordo bianco attorno a tutto il disegno (in pollici):
    # "0.3,0.6" -> 0.3" ai lati, 0.6" sopra/sotto, così gli archi che salgono
    # in alto (es. T13) non restano attaccati al margine superiore.
    g.attr(rankdir=rankdir, splines="spline", nodesep="0.35", ranksep="0.7",
           pad="0.3,0.6", fontname="Helvetica")
    g.attr("node", shape="ellipse", style="filled", fillcolor="white",
           color="black", fontname="Helvetica")
    g.attr("edge", color="black", arrowsize="0.8")

    # nodi in ordine naturale (T1, T2, ... T40)
    for t in sorted(predecessors, key=task_num):
        if times and show_time:
            label = f"{t}\n{times[t]}s"
        else:
            label = t
        g.node(t, label=label)

    # archi: predecessore -> task
    for t, preds in predecessors.items():
        for p in preds:
            g.edge(p, t)

    return g


def main():
    ap = argparse.ArgumentParser(description="Plot del grafo delle precedenze ALB")
    ap.add_argument("--xlsx", default=XLSX_DEFAULT,
                    help="file Excel con la tabella dei task")
    ap.add_argument("--out", default="grafo_precedenze",
                    help="nome del file di output (senza estensione)")
    ap.add_argument("--fmt", default="png", choices=["png", "pdf", "svg"],
                    help="formato di output")
    ap.add_argument("--rankdir", default="LR", choices=["LR", "TB"],
                    help="direzione del layout (LR=orizzontale, TB=verticale)")
    ap.add_argument("--no-time", action="store_true",
                    help="non mostrare il tempo dentro i nodi")
    args = ap.parse_args()

    # 1. Lettura dati e costruzione dizionari
    df = load_tasks(args.xlsx)
    times, predecessors, successors = build_dicts(df)
    print(f"Caricati {len(times)} task da '{args.xlsx}'.")

    # 2. Verifica di aciclicità (Kahn): se c'è un ciclo si ferma qui
    try:
        order = topological_order(times, predecessors)
        print(f"Grafo aciclico OK. Ordine topologico: {' -> '.join(order)}")
    except ValueError as e:
        print(f"ERRORE: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Costruzione e rendering del grafo
    g = build_graph(predecessors, times=times, rankdir=args.rankdir,
                    show_time=not args.no_time, fmt=args.fmt)
    out_path = g.render(args.out, cleanup=True)
    print(f"Grafo salvato in: {out_path}")


if __name__ == "__main__":
    main()
