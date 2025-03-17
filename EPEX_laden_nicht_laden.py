

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import os
import time
import config

CONFIG = {
    'week_start': 1,
    'week_end': 53
}

def max_truck_assignment(arrival_times, departure_times, num_stations):
    """
    Maximiert die Anzahl an LKWs, die bedient werden können,
    unter der Einschränkung, dass LKWs sich nicht überlappen dürfen.

    Parameter:
    -----------
    arrival_times  : list of float
        Liste der Ankunftszeiten [a_i].
    departure_times: list of float
        Liste der Abfahrtszeiten [d_i].
    num_stations   : int
        Anzahl verfügbarer Ladesäulen (K).

    Returns:
    -----------
    ladestatus: list of int (0 oder 1)
        Liste, die angibt, welche LKWs (Index i) bedient wurden (1) und welche nicht (0).
    """

    # 1. Initialisierung des Modells
    model = gp.Model("max_truck_assignment")
    model.setParam('OutputFlag', 0)

    # 2. Indizes
    I = range(len(arrival_times))  # Menge der LKWs
    N_l = range(num_stations)      # Anzahl an Ladesäulen

    # 3. Entscheidungsvariablen x[i,s]
    x = model.addVars(
        [(i, s) for i in I for s in N_l],
        vtype=GRB.BINARY,
        name="x"
    )

    # 4. Zielfunktion: Maximiere Anzahl der bedienten LKWs
    model.setObjective(
        gp.quicksum(x[i, s] for i in I for s in N_l), 
        GRB.MAXIMIZE
    )

    # 5. Nebenbedingungen

    # (a) Jeder LKW darf höchstens einer Ladesäule zugewiesen werden
    for i in I:
        model.addConstr(
            gp.quicksum(x[i, s] for s in N_l) <= 1,
            name=f"Assign_LKW_{i}"
        )

    # (b) Zeitüberlappung: Keine zwei LKWs auf derselben Säule, 
    #     wenn ihre Zeitfenster kollidieren.
    for i in I:
        for j in I:
            if i < j:  # nur einmal prüfen
                # Überlappt [a_i, d_i) mit [a_j, d_j)?
                if (arrival_times[i] < departure_times[j]) and (arrival_times[j] < departure_times[i]):
                    for s in N_l:
                        model.addConstr(
                            x[i, s] + x[j, s] <= 1,
                            name=f"Overlap_{i}_{j}_s{s}"
                        )

    # 6. Optimierung
    model.optimize()

    # 7. Ergebnisse aufbereiten (ladestatus pro LKW)
    ladestatus = [0]*len(I)
    if model.status == GRB.OPTIMAL:
        for i in I:
            # Prüfen, ob LKW i auf mind. 1 Ladesäule zugewiesen wurde
            if any(x[i, s].X > 0.5 for s in N_l):
                ladestatus[i] = 1
    else:
        print("Keine optimale Lösung gefunden. Status:", model.status)
    
    return ladestatus


def main():
    # Großes DataFrame zum Zusammenfassen aller Wochen + aller LKW
    df_lkws_gesamt = pd.DataFrame()

    # Ladetypen
    ladetypen = ['HPC', 'MCS', 'NCS']

    # Beispiel: nur 1 Szenario, 
    # Sie können hier auch mehrere aus config.list_szenarien iterieren
    list_szenarien = config.list_szenarien  
    szenario = list_szenarien[0]

    path_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

    # Einlesen der Ladesäulen-Konfiguration
    df_anzahl_ladesaeulen = pd.read_csv(
        os.path.join(path_data, 'flex', "konfiguration_ladehub", f"anzahl_ladesaeulen_{szenario}.csv"), 
        sep=';', decimal=',', index_col=0
    )
    
    cluster = int(szenario.split('_')[1])

    anzahl = {
        'NCS': df_anzahl_ladesaeulen.loc[0, 'NCS'],
        'HPC': df_anzahl_ladesaeulen.loc[0, 'HPC'],
        'MCS': df_anzahl_ladesaeulen.loc[0, 'MCS']
    }


    # CSV mit allen eingehenden LKW
    df_all_incoming = pd.read_csv(
        os.path.join(path_data, 'epex','lkw_eingehend', 'eingehende_lkws_ladesaeule.csv'),
        sep=';', decimal=',', index_col=0
    )

    df_all_incoming = df_all_incoming[df_all_incoming['Cluster'] == cluster].copy()

    # NUM_WEEKS = df_all_incoming['KW'].max()  # Anzahl Wochen
    
    
    # Schleife über Ladetypen
    for ladetyp in ladetypen:
        # Extrahieren alle LKW dieses Ladetyps
        df_eingehende_lkws = df_all_incoming[df_all_incoming['Ladesäule'] == ladetyp].copy()

        print(f"\n=== Ladetyp: {ladetyp} ===")

        # Schleife über Wochen
        for week in range(CONFIG['week_start'], CONFIG['week_end']+1):

            df_week = df_eingehende_lkws[df_eingehende_lkws['KW'] == week].copy()
            
            if df_week.empty:
                # Keine LKWs in dieser Woche
                continue

            arrival_times   = df_week['Ankunftszeit_total'].values
            departure_times = (df_week['Ankunftszeit_total'] + df_week['Pausenlaenge']).values

            # Gurobi-Optimierung nur für diese Woche
            ladestatus = max_truck_assignment(arrival_times, departure_times, int(anzahl[ladetyp]))

            # In das DataFrame der Woche eintragen
            df_week['LoadStatus'] = ladestatus

            # Anschließend an das globale DF anhängen
            df_lkws_gesamt = pd.concat([df_lkws_gesamt, df_week])
            
            print(f"Woche {week}: Ladequote: {sum(ladestatus)/len(ladestatus):.2f}")

    # Am Ende: df_lkws_gesamt speichern
    output_path = os.path.join(path_data, 'epex', 'lkws')
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # CSV schreiben
    df_lkws_gesamt.to_csv(
        os.path.join(output_path, f'eingehende_lkws_loadstatus_{szenario}.csv'),
        sep=';', decimal=','
    )
    print(f"\nErgebnis als CSV gespeichert: {os.path.join(output_path, f'eingehende_lkws_loadstatus_{szenario}.csv')}")


if __name__ == "__main__":
    time_start = time.time()
    main()
    time_end = time.time()
    print(f"\nGesamtlaufzeit: {time_end - time_start:.2f} Sekunden.")