from gurobipy import Model, GRB, quicksum
import pandas as pd
import numpy as np
import time
import os
import config
import logging

logging.basicConfig(filename='logs.log', level=logging.DEBUG, format='%(asctime)s; %(levelname)s; %(message)s')

def modellierung(szenario):
    
    base_case = 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base'
    
    dict_base = {
        'ladequote': base_case.split('_')[3],
        'cluster': base_case.split('_')[1],
        'pause': base_case.split('_')[9]
    }
    
    dict_szenario = {
        'ladequote': szenario.split('_')[3],
        'cluster': szenario.split('_')[1],
        'pause': szenario.split('_')[9]
    }
    
    path = os.path.dirname(os.path.abspath(__file__))
    
    # Passende CSV-Dateien wählen
    if (dict_szenario['ladequote'] == dict_base['ladequote'] and 
        dict_szenario['cluster']   == dict_base['cluster']   and 
        dict_szenario['pause']     == dict_base['pause']):
        
        df_lkw = pd.read_csv(
            os.path.join(path, 'data', 'epex', 'lkws', f'eingehende_lkws_loadstatus_{base_case}.csv'),
            sep=';', decimal=','
        )
        df_ladehub = pd.read_csv(
            os.path.join(path, 'data', 'flex', 'konfiguration_ladehub',f'anzahl_ladesaeulen_{base_case}.csv'),
            sep=';', decimal=','
        )
    else:
        df_lkw  = pd.read_csv(
            os.path.join(path, 'data', 'epex', 'lkws', f'eingehende_lkws_loadstatus_{szenario}.csv'),
            sep=';', decimal=','
        )
        df_ladehub = pd.read_csv(
            os.path.join(path, 'data', 'flex', 'konfiguration_ladehub',f'anzahl_ladesaeulen_{szenario}.csv'),
            sep=';', decimal=','
        )

    df_epex = pd.read_csv(os.path.join(path, 'input', 'epex_week.csv'), sep=';', decimal=',', index_col=0)
    df_nrv = pd.read_csv(os.path.join(path, 'input', 'NRV-Saldo_2024_5min_quadratic.csv'), sep=';', decimal=',', index_col=0)    

    print(len(df_nrv))

    # Bidirektional: aus Szenario ableiten
    bidirektional = False if szenario.split('_')[10] == 'M' else True
    
    # Maximale Leistung pro Ladesäulen-Typ
    ladeleistung = {
        'NCS': int(int(szenario.split('_')[7].split('-')[0]) / 100 * config.leistung_ladetyp['NCS']),
        'HPC': int(int(szenario.split('_')[7].split('-')[1]) / 100 * config.leistung_ladetyp['HPC']),
        'MCS': int(int(szenario.split('_')[7].split('-')[2]) / 100 * config.leistung_ladetyp['MCS'])
    }

    # Anzahl Ladesäulen
    max_saeulen = {
        'NCS': int(df_ladehub['NCS'][0]),
        'HPC': int(df_ladehub['HPC'][0]),
        'MCS': int(df_ladehub['MCS'][0])
    }

    netzanschlussfaktor = float(int(szenario.split('_')[5]) / 100)
    netzanschluss = (
        max_saeulen['NCS'] * ladeleistung['NCS'] +
        max_saeulen['HPC'] * ladeleistung['HPC'] +
        max_saeulen['MCS'] * ladeleistung['MCS']
    ) * netzanschlussfaktor

    
    # -------------------------------------
    # Vorbereitung: Lastgang-Arrays
    # -------------------------------------
    # Ein Jahr mit 525.600 Minuten, 5-Minuten-Schritte -> 105.120 Zeitschritte
    YEAR_MINUTES = 527040
    TIMESTEP = 5
    N = YEAR_MINUTES // TIMESTEP  # 527040 / 5 = 105408
    NUM_WEEKS = df_lkw['KW'].max()  # Anzahl Wochen
    # -------------------------------------
    # Wochenschleife (52-53 Wochen im Jahr)
    # Hier: range(365), was bei dir 365 Blöcke bedeutet
    # -------------------------------------
    # 1 Woche = 7 Tage = 2016 Zeitstufen (7*24*60/5)
    T_8 = 288 * 8
    T_7 = 288 * 7
    
    Delta_t = TIMESTEP / 60.0

    STRATEGIES = ["NRV"]  
    # STRATEGIES = ["T_min", "Epex", "Konstant"]

    # Vorbefüllen der Liste mit allen Zeitpunkten und Strategien
    rows = []
    for strategie in STRATEGIES:
        for i in range(N):
            rows.append({
                'Datum':                pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(minutes=i * TIMESTEP),
                'Woche':                1 + i // T_7,
                'Tag':                  1 + (i // 288) % 7,
                'Zeit':                 (i * TIMESTEP) % 1440,
                # 'Preis':                df_epex['Preis'][i],
                'Leistung_Total':       0.0,
                'Leistung_Max_Total':   0.0,
                'Leistung_NCS':         0.0,
                'Leistung_HPC':         0.0,
                'Leistung_MCS':         0.0,
                'Ladestrategie':        strategie,
                'Netzanschluss':        netzanschluss,
                'Ladequote':            0.0,
            })

    # Index-Map für schnellen Zugriff erstellen
    row_index = {(strategie, i): idx for idx, (strategie, i) in enumerate([(r['Ladestrategie'], 
                                             (pd.Timestamp(r['Datum']) - pd.Timestamp('2024-01-01 00:00:00')).total_seconds() // (60 * TIMESTEP)) 
                                             for r in rows])}

    dict_lkw_lastgang = {
        'LKW_ID': [],
        'Datum': [],
        'Woche': [],
        'Tag': [],
        'Zeit': [],
        'Ladetyp': [],
        'Ladestrategie': [],
        'Ladezeit': [],
        'Preis': [],
        'Leistung': [],
        'SOC': [],
        'Max_Leistung': [],
        'Pplus': [],
        'Pminus': [],
        'z': []
    }

    for week in range(1, NUM_WEEKS + 1):

        df_lkw_filtered = df_lkw[
            (df_lkw['KW'] == week) &
            (df_lkw['LoadStatus'] == 1)
        ].copy() 
                
        df_epex_filtered = df_epex[
            (df_epex['KW'] == week)
            | (df_epex['KW'] == week+1)
        ].copy()
        
        df_nrv_filtered = df_nrv[
            (df_nrv['KW'] == week)
            | (df_nrv['KW'] == week+1)
        ].copy()
        
        if df_lkw_filtered.empty:
            # Keine LKW in dieser Woche
            continue

        # Ankunfts- und Abfahrtszeiten in 5-Minuten-Index
        week_offset_steps = (week-1) * T_7
        df_lkw_filtered['t_a'] = (df_lkw_filtered['Ankunftszeit_total'] // TIMESTEP).astype(int) - week_offset_steps
        df_lkw_filtered['t_d'] = ((df_lkw_filtered['Ankunftszeit_total'] 
                                   + df_lkw_filtered['Pausenlaenge'] 
                                   - TIMESTEP) // TIMESTEP).astype(int) - week_offset_steps
        
        if df_lkw_filtered.empty:
            continue

        t_in     = df_lkw_filtered['t_a'].tolist()        
        t_out    = df_lkw_filtered['t_d'].tolist()
        l        = df_lkw_filtered['Ladesäule'].tolist()
        SOC_A    = df_lkw_filtered['SOC'].tolist()
        kapaz    = df_lkw_filtered['Kapazitaet'].tolist()
        maxLKW   = df_lkw_filtered['Max_Leistung'].tolist()
        SOC_req  = df_lkw_filtered['SOC_Target'].tolist()
        preis    = df_epex_filtered['Preis'].tolist()
        nrv      = df_nrv_filtered['Saldo'].values

        
        # Leistungsskalierung
        pow_split = szenario.split('_')[6].split('-')
        if len(pow_split) > 1:
            lkw_leistung_skalierung = float(pow_split[1]) / 100
        else:
            lkw_leistung_skalierung = 1.0

        max_lkw_leistung = [m * lkw_leistung_skalierung for m in maxLKW]
        E_req = [kapaz[i] * (SOC_req[i] - SOC_A[i]) for i in range(len(df_lkw_filtered))]
        I = len(df_lkw_filtered)

        # Offset in Minuten für diese Woche im Jahreslauf
        week_offset_minutes = week * T_7 * TIMESTEP

        # -------------------------------------
        # Strategien p_max / p_min
        # -------------------------------------
        for strategie in STRATEGIES:
            # Neues Gurobi-Modell
            model = Model("Ladehub_Optimierung")
            model.setParam('OutputFlag', 0)

            # Variablen
            P, Pplus, Pminus = {}, {}, {}
            P_max_i, P_max_i_2, SoC, z = {}, {}, {}, {}

            for i in range(I):
                for t_step in range(t_in[i], t_out[i] + 1):
                    if bidirektional:
                        P[(i,t_step)] = model.addVar(lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS)
                    else:
                        P[(i,t_step)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS)

                    Pplus[(i,t_step)]  = model.addVar(lb=0, vtype=GRB.CONTINUOUS)
                    Pminus[(i,t_step)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS)
                    P_max_i[(i,t_step)]   = model.addVar(lb=0, vtype=GRB.CONTINUOUS)
                    P_max_i_2[(i,t_step)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS)
                    z[(i,t_step)] = model.addVar(vtype=GRB.BINARY)

                for t_step in range(t_in[i], t_out[i] + 2):
                    SoC[(i,t_step)] = model.addVar(lb=0, ub=1, vtype=GRB.CONTINUOUS)

            # CONSTRAINTS
            # 1) Energiebedarf
            for i in range(I):
                model.addConstr(quicksum(P[(i, t_step)]*Delta_t 
                                         for t_step in range(t_in[i], t_out[i]+1)) <= E_req[i])

            # 2) SOC-Fortschreibung
            for i in range(I):
                model.addConstr(SoC[(i, t_in[i])] == SOC_A[i])
                for t_step in range(t_in[i], t_out[i]+1):
                    model.addConstr(
                        SoC[(i, t_step+1)] == SoC[(i, t_step)] + P[(i, t_step)] * Delta_t / kapaz[i]
                    )

            # 3) Ladekurven
            for i in range(I):
                for t_step in range(t_in[i], t_out[i]+1):
                    ml = max_lkw_leistung[i]
                    model.addConstr(P_max_i[(i, t_step)]   == (-0.177038*SoC[(i,t_step)] + 0.970903)*ml)
                    model.addConstr(P_max_i_2[(i,t_step)] == (-1.51705*SoC[(i,t_step)] + 1.6336)*ml)

                    model.addConstr(Pplus[(i,t_step)]  <= P_max_i[(i,t_step)]   * z[(i,t_step)])
                    model.addConstr(Pminus[(i,t_step)] <= P_max_i[(i,t_step)]   * (1 - z[(i,t_step)]))
                    model.addConstr(Pplus[(i,t_step)]  <= P_max_i_2[(i,t_step)] * z[(i,t_step)])
                    model.addConstr(Pminus[(i,t_step)] <= P_max_i_2[(i,t_step)] * (1 - z[(i,t_step)]))

            # 4) Leistungsbegrenzung Ladesäulentyp
            for i in range(I):
                typ = l[i]
                P_max_l = ladeleistung[typ]
                for t_step in range(t_in[i], t_out[i]+1):
                    model.addConstr(Pplus[(i,t_step)]  <= z[(i,t_step)] * P_max_l)
                    model.addConstr(Pminus[(i,t_step)] <= (1 - z[(i,t_step)]) * P_max_l)

            # 5) Netzanschluss
            for t_step in range(T_8):
                idx = [i for i in range(I) if t_in[i] <= t_step <= t_out[i]]
                if idx:
                    model.addConstr(quicksum(Pplus[(i,t_step)] + Pminus[(i,t_step)] 
                                             for i in idx) <= netzanschluss)

            # 6) Kopplungsbedingungen (P = Pplus - Pminus, z monoton steigend)
            for i in range(I):
                for t_step in range(t_in[i], t_out[i]+1):
                    model.addConstr(P[(i,t_step)] == Pplus[(i,t_step)] - Pminus[(i,t_step)])
                for t_step in range(t_in[i], t_out[i]):
                    model.addConstr(z[(i, t_step+1)] >= z[(i, t_step)])

            # -------------------------------------
            # Zielfunktion
            # -------------------------------------
            if strategie == "Epex":
                # Zweistufiger Ansatz:
                # 1. Maximiere die Gesamtleistung (immer so viel wie möglich laden)
                # 2. Verteile diese Energie kostengünstig (bei günstigsten Preisen laden)
                
                # Wichtig: Der Faktor M muss ausreichend groß sein, damit die Energiemaximierung
                # immer Priorität hat vor der Kostenoptimierung
                M = 10000  # Hoher Gewichtungsfaktor für die Energiemaximierung
                
                # Primäres Ziel: Maximale Ladeleistung
                # Sekundäres Ziel: Minimiere Kosten durch Laden bei günstigen Preisen
                obj_expr = quicksum(
                    M * Pplus[(i, t)] - preis[t] * Pplus[(i, t)]
                    for i in range(I) for t in range(t_in[i], t_out[i] + 1)
                )

            elif strategie == "T_min":
                obj_expr = quicksum(((1/(t+1)) * (Pplus[(i, t)])) - (t * Pminus[(i, t)]) for i in range(I) for t in range(t_in[i], t_out[i] + 1))

            elif strategie == "Konstant":
                # Hilfsvariablen für Leistungsänderungen zwischen Zeitschritten
                delta = {}
                for i in range(I):
                    for t_step in range(t_in[i], t_out[i]):
                        # Variable für die absolute Differenz zwischen aufeinanderfolgenden Zeitschritten
                        delta[(i,t_step)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"delta_{i}_{t_step}")
                        # Berechnung der absoluten Differenz zwischen aufeinanderfolgenden Leistungswerten
                        model.addConstr(delta[(i,t_step)] >= P[(i,t_step+1)] - P[(i,t_step)])
                        model.addConstr(delta[(i,t_step)] >= P[(i,t_step)] - P[(i,t_step+1)])
                
                # Extrem hohe Gewichtung für die Energiemaximierung, um absolute Priorität zu gewährleisten
                M_energy = 1000000  # Sehr hoher Gewichtungsfaktor
                
                # Zielfunktion: Hierarchisches Modell
                # 1. Primäres Ziel mit sehr hoher Gewichtung: Maximiere Energie
                # 2. Sekundäres Ziel: Minimiere Leistungsschwankungen
                obj_expr = quicksum(
                    M_energy * Pplus[(i, t)]  # Primärziel mit sehr hoher Gewichtung
                    - quicksum(delta[(i, t_step)] for t_step in range(t_in[i], min(t+1, t_out[i])) if t_step < t_out[i])  # Sekundärziel
                    for i in range(I) for t in range(t_in[i], t_out[i] + 1)
                )

            elif strategie == "NRV":
                # NRV-Werte extrahieren 
                nrv_values = df_nrv_filtered['Saldo'].values
                
                # Normalisiere NRV-Werte für bessere numerische Stabilität
                max_abs_nrv = max(abs(v) for v in nrv_values) if len(nrv_values) > 0 else 1
                normalized_nrv = [v / max_abs_nrv for v in nrv_values]
                
                # Hierarchisches Optimierungsmodell:
                # 1. Primäres Ziel mit hoher Gewichtung: Maximiere Energieeintrag (ähnlich wie bei anderen Strategien)
                # 2. Sekundäres Ziel: Minimiere NRV-Einfluss durch gegenläufiges Verhalten
                #    - Bei positivem NRV (Strommangel): Weniger laden oder rückspeisen
                #    - Bei negativem NRV (Stromüberschuss): Mehr laden
                
                M_energy = 10000  # Hoher Gewichtungsfaktor für die Energiemaximierung
                
                obj_expr = quicksum(
                    # Primärziel: Maximiere Ladung
                    M_energy * Pplus[(i, t)]  
                    # Sekundärziel: NRV-Gegensteuerung
                    # Negativer NRV-Wert * Laden: Erhöht Ladeleistung bei Überschuss
                    # Positiver NRV-Wert * Entladen: Fördert Rückspeisung bei Mangel
                    + (-normalized_nrv[t] * Pplus[(i, t)] + normalized_nrv[t] * Pminus[(i, t)])
                    for i in range(I) for t in range(t_in[i], t_out[i] + 1) if t < len(normalized_nrv)
                )
                
            
            model.setObjective(obj_expr, GRB.MAXIMIZE)
            model.optimize()

            # -------------------------------------
            # Ergebnisse verarbeiten
            # -------------------------------------
            if model.Status == GRB.OPTIMAL:
                # Ladequote in dieser Woche
                list_volladungen = []
                for i in range(I):
                    if SoC[(i, t_out[i]+1)].X >= SOC_req[i] - 0.01:
                        list_volladungen.append(1)
                    else:
                        list_volladungen.append(0)
                ladequote_week = sum(list_volladungen) / len(list_volladungen)
                
                # Berechnung der Gesamtkosten für die Ladung in dieser Woche
                gesamtkosten = 0.0
                for i in range(I):
                    for t_step in range(t_in[i], t_out[i]+1):
                        # Nur positive Ladeleistung (Pplus) kostet Geld
                        gesamtkosten += Pplus[(i, t_step)].X * Delta_t * preis[t_step]
                
                print(f"[Szenario={szenario}, Woche={week}, Strategie={strategie}] "
                      f"Lösung OK. Ladequote: {ladequote_week:.3f}, "
                      f"Anzahl LKW: {len(df_lkw_filtered)}, "
                      f"Gesamtkosten: {gesamtkosten:.2f} €")
                
                # Lastgang: direkt in rows eintragen
                for t_step in range(T_8):
                    sum_p_total = 0.0
                    sum_p_total_max = 0.0
                    sum_p_ncs = 0.0
                    sum_p_hpc = 0.0
                    sum_p_mcs = 0.0
                    for i in range(I):
                        if t_in[i] <= t_step <= t_out[i]:
                            val = P[(i, t_step)].X
                            sum_p_total += val
                            sum_p_total_max += ladeleistung[l[i]]
                            if l[i] == 'NCS':
                                sum_p_ncs += val
                            elif l[i] == 'HPC':
                                sum_p_hpc += val
                            elif l[i] == 'MCS':
                                sum_p_mcs += val

                    global_t = week_offset_minutes + t_step * TIMESTEP
                    idx = global_t // TIMESTEP  # entspricht global_t_min / 5

                    # Direktes Eintragen in rows mit dem entsprechenden Index
                    row_idx = row_index[(strategie, idx)]
                    rows[row_idx]['Leistung_Total'] += sum_p_total
                    rows[row_idx]['Leistung_Max_Total'] += sum_p_total_max
                    rows[row_idx]['Leistung_NCS'] += sum_p_ncs
                    rows[row_idx]['Leistung_HPC'] += sum_p_hpc
                    rows[row_idx]['Leistung_MCS'] += sum_p_mcs
                    rows[row_idx]['Ladequote'] = ladequote_week  # Überschreiben, nicht addieren

                for i in range(I):
                    t_charging = 0
                    for t in range(T_8):   
                        if t_in[i] <= t <= t_out[i]+1:
                            dict_lkw_lastgang['Datum'].append(pd.Timestamp('2024-01-01') + pd.Timedelta(minutes=week_offset_minutes + t*5))
                            dict_lkw_lastgang['Woche'].append(week + 1)
                            dict_lkw_lastgang['Tag'].append(df_lkw_filtered.iloc[i]['Tag'] % 7)
                            dict_lkw_lastgang['Preis'].append(f"{preis[t]:.7f}".replace('.', ','))
                            dict_lkw_lastgang['Zeit'].append((t * 5) % 1440)
                            dict_lkw_lastgang['Ladestrategie'].append(strategie)
                            dict_lkw_lastgang['LKW_ID'].append(df_lkw_filtered.iloc[i]['Nummer'])
                            dict_lkw_lastgang['Ladetyp'].append(l[i])
                            dict_lkw_lastgang['Ladezeit'].append(t_charging)
                            t_charging += 5
                            if t > t_out[i]:
                                dict_lkw_lastgang['Leistung'].append(None)
                                dict_lkw_lastgang['Pplus'].append(None)
                                dict_lkw_lastgang['Pminus'].append(None)
                                dict_lkw_lastgang['SOC'].append(SoC[(i, t_out[i]+1)].X)
                                dict_lkw_lastgang['z'].append(None)
                                dict_lkw_lastgang['Max_Leistung'].append(None)
                                continue
                            else:                        
                                dict_lkw_lastgang['Max_Leistung'].append(min(ladeleistung[l[i]], max_lkw_leistung[i]))
                                dict_lkw_lastgang['z'].append(z[(i, t)].X)
                                dict_lkw_lastgang['Pplus'].append(Pplus[(i, t)].X)
                                dict_lkw_lastgang['Pminus'].append(Pminus[(i, t)].X)
                                dict_lkw_lastgang['Leistung'].append(P[(i, t)].X)
                                dict_lkw_lastgang['SOC'].append(SoC[(i, t)].X)
            else:
                print(f"[Szenario={szenario}, Woche={week}, Strategie={strategie}] "
                      f"Keine optimale Lösung gefunden.")

    # -------------------------------------
    # Nach Wochen-Schleife: DataFrames bauen und speichern
    # -------------------------------------
    # 1) Lastgang-DF je Strategie
    #    Wir packen beide Strategien zusammen in EIN DataFrame,
    #    indem wir sie untereinander (concat) kleben und eine Spalte "Ladestrategie" hinzufügen.
    
    df_lastgang = pd.DataFrame(rows)

    # 2) LKW-Lastgang als DataFrame
    df_lkw_lastgang_df = pd.DataFrame(dict_lkw_lastgang)
    df_lkw_lastgang_df.sort_values(['LKW_ID', 'Ladestrategie', 'Zeit'], inplace=True)
    
    
    # Ordner anlegen und CSV speichern
    os.makedirs(os.path.join(path, 'data', 'epex', 'lastgang'), exist_ok=True)
    os.makedirs(os.path.join(path, 'data', 'epex', 'lastgang_lkw'), exist_ok=True)

    df_lastgang.to_csv(
        os.path.join(path, 'data', 'epex', 'lastgang', f'lastgang_{szenario}.csv'),
        sep=';', decimal=',', index=False
    )
    df_lkw_lastgang_df.to_csv(
        os.path.join(path, 'data', 'epex', 'lastgang_lkw', f'lastgang_lkw_{szenario}.csv'),
        sep=';', decimal=',', index=False
    )

    return None


def main():
    for szenario in config.list_szenarien:
        print(f"Starte wochenweise Optimierung für: {szenario}")
        logging.info(f"Optimierung p_max/p_min: {szenario}")
        modellierung(szenario)

if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print(f"Gesamtlaufzeit: {end - start:.2f} Sekunden")