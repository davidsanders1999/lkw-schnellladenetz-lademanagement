# ======================================================
# Benötigte Bibliotheken importieren
# ======================================================
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import os
import time
import config

# Konfiguration der Zeitspanne (Wochen)
CONFIG = {
    'week_start': 1,
    'week_end': 53
}

# ======================================================
# Optimierungsfunktion: Maximale LKW-Zuweisung an Ladesäulen
# ======================================================
def max_truck_assignment(arrival_times, departure_times, num_stations):
    """
    Maximiert die Anzahl der LKWs, die gleichzeitig geladen werden können,
    unter Einhaltung von Zeitüberschneidungs- und Ressourcenkapazitäten.
    """

    # Modellinitialisierung
    model = gp.Model("max_truck_assignment")
    model.setParam('OutputFlag', 0)  # Keine Konsolenausgabe

    I = range(len(arrival_times))       # LKW-Indizes
    N_l = range(num_stations)           # Ladesäulen-Indizes

    # Entscheidungsvariablen: x[i,s] = 1, wenn LKW i auf Säule s geladen wird
    x = model.addVars([(i, s) for i in I for s in N_l], vtype=GRB.BINARY, name="x")

    # Zielfunktion: Maximiere Anzahl zugewiesener LKWs
    model.setObjective(gp.quicksum(x[i, s] for i in I for s in N_l), GRB.MAXIMIZE)

    # Nebenbedingung: Jeder LKW darf max. 1 Säule nutzen
    for i in I:
        model.addConstr(gp.quicksum(x[i, s] for s in N_l) <= 1, name=f"Assign_LKW_{i}")

    # Keine Zeitüberschneidung auf derselben Säule zulassen
    for i in I:
        for j in I:
            if i < j:
                # Prüfe, ob Zeitfenster kollidieren
                if (arrival_times[i] < departure_times[j]) and (arrival_times[j] < departure_times[i]):
                    for s in N_l:
                        model.addConstr(x[i, s] + x[j, s] <= 1, name=f"Overlap_{i}_{j}_s{s}")

    # Optimierung durchführen
    model.optimize()

    # Ergebnis extrahieren
    ladestatus = [0] * len(I)
    if model.status == GRB.OPTIMAL:
        for i in I:
            if any(x[i, s].X > 0.5 for s in N_l):
                ladestatus[i] = 1
    else:
        print("⚠️ Keine optimale Lösung gefunden. Status:", model.status)

    return ladestatus

# ======================================================
# Hauptfunktion: Ladezuweisung über alle Wochen + Typen
# ======================================================
def main():
    time_start = time.time()

    df_lkws_gesamt = pd.DataFrame()
    ladetypen = ['HPC', 'MCS', 'NCS']

    # Liste der zu analysierenden Szenarien
    list_szenarien = config.list_szenarien
    szenario = list_szenarien[0]  # Beispielweise nur erstes Szenario
    
    path_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

    # Lade die konfigurierte Anzahl an Ladesäulen je Typ
    path_cfg = os.path.join(path_data, 'flex', "konfiguration_ladehub", f"anzahl_ladesaeulen_{szenario}.csv")
    df_anzahl_ladesaeulen = pd.read_csv(path_cfg, sep=';', decimal=',', index_col=0)

    cluster = int(szenario.split('_')[1])
    anzahl = {
        'NCS': int(df_anzahl_ladesaeulen.loc[0, 'NCS']),
        'HPC': int(df_anzahl_ladesaeulen.loc[0, 'HPC']),
        'MCS': int(df_anzahl_ladesaeulen.loc[0, 'MCS'])
    }

    # Eingehende LKW-Daten laden (nur entsprechender Cluster)
    df_all_incoming = pd.read_csv(
        os.path.join(path_data, 'epex', 'lkw_eingehend', 'eingehende_lkws_ladesaeule.csv'),
        sep=';', decimal=',', index_col=0
    )
    df_all_incoming = df_all_incoming[df_all_incoming['Cluster'] == cluster].copy()

    # Iteration über alle Ladetypen
    for ladetyp in ladetypen:
        df_eingehende_lkws = df_all_incoming[df_all_incoming['Ladesäule'] == ladetyp].copy()
        print(f"\n=== Verarbeitung: Ladetyp '{ladetyp}' ===")

        # Iteration über Wochen
        for week in range(CONFIG['week_start'], CONFIG['week_end'] + 1):
            df_week = df_eingehende_lkws[df_eingehende_lkws['KW'] == week].copy()
            if df_week.empty:
                continue  # Keine LKWs in dieser Woche

            arrival_times = df_week['Ankunftszeit_total'].values
            departure_times = (df_week['Ankunftszeit_total'] + df_week['Pausenlaenge']).values

            # Gurobi-Optimierung aufrufen
            ladestatus = max_truck_assignment(arrival_times, departure_times, anzahl[ladetyp])
            df_week['LoadStatus'] = ladestatus

            df_lkws_gesamt = pd.concat([df_lkws_gesamt, df_week])
            ladequote = sum(ladestatus) / len(ladestatus)
            print(f"Woche {week:02d} → Ladequote: {ladequote:.2%}")

    # Export der gesammelten Ergebnisse
    output_path = os.path.join(path_data, 'epex', 'lkws')
    os.makedirs(output_path, exist_ok=True)

    output_file = os.path.join(output_path, f'eingehende_lkws_loadstatus_{szenario}.csv')
    df_lkws_gesamt.to_csv(output_file, sep=';', decimal=',')
    print(f"\n✅ Ergebnisse gespeichert unter:\n{output_file}")

    time_end = time.time()
    print(f"⏱️ Gesamtlaufzeit: {time_end - time_start:.2f} Sekunden.")

# ======================================================
# Programmstart
# ======================================================
if __name__ == "__main__":
    main()