# Assembly Line Balancing — RPW & LCR

Implementazione in Python di due euristiche di bilanciamento di una linea di
assemblaggio, applicate a un caso studio di 40 task:

- **RPW** — *Ranked Positional Weight*
- **LCR** — *Largest Candidate Rule*

I risultati delle due euristiche vengono confrontati con la configurazione
attuale della linea (**AS-IS**, il benchmark) tramite gli indicatori di
prestazione (KPI).

**Parametri del caso studio:** Cycle Time `CT = 420 s` · Work Content `WC = 1905 s`.

---

## Contenuto del progetto

| File | Descrizione |
|------|-------------|
| `assembly_line_balancing.ipynb` | Notebook principale: svolge l'intero studio passo-passo |
| `alb_helpers.py` | Modulo con tutte le funzioni di calcolo (lettura dati, pesi posizionali, assegnazione alle stazioni, KPI, export) |
| `plot_precedence_graph.py` | Script che genera il grafo delle precedenze dei task (usa Graphviz) |
| `tabella_attivita_tempo_standard_MOST.xlsx` | Dataset di input: 40 task con tempo standard e predecessori |
| `requirements.txt` | Dipendenze Python |
| `risultati_ALB.xlsx` | Output generato dal notebook (file Excel multi-foglio) |
| `grafo_precedenze.png` | Output generato da `plot_precedence_graph.py` (grafo delle precedenze) |

---

## Requisiti

- **Python 3.9** o superiore
- I pacchetti elencati in `requirements.txt` (`pandas`, `openpyxl`, `ipykernel`)

---

## Setup dell'ambiente

Dal terminale, nella cartella del progetto.

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows**
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> Il progetto include già una cartella `venv/` pronta all'uso: i comandi sopra
> servono per ricrearla da zero su un'altra macchina.

---

## Come eseguire

### Opzione A — VSCode (consigliata)

1. Apri la cartella del progetto in VSCode.
2. Apri `assembly_line_balancing.ipynb`.
3. In alto a destra, **seleziona il kernel** scegliendo l'interprete del venv
   (`venv/bin/python`).
4. Premi **Run All** per eseguire tutte le celle in ordine.

### Opzione B — Jupyter nel browser

```bash
source venv/bin/activate      # su Windows: venv\Scripts\activate
pip install jupyterlab
jupyter lab
```
Apri il notebook dall'interfaccia ed esegui le celle.

---

## Grafo delle precedenze (opzionale)

Lo script `plot_precedence_graph.py` disegna il grafo delle precedenze dei task
e lo salva in `grafo_precedenze.png`. Richiede, oltre al pacchetto `graphviz`
(già in `requirements.txt`), il **binario Graphviz di sistema**:

```bash
# macOS
brew install graphviz
# Debian / Ubuntu
sudo apt-get install graphviz
```

Esecuzione:

```bash
source venv/bin/activate
python plot_precedence_graph.py
# opzioni: --rankdir TB (layout verticale), --fmt pdf, --no-time, --out nome_file
```

> Questo passaggio è indipendente dal notebook: serve solo a produrre la figura
> del grafo, non è necessario per il calcolo di RPW, LCR e KPI.

---

## Output prodotti

Eseguendo il notebook ottieni, a video:

- la tabella dei task (con i predecessori come liste);
- la configurazione **AS-IS** (benchmark, 6 stazioni);
- la tabella dei **pesi posizionali RPW** e l'ordinamento RPW;
- la configurazione **RPW** alle stazioni;
- l'ordinamento e la configurazione **LCR**;
- la **tabella KPI** di confronto AS-IS / RPW / LCR.

e su file, `risultati_ALB.xlsx`, con i fogli:
`Task`, `RPW_weights`, `RPW_order`, `RPW_assignment`, `LCR_order`,
`LCR_assignment`, `ASIS_assignment`, `KPI_comparison`.

### Risultati attesi

| Metodo | N. stazioni | Idle Time | Efficienza | Balance Delay |
|--------|-------------|-----------|------------|----------------|
| AS-IS  | 6 | 615 s | 75.6 % | 24.4 % |
| RPW    | 5 | 195 s | 90.7 % | 9.3 % |
| LCR    | 5 | 195 s | 90.7 % | 9.3 % |

Entrambe le euristiche eliminano una stazione rispetto all'AS-IS (6 → 5, il
minimo teorico ⌈1905/420⌉ = 5), aumentando l'efficienza della linea.

---

## Note

- Le funzioni di calcolo sono in `alb_helpers.py` e vengono importate dal
  notebook (`import alb_helpers as H`). Il notebook attiva l'**autoreload**, così
  le modifiche al modulo vengono ricaricate automaticamente.
- Se dopo aver modificato `alb_helpers.py` ottieni un errore tipo
  `AttributeError: module 'alb_helpers' has no attribute ...` oppure vedi un
  comportamento "vecchio", esegui **Restart Kernel** e poi **Run All**: il
  modulo viene reimportato da zero.
