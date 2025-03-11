from gurobipy import Model, GRB, quicksum
import pandas as pd
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

    # Bidirektional: aus Szenario ableiten
    bidirektional = False if szenario.split('_')[10] == 'M' else True
    
    # -------------------------------------
    # Container für Jahres-Lastgänge
    # -------------------------------------
    YEAR_MINUTES = 525600  # z.B. 365 Tage
    TIMESTEP = 5
    lastgang_dict = {}
    
    # Zwei Strategien, die wir später in einer Schleife durchlaufen
    STRATEGIES = ["p_max", "p_min"]

    # Für jede mögliche Minute im Jahr + jede Strategie initialisieren
    for strategie in STRATEGIES:
        for t in range(0, YEAR_MINUTES+1, TIMESTEP):
            key = (t, strategie)
            lastgang_dict[key] = {
                'Zeit': t,
                'Zeit_Time': pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(minutes=t),
                'Leistung_Total': 0.0,
                'Leistung_Max_Total': 0.0,
                'Leistung_NCS': 0.0,
                'Leistung_HPC': 0.0,
                'Leistung_MCS': 0.0,
                'Ladestrategie': strategie,
                'Netzanschluss': 0.0,
                'Ladequote': 0.0
            }

    # Globale Container für LKW-Lastgänge
    dict_lkw_lastgang = {
        'LKW_ID': [],
        'Ladetyp': [],
        'Zeit': [],
        'Ladezeit': [],
        'Leistung': [],
        'Max_Leistung': [],
        'Pplus': [],
        'Pminus': [],
        'SOC': [],
        'z': [],
        'Ladestrategie': []
    }

    # Maximale Leistung pro Ladesäulen-Typ
    ladeleistung = {
        'NCS': int(int(szenario.split('_')[7].split('-')[0])/100 * config.leistung_ladetyp['NCS']),
        'HPC': int(int(szenario.split('_')[7].split('-')[1])/100 * config.leistung_ladetyp['HPC']),
        'MCS': int(int(szenario.split('_')[7].split('-')[2])/100 * config.leistung_ladetyp['MCS'])
    }

    # Anzahl Ladesäulen
    max_saeulen = {
        'NCS': int(df_ladehub['NCS'][0]),
        'HPC': int(df_ladehub['HPC'][0]),
        'MCS': int(df_ladehub['MCS'][0])
    }

    netzanschlussfaktor = float(int(szenario.split('_')[5])/100)
    netzanschluss = (
        max_saeulen['NCS']*ladeleistung['NCS'] +
        max_saeulen['HPC']*ladeleistung['HPC'] +
        max_saeulen['MCS']*ladeleistung['MCS']
    ) * netzanschlussfaktor

    # -------------------------------------
    # Wochenschleife (52 Wochen)
    # -------------------------------------
    # Beispiel: 1 Woche = 7 Tage = 2016 Zeitstufen (7*24*12)
    T = 288 * 7
    Delta_t = TIMESTEP / 60.0

    for week in range(2):
        wday_start = 1 + week*7
        wday_end   = 7 + week*7

        # LKW-Daten filtern
        df_lkw_filtered = df_lkw[
            (df_lkw['Cluster'] == int(dict_szenario['cluster'])) &
            (df_lkw['LoadStatus'] == 1) &
            (df_lkw['Wochentag'] >= wday_start) &
            (df_lkw['Wochentag'] <= wday_end)
        ].copy()

        if df_lkw_filtered.empty:
            # Keine LKW in dieser Woche
            continue

        # Ankunfts- und Abfahrtszeiten in 5-Minuten-Index
        df_lkw_filtered['t_a'] = (df_lkw_filtered['Ankunftszeit_total'] // TIMESTEP).astype(int)
        df_lkw_filtered['t_d'] = ((df_lkw_filtered['Ankunftszeit_total'] + df_lkw_filtered['Pausenlaenge'] - TIMESTEP)//TIMESTEP).astype(int)

        # Offset, damit jede Woche bei t=0 beginnt
        min_in_week = df_lkw_filtered['t_a'].min()
        df_lkw_filtered['t_a'] -= min_in_week
        df_lkw_filtered['t_d'] -= min_in_week

        # Clipping auf 0..T-1
        df_lkw_filtered = df_lkw_filtered[
            (df_lkw_filtered['t_a'] >= 0) & (df_lkw_filtered['t_a'] < T)
        ]
        df_lkw_filtered['t_d'] = df_lkw_filtered['t_d'].clip(upper=T-1)

        if df_lkw_filtered.empty:
            continue

        # Spalten auslesen
        t_in     = df_lkw_filtered['t_a'].tolist()
        t_out    = df_lkw_filtered['t_d'].tolist()
        l        = df_lkw_filtered['Ladesäule'].tolist()
        SOC_A    = df_lkw_filtered['SOC'].tolist()
        kapaz    = df_lkw_filtered['Kapazitaet'].tolist()
        maxLKW   = df_lkw_filtered['Max_Leistung'].tolist()
        SOC_req  = df_lkw_filtered['SOC_Target'].tolist()

        # Leistungsskalierung
        pow_split = szenario.split('_')[6].split('-')
        if len(pow_split) > 1:
            lkw_leistung_skalierung = float(pow_split[1]) / 100
        else:
            lkw_leistung_skalierung = 1.0

        max_lkw_leistung = [m * lkw_leistung_skalierung for m in maxLKW]
        E_req = [kapaz[i]*(SOC_req[i] - SOC_A[i]) for i in range(len(df_lkw_filtered))]
        I = len(df_lkw_filtered)

        # Offset in Minuten für diese Woche im Jahreslauf
        week_offset_minutes = week * T * TIMESTEP

        # -------------------------------------
        # STRATEGIEN-Schleife
        # -------------------------------------
        for strategie in STRATEGIES:
            # Neues Gurobi-Modell
            model = Model("Ladehub_Optimierung")
            # model.setParam('OutputFlag', 0)

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
                model.addConstr(quicksum(P[(i, t_step)]*Delta_t for t_step in range(t_in[i], t_out[i]+1)) <= E_req[i])

            # 2) SOC-Fortschreibung
            for i in range(I):
                model.addConstr(SoC[(i, t_in[i])] == SOC_A[i])
                for t_step in range(t_in[i], t_out[i]+1):
                    model.addConstr(
                        SoC[(i, t_step+1)] == SoC[(i, t_step)] + P[(i, t_step)]*Delta_t/kapaz[i]
                    )

            # 3) Ladekurven
            for i in range(I):
                for t_step in range(t_in[i], t_out[i]+1):
                    ml = max_lkw_leistung[i]
                    model.addConstr(P_max_i[(i, t_step)]   == (-0.177038*SoC[(i,t_step)] + 0.970903)*ml)
                    model.addConstr(P_max_i_2[(i, t_step)] == (-1.51705*SoC[(i,t_step)] + 1.6336)*ml)

                    model.addConstr(Pplus[(i,t_step)]  <= P_max_i[(i,t_step)]   * z[(i,t_step)])
                    model.addConstr(Pminus[(i,t_step)] <= P_max_i[(i,t_step)]   * (1 - z[(i,t_step)]))
                    model.addConstr(Pplus[(i,t_step)]  <= P_max_i_2[(i,t_step)] * z[(i,t_step)])
                    model.addConstr(Pminus[(i,t_step)] <= P_max_i_2[(i,t_step)] * (1 - z[(i,t_step)]))

            # 4) Leistungsbegrenzung Ladesäulentyp
            for i in range(I):
                typ = l[i]
                P_max_l = ladeleistung[typ]
                for t_step in range(t_in[i], t_out[i]+1):
                    model.addConstr(Pplus[(i,t_step)]  <= z[(i,t_step)]*P_max_l)
                    model.addConstr(Pminus[(i,t_step)] <= (1 - z[(i,t_step)])*P_max_l)

            # 5) Netzanschluss
            for t_step in range(T):
                idx = [i for i in range(I) if t_in[i]<=t_step<=t_out[i]]
                if idx:
                    model.addConstr(quicksum(Pplus[(i,t_step)] + Pminus[(i,t_step)] for i in idx) <= netzanschluss)

            # 6) Kopplungsbedingungen (P = Pplus - Pminus, z monoton steigend)
            for i in range(I):
                for t_step in range(t_in[i], t_out[i]+1):
                    model.addConstr(P[(i,t_step)] == Pplus[(i,t_step)] - Pminus[(i,t_step)])
                for t_step in range(t_in[i], t_out[i]):
                    model.addConstr(z[(i, t_step+1)] >= z[(i, t_step)])

            # -------------------------------------
            # Verschiedene Zielfunktionen
            # -------------------------------------
            if strategie == "p_max":
                # Beispiel: Minimales t -> hoher Einfluss auf Pplus
                obj_expr = quicksum(
                    ((1.0 / (t_step+1)) * Pplus[(i, t_step)]) - (t_step * Pminus[(i, t_step)])
                    for i in range(I)
                    for t_step in range(t_in[i], t_out[i]+1)
                )
            else:  # strategie == "p_min"
                # Beispiel: Hohe Zeitgewichte auf Pplus negativ
                obj_expr = quicksum(
                    (-(t_step+1) * Pplus[(i, t_step)]) - ((t_step+1) * Pminus[(i, t_step)])
                    for i in range(I)
                    for t_step in range(t_in[i], t_out[i]+1)
                )

            model.setObjective(obj_expr, GRB.MAXIMIZE)

            # Optimieren
            model.optimize()

            # Ergebnisse speichern
            if model.Status == GRB.OPTIMAL:
                list_volladungen = []
                for i in range(I):
                    if SoC[(i, t_out[i]+1)].X >= SOC_req[i] - 0.01:
                        list_volladungen.append(1)
                    else:
                        list_volladungen.append(0)
                ladequote_week = sum(list_volladungen)/len(list_volladungen)

                # Lastgang in das globale Dictionary schreiben
                for t_step in range(T):
                    sum_p_total = 0.0
                    sum_p_total_max = 0.0
                    sum_p_ncs = 0.0
                    sum_p_hpc = 0.0
                    sum_p_mcs = 0.0
                    for i in range(I):
                        if t_in[i] <= t_step <= t_out[i]:
                            val = P[(i,t_step)].X
                            sum_p_total += val
                            sum_p_total_max += ladeleistung[l[i]]
                            if l[i] == 'NCS':
                                sum_p_ncs += val
                            elif l[i] == 'HPC':
                                sum_p_hpc += val
                            elif l[i] == 'MCS':
                                sum_p_mcs += val

                    # globaler Index in Minuten
                    global_t_min = week_offset_minutes + t_step*TIMESTEP
                    key = (global_t_min, strategie)
                    if key in lastgang_dict:
                        lastgang_dict[key]['Leistung_Total'] += sum_p_total
                        lastgang_dict[key]['Leistung_Max_Total'] += sum_p_total_max
                        lastgang_dict[key]['Leistung_NCS'] += sum_p_ncs
                        lastgang_dict[key]['Leistung_HPC'] += sum_p_hpc
                        lastgang_dict[key]['Leistung_MCS'] += sum_p_mcs
                        lastgang_dict[key]['Netzanschluss'] = netzanschluss
                        # Ladequote in diesem Beispiel einheitlich
                        lastgang_dict[key]['Ladequote'] = ladequote_week

                # LKW-Lastgang
                for i in range(I):
                    t_charging = 0
                    for t_step in range(T+1):
                        global_t_min = week_offset_minutes + t_step*TIMESTEP
                        dict_lkw_lastgang['LKW_ID'].append(df_lkw_filtered.iloc[i]['Nummer'])
                        dict_lkw_lastgang['Ladetyp'].append(l[i])
                        dict_lkw_lastgang['Zeit'].append(global_t_min)
                        dict_lkw_lastgang['Ladezeit'].append(t_charging)
                        dict_lkw_lastgang['Ladestrategie'].append(strategie)

                        if (t_step < t_in[i]) or (t_step > t_out[i]):
                            # keine Ladung
                            dict_lkw_lastgang['Leistung'].append(None)
                            dict_lkw_lastgang['Pplus'].append(None)
                            dict_lkw_lastgang['Pminus'].append(None)
                            if t_step == t_out[i]+1:
                                dict_lkw_lastgang['SOC'].append(SoC[(i, t_out[i]+1)].X)
                            else:
                                dict_lkw_lastgang['SOC'].append(None)
                            dict_lkw_lastgang['z'].append(None)
                            dict_lkw_lastgang['Max_Leistung'].append(None)
                        else:
                            # innerhalb Ladezeit
                            dict_lkw_lastgang['Leistung'].append(P[(i,t_step)].X)
                            dict_lkw_lastgang['Pplus'].append(Pplus[(i,t_step)].X)
                            dict_lkw_lastgang['Pminus'].append(Pminus[(i,t_step)].X)
                            dict_lkw_lastgang['SOC'].append(SoC[(i,t_step)].X)
                            dict_lkw_lastgang['z'].append(z[(i,t_step)].X)
                            dict_lkw_lastgang['Max_Leistung'].append(
                                min(ladeleistung[l[i]], max_lkw_leistung[i])
                            )
                        t_charging += TIMESTEP

                print(f"[Szenario={szenario}, Woche={week}, Strategie={strategie}] Lösung OK. Ladequote: {ladequote_week:.3f}")
            else:
                print(f"[Szenario={szenario}, Woche={week}, Strategie={strategie}] Keine optimale Lösung gefunden.")

    # Nach Schleife: alles als CSV speichern
    df_lastgang = pd.DataFrame(list(lastgang_dict.values()))
    df_lkw_lastgang_df = pd.DataFrame(dict_lkw_lastgang)

    os.makedirs(os.path.join(path, 'data', 'flex', 'lastgang'), exist_ok=True)
    os.makedirs(os.path.join(path, 'data', 'flex', 'lastgang_lkw'), exist_ok=True)

    df_lastgang.to_csv(
        os.path.join(path, 'data', 'flex', 'lastgang', f'lastgang_{szenario}.csv'),
        sep=';', decimal=',', index=False
    )
    df_lkw_lastgang_df.to_csv(
        os.path.join(path, 'data', 'flex', 'lastgang_lkw', f'lastgang_lkw_{szenario}.csv'),
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