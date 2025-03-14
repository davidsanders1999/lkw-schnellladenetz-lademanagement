from gurobipy import Model, GRB, quicksum
import pandas as pd
import time
import os
import config
import logging
logging.basicConfig(filename='logs.log', level=logging.DEBUG, format='%(asctime)s; %(levelname)s; %(message)s')

start = time.time() 


# ======================================================
# 1) Einlesen oder Erzeugen der Basis-Daten
# ======================================================

def modellierung_p_max_min(szenario):
    
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
    
    if dict_szenario['ladequote'] == dict_base['ladequote'] and dict_szenario['cluster'] == dict_base['cluster'] and dict_szenario['pause'] == dict_base['pause']:
        df_lkw = pd.read_csv(os.path.join(path, 'data', 'flex', 'lkws', f'eingehende_lkws_loadstatus_{base_case}.csv'), sep=';', decimal=',')
        df_ladehub = pd.read_csv(os.path.join(path, 'data', 'flex', 'konfiguration_ladehub',f'anzahl_ladesaeulen_{base_case}.csv'), sep=';', decimal=',')
    else:
        df_lkw  = pd.read_csv(os.path.join(path, 'data', 'flex', 'lkws', f'eingehende_lkws_loadstatus_{szenario}.csv'), sep=';', decimal=',')
        df_ladehub = pd.read_csv(os.path.join(path, 'data', 'flex', 'konfiguration_ladehub',f'anzahl_ladesaeulen_{szenario}.csv'), sep=';', decimal=',')

    df_lkw_filtered = df_lkw[(df_lkw['Cluster'] == int(dict_szenario['cluster'])) & (df_lkw['LoadStatus'] == 1)][:].copy()
    
    print(f"Anzahl LKWs: {len(df_lkw_filtered)}")
    
    bidirektional = False if szenario.split('_')[10] == 'M' else True

    
    
    lastgang_dict = {}

    # Zwei Ladestrategien
    ladestrategien = ['p_max', 'p_min']

    for strategie in ladestrategien:
        for t in range(0, 11520, 5):
            # Verwende als Schlüssel das Tupel (Zeit, Ladestrategie)
            key = (t, strategie)
            lastgang_dict[key] = {
                'Zeit': t,
                'Zeit_Time': pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(minutes=t),
                'Leistung_Total': 0,
                'Leistung_Max_Total': 0,
                'Leistung_NCS': 0,
                'Leistung_HPC': 0,
                'Leistung_MCS': 0,
                'Ladestrategie': strategie,
                'Netzanschluss': 0,
                'Ladequote': 0
            }
    
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
    
    list_volladungen = []
        


    # Maximale Leistung pro Ladesäulen-Typ
    ladeleistung = {
        'NCS': int(int(szenario.split('_')[7].split('-')[0])/100 * config.leistung_ladetyp['NCS']),
        'HPC': int(int(szenario.split('_')[7].split('-')[1])/100 * config.leistung_ladetyp['HPC']),
        'MCS': int(int(szenario.split('_')[7].split('-')[2])/100 * config.leistung_ladetyp['MCS'])
    }

    # Verfügbare Anzahl Ladesäulen pro Typ
    max_saeulen = {
        'NCS': int(df_ladehub['NCS'][0]),
        'HPC': int(df_ladehub['HPC'][0]),
        'MCS': int(df_ladehub['MCS'][0])
    }

    netzanschlussfaktor = float(int(szenario.split('_')[5])/100)
    netzanschluss = (max_saeulen['NCS'] * ladeleistung['NCS'] + max_saeulen['HPC'] * ladeleistung['HPC'] + max_saeulen['MCS'] * ladeleistung['MCS']) * netzanschlussfaktor
    dict_geladene_energie = {}
    
    # Gesamter Zeit-Horizont (z.B. 8 Tage à 288 5-Min-Slots pro Tag)
    T = 288 * 8          # = 2304
    Delta_t = 5 / 60.0   # Zeitintervall in Stunden (5 Minuten)

    # ======================================================
    # 2) Schleife über die Ladestrategien
    # ======================================================
    for strategie in ladestrategien:
        # --------------------------------------------------
        # 2.1) LKW-Daten vorbereiten/filtern
        # --------------------------------------------------
        df_lkw_filtered['t_a'] = ((df_lkw_filtered['Ankunftszeit_total']) // 5).astype(int)
        df_lkw_filtered['t_d'] = ((df_lkw_filtered['Ankunftszeit_total'] + df_lkw_filtered['Pausenlaenge'] - 5) // 5).astype(int)
        t_in = df_lkw_filtered['t_a'].tolist()
        t_out = df_lkw_filtered['t_d'].tolist()
        l = df_lkw_filtered['Ladesäule'].tolist()
        SOC_A = df_lkw_filtered['SOC'].tolist()
        kapazitaet = df_lkw_filtered['Kapazitaet'].tolist()
        
        pow_split = szenario.split('_')[6].split('-')
        if len(pow_split) > 1:
            lkw_leistung_skalierung = int(pow_split[1])/100
        else:
            lkw_leistung_skalierung = 1
            
        max_lkw_leistung = [leistung * lkw_leistung_skalierung for leistung in df_lkw_filtered['Max_Leistung'].tolist()]
        SOC_req = df_lkw_filtered['SOC_Target'].tolist()
        ladetyp = df_lkw_filtered['Ladesäule'].tolist()

        # SOC_req = []
        # for index, row in df_lkw_filtered.iterrows():
        #     if row['Ladesäule'] == 'NCS':
        #         SOC_req.append(1)
        #     else:
        #         SOC_req.append(4.5 * 1.26 * 80 / row['Kapazitaet'] + 0.15)
        
        E_req = [kapazitaet[i] * (SOC_req[i] - SOC_A[i]) for i in range(len(df_lkw_filtered))]
        I = len(df_lkw_filtered)
        
        # --------------------------------------------------
        # 2.2) Gurobi-Modell
        # --------------------------------------------------
        model = Model("Ladehub_Optimierung")
        # model.setParam('OutputFlag', 0)
        # model.setParam('MIPGap', 0.1)
        # --------------------------------------------------
        # 2.3) Variablen anlegen
        # --------------------------------------------------
        P = {}
        Pplus = {}
        Pminus = {}
        P_max_i = {}
        P_max_i_2 = {}
        SoC = {}

        z = {}
        
        for i in range(I):
            for t in range(t_in[i], t_out[i] + 1):
                
                if bidirektional:
                    P[(i, t)] = model.addVar(lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS)
                else:
                    P[(i, t)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS)
                    
                Pplus[(i,t)] = model.addVar(lb = 0, vtype=GRB.CONTINUOUS)
                Pminus[(i,t)] = model.addVar(lb = 0, vtype=GRB.CONTINUOUS)
                P_max_i[(i,t)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"Pmax_{i}_{t}")
                P_max_i_2[(i,t)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"Pmax2_{i}_{t}")

                z[(i,t)] = model.addVar(vtype=GRB.BINARY)
            
            for t in range(t_in[i], t_out[i] + 2):
                SoC[(i, t)] = model.addVar(lb=0, ub=1, vtype=GRB.CONTINUOUS, name=f"SoC_{i}_{t}")
        
        # --------------------------------------------------
        # 2.5) Constraints
        # --------------------------------------------------     
        
        # Energiebedarf je LKW decken
        for i in range(I):
            model.addConstr(quicksum(P[(i, t)] * Delta_t for t in range(t_in[i], t_out[i] + 1)) <= E_req[i])        
        
        # Leistungsbegrenzung Ladekurve
        for i in range(I):
            model.addConstr(SoC[(i, t_in[i])] == SOC_A[i])
        for i in range(I):
            for t in range(t_in[i], t_out[i]+1):
                model.addConstr(SoC[(i, t+1)] == SoC[(i, t)] + (P[(i, t)] * Delta_t / kapazitaet[i]))
        
            
            # xvals = [0.0, 0.2, 0.2, 0.3, 0.3, 0.4, 0.4, 0.5, 0.5, 0.6, 0.6, 0.7, 0.7, 0.8, 0.8, 1.0]
            # yvals = [0.957815431, 0.957815431, 0.934481552, 0.934481552, 0.921501434, 0.921501434, 0.872106079, 0.872106079, 0.805719321, 0.805719321, 0.630586501, 0.630586501, 0.531460006, 0.531460006, 0.266505066, 0.266505066]
            																					
            # xvals = [0.0, 0.5, 0.5, 0.8, 0.8, 1.0]
            # yvals = [1300, 1300, 1000, 1000, 500, 500]
        for i in range(I):
            for t in range(t_in[i], t_out[i] + 1):
                ml = max_lkw_leistung[i]
                model.addConstr(P_max_i[(i, t)] == (-0.177038 * SoC[(i, t)] + 0.970903) * ml)
                model.addConstr(P_max_i_2[(i, t)] == (-1.51705 * SoC[(i, t)] + 1.6336) * ml)
                    
            for t in range(t_in[i], t_out[i] + 1):
                model.addConstr(Pplus[(i,t)] <= P_max_i[(i,t)] * z[(i,t)])
                model.addConstr(Pminus[(i,t)] <= P_max_i[(i,t)] * (1-z[(i,t)]))
                
                model.addConstr(Pplus[(i,t)] <= P_max_i_2[(i,t)] * z[(i,t)])
                model.addConstr(Pminus[(i,t)] <= P_max_i_2[(i,t)] * (1-z[(i,t)]))
                    

        # Leistungsbegrenzung Ladesäulen-Typ    
        for i in range(I):
            typ = l[i]
            P_max_l = ladeleistung[typ]
            for t in range(t_in[i], t_out[i] + 1):
                model.addConstr(Pplus[(i,t)] <= z[(i,t)]     * P_max_l)
                model.addConstr(Pminus[(i,t)] <= (1-z[(i,t)]) * P_max_l)
        
        # Leistungsbegrenzung Netzanschluss
        for t in range(T):
            model.addConstr(quicksum(Pplus[(i, t)] + Pminus[(i, t)] for i in range(I) if t_in[i] <= t <= t_out[i]) <= netzanschluss)    
        
        # Hilfsbedingungen
        for i in range(I):
            for t in range(t_in[i], t_out[i]+1):
                model.addConstr(P[(i,t)] == Pplus[(i,t)] - Pminus[(i,t)])
                
            for t in range(t_in[i], t_out[i]):
                model.addConstr(z[(i, t+1)] >= z[(i, t)])
        
        # --------------------------------------------------
        # 2.4) Zielfunktion
        # --------------------------------------------------
        if strategie == 'p_max':
            obj_expr = quicksum(((1/t) * (Pplus[(i, t)])) - (t * Pminus[(i, t)]) for i in range(I) for t in range(t_in[i], t_out[i] + 1))
            # obj_expr = quicksum((t * (-Pplus[(i, t)])) for i in range(I) for t in range(t_in[i], t_out[i] + 1))
            model.setObjective(obj_expr, GRB.MAXIMIZE)
        elif strategie == 'p_min':
            obj_expr = quicksum((t * Pplus[(i, t)]) - (t * Pminus[(i, t)]) for i in range(I) for t in range(t_in[i], t_out[i] + 1))
            model.setObjective(obj_expr, GRB.MAXIMIZE)
        
        # --------------------------------------------------
        # 2.6) Optimierung
        # --------------------------------------------------
        model.optimize()
        
        # --------------------------------------------------
        # 2.7) Ergebnisse in df_lastgang übernehmen
        # --------------------------------------------------
        if model.Status == GRB.OPTIMAL:
            print(f"Optimale Lösung für {strategie} gefunden.")
            
            for i in range(I):
                if (SoC[(i, t_out[i]+1)].X >= SOC_req[i]-0.01):
                    list_volladungen.append(1)
                else:
                    list_volladungen.append(0)
            
            for t in range(T):  # T entspricht hier der Anzahl der Zeitschritte (z.B. 2304)
                sum_p_total = 0
                sum_p_total_max = 0
                sum_p_ncs = 0
                sum_p_hpc = 0
                sum_p_mcs = 0
                
                # Summierung der Ladeleistungen über alle LKWs
                for i in range(I):
                    if t_in[i] <= t <= t_out[i]:
                        sum_p_total += P[(i, t)].X
                        sum_p_total_max += ladeleistung[l[i]]
                        if l[i] == 'NCS':
                            sum_p_ncs += P[(i, t)].X
                        elif l[i] == 'HPC':
                            sum_p_hpc += P[(i, t)].X
                        elif l[i] == 'MCS':
                            sum_p_mcs += P[(i, t)].X
                
                # Beachte: Im Dictionary ist 'Zeit' in Minuten gespeichert, daher verwenden wir t*5
                key = (t*5, strategie)
                lastgang_dict[key]['Netzanschluss'] = netzanschluss
                lastgang_dict[key]['Leistung_Total'] += sum_p_total
                lastgang_dict[key]['Leistung_Max_Total'] += sum_p_total_max
                lastgang_dict[key]['Leistung_NCS'] += sum_p_ncs
                lastgang_dict[key]['Leistung_HPC'] += sum_p_hpc
                lastgang_dict[key]['Leistung_MCS'] += sum_p_mcs
                lastgang_dict[key]['Ladequote'] = sum(list_volladungen)/len(list_volladungen)

            
            for i in range(I):
                t_charging = 0
                for t in range(T):   
                    if t_in[i] <= t <= t_out[i]+1:
                        dict_lkw_lastgang['Ladestrategie'].append(strategie)
                        dict_lkw_lastgang['LKW_ID'].append(df_lkw_filtered.iloc[i]['Nummer'])
                        dict_lkw_lastgang['Zeit'].append(t*5)
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
            
            
            
            print(f"Ladequote: {sum(list_volladungen)/len(list_volladungen)}")
            print(f"Geladene Energie: {sum(P[(i, t)].X for i in range(I) for t in range(t_in[i], t_out[i] + 1))}")
            dict_geladene_energie[strategie] = sum(P[(i, t)].X for i in range(I) for t in range(t_in[i], t_out[i] + 1))
        else:
            print(f"Keine optimale Lösung für {strategie} gefunden.")
    
    
    print(f"Energiediffernz: {dict_geladene_energie['p_max'] - dict_geladene_energie['p_min']}")
    
    # Create directories if they do not exist
    os.makedirs(os.path.join(path, 'data', 'flex', 'lastgang'), exist_ok=True)
    os.makedirs(os.path.join(path, 'data', 'flex', 'lastgang_lkw'), exist_ok=True)
    
    df_lkw_lastgang = pd.DataFrame(dict_lkw_lastgang)
    df_lkw_lastgang.sort_values(by=['Ladestrategie','LKW_ID', 'Zeit'], inplace=True)
    
    df_lastgang = pd.DataFrame(list(lastgang_dict.values()))                        
    df_lastgang.to_csv(os.path.join(path, 'data', 'flex', 'lastgang', f'lastgang_{szenario}.csv'), sep=';', decimal=',', index=False) 
    df_lkw_lastgang.to_csv(os.path.join(path, 'data', 'flex', 'lastgang_lkw', f'lastgang_lkw_{szenario}.csv'), sep=';', decimal=',', index=False)
    return None

def main():
    for szenario in config.list_szenarien:
        print(f"Optimierung P_max/P_min: {szenario}")
        logging.info(f"Optimierung P_max/P_min: {szenario}")
        modellierung_p_max_min(szenario)        
    
    
if __name__ == '__main__':
    
    start = time.time()
    main()
    end = time.time()
    
    print(f"Laufzeit: {end - start} Sekunden")