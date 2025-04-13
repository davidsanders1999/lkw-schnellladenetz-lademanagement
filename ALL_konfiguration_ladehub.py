# ======================================================
# Bibliotheken importieren
# ======================================================
import pandas as pd
import numpy as np
import networkx as nx
import os
import config
import logging

# Logging-Konfiguration
logging.basicConfig(
    filename='logs.log',
    level=logging.DEBUG,
    format='%(asctime)s; %(levelname)s; %(message)s'
)

# ======================================================
# Datenimport-Funktion
# ======================================================
def datenimport():
    """
    Liest die eingehenden LKW-Daten aus der CSV-Datei ein.
    Erstellt die benötigten Verzeichnisse, falls nicht vorhanden.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'flex')
    os.makedirs(os.path.join(path, 'lkw_eingehend'), exist_ok=True)

    file_path = os.path.join(path, 'lkw_eingehend', 'eingehende_lkws_ladesaeule.csv')
    df_eingehende_lkws = pd.read_csv(file_path, sep=';', decimal=',', index_col=0)
    return df_eingehende_lkws

# ======================================================
# Netzwerk-Aufbau für LKW-Flussmodellierung
# ======================================================
def build_flow_network(df_filter, anzahl_ladesaeulen):
    """
    Erstellt ein gerichtetes Flussnetzwerk (DiGraph) für die LKWs.
    
    - Jeder LKW wird als zwei Knoten dargestellt: _arr (Ankunft) & _dep (Abfahrt).
    - Zeitliche Knoten im 5-Minuten-Raster verbinden die Ereignisse.
    - Es gibt eine SuperSource (S) und einen SuperSink (T) für den Fluss.
    - Die Kapazität der Zeitkanten entspricht der Anzahl verfügbarer Ladesäulen.
    """
    G = nx.DiGraph()
    S, T = 'SuperSource', 'SuperSink'
    G.add_node(S)
    G.add_node(T)

    # Effektive Zeitachsenberechnung: Ankunft + Wochentagsverschiebung
    df_filter = df_filter.copy()
    df_filter['EffectiveArrival'] = df_filter['Ankunftszeit'] + (df_filter['Wochentag'] - 1) * 1440
    df_filter['EffectiveDeparture'] = df_filter['EffectiveArrival'] + df_filter['Pausenlaenge'] + 5  # Pufferzeit

    start = int(df_filter['EffectiveArrival'].min())
    ende  = int(df_filter['EffectiveDeparture'].max())
    times = list(range(start, ende + 1, 5))

    # Zeitknoten und Kanten hinzufügen
    for t in times:
        G.add_node(f"time_{t}")
    G.add_edge(S, f"time_{times[0]}", capacity=anzahl_ladesaeulen, weight=0)
    G.add_edge(f"time_{times[-1]}", T, capacity=anzahl_ladesaeulen, weight=0)

    for i in range(len(times) - 1):
        G.add_edge(f"time_{times[i]}", f"time_{times[i+1]}", capacity=anzahl_ladesaeulen, weight=10)

    # LKW-Knoten hinzufügen
    for idx, row in df_filter.iterrows():
        lkw_id = row['Nummer']
        lkw_arr, lkw_dep = f"LKW{lkw_id}_arr", f"LKW{lkw_id}_dep"

        G.add_node(lkw_arr)
        G.add_node(lkw_dep)

        arrival_node = f"time_{int(row['EffectiveArrival'])}"
        departure_node = f"time_{int(row['EffectiveDeparture'])}"

        G.add_edge(arrival_node, lkw_arr, capacity=1, weight=0)
        G.add_edge(lkw_dep, departure_node, capacity=1, weight=0)
        G.add_edge(lkw_arr, lkw_dep, capacity=1, weight=0)

    # Flussberechnung mit minimalen Kosten
    flow_dict = nx.max_flow_min_cost(G, S, T)
    return flow_dict

# ======================================================
# Ladehub-Konfiguration
# ======================================================
def konfiguration_ladehub(df_eingehende_lkws, szenario):
    """
    Ermittelt pro Ladesäulentyp (HPC, MCS, NCS) die notwendige Anzahl an Ladesäulen,
    um eine definierte Ladequote zu erfüllen. Zusätzlich wird für jeden LKW
    festgehalten, ob er geladen wurde (LoadStatus).
    """
    df_eingehende_lkws_loadstatus = pd.DataFrame()

    # Szenarioparameter extrahieren
    cluster = int(szenario.split('_')[1])
    dict_ladequoten = {
        'NCS': float(szenario.split('_')[3].split('-')[0]) / 100,
        'HPC': float(szenario.split('_')[3].split('-')[1]) / 100,
        'MCS': float(szenario.split('_')[3].split('-')[2]) / 100
    }
    dict_ladezeit = {
        'Schnell': int(szenario.split('_')[9].split('-')[0]),
        'Nacht': int(szenario.split('_')[9].split('-')[1])
    }

    # Falls Ladezeiten von Standardwerten abweichen, anpassen
    if dict_ladezeit['Schnell'] != 45 or dict_ladezeit['Nacht'] != 540:
        for idx, row in df_eingehende_lkws.iterrows():
            if row['Pausentyp'] == 'Nachtlader':
                df_eingehende_lkws.loc[idx, 'Pausenlaenge'] = dict_ladezeit['Nacht']
            elif row['Pausentyp'] == 'Schnelllader':
                df_eingehende_lkws.loc[idx, 'Pausenlaenge'] = dict_ladezeit['Schnell']
            else:
                raise ValueError(f"Unbekannter Pausentyp: {row['Pausentyp']}")

    df_anzahl_ladesaeulen = pd.DataFrame(columns=[
        'Cluster','NCS','Ladequote_NCS','HPC','Ladequote_HPC','MCS','Ladequote_MCS'
    ])
    df_konf_optionen = pd.DataFrame(columns=[
        'Ladetype','Anzahl_Ladesaeulen','Ladequote','LKW_pro_Ladesaeule'
    ])

    for ladetyp in dict_ladequoten:
        zielquote = dict_ladequoten[ladetyp]

        # Relevante LKW filtern
        df_filter = df_eingehende_lkws[
            (df_eingehende_lkws['Cluster'] == cluster) &
            (df_eingehende_lkws['Ladesäule'] == ladetyp)
        ]

        anzahl_lkw = len(df_filter)
        ladequote = 0
        anzahl_ladesaeulen = 1

        for durchgang in range(anzahl_lkw):
            flow_dict = build_flow_network(df_filter, anzahl_ladesaeulen)

            # Zähle geladene LKW
            geladen = sum(
                flow_dict.get(f"LKW{row['Nummer']}_arr", {}).get(f"LKW{row['Nummer']}_dep", 0)
                for idx, row in df_filter.iterrows()
            )

            ladequote = geladen / anzahl_lkw
            lkw_pro_saeule = geladen / anzahl_ladesaeulen / 7

            # Dokumentation
            df_konf_optionen.loc[len(df_konf_optionen)] = [
                ladetyp, anzahl_ladesaeulen, ladequote, lkw_pro_saeule
            ]
            print(f"[{ladetyp}] | Säulen: {anzahl_ladesaeulen}, Ladequote: {ladequote:.2%}, LKW/Säule: {lkw_pro_saeule:.2f}")

            if ladequote >= zielquote:
                statusliste = []
                for idx, row in df_filter.iterrows():
                    val = flow_dict.get(f"LKW{row['Nummer']}_arr", {}).get(f"LKW{row['Nummer']}_dep", 0)
                    statusliste.append(1 if val > 0 else 0)
                df_filter = df_filter.copy()
                df_filter['LoadStatus'] = statusliste
                df_eingehende_lkws_loadstatus = pd.concat([df_eingehende_lkws_loadstatus, df_filter])
                break
            else:
                anzahl_ladesaeulen = int(np.ceil(anzahl_ladesaeulen / ladequote * zielquote))

        df_anzahl_ladesaeulen.loc[0, 'Cluster'] = cluster
        df_anzahl_ladesaeulen.loc[0, ladetyp] = anzahl_ladesaeulen
        df_anzahl_ladesaeulen.loc[0, f'Ladequote_{ladetyp}'] = ladequote

    # Ergebnisse speichern
    pfad_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'flex')
    os.makedirs(os.path.join(pfad_base, 'konfiguration_ladehub'), exist_ok=True)
    os.makedirs(os.path.join(pfad_base, 'lkws'), exist_ok=True)
    os.makedirs(os.path.join(pfad_base, 'konf_optionen'), exist_ok=True)

    df_anzahl_ladesaeulen.to_csv(
        os.path.join(pfad_base, 'konfiguration_ladehub', f'anzahl_ladesaeulen_{szenario}.csv'),
        sep=';', decimal=','
    )
    df_eingehende_lkws_loadstatus.to_csv(
        os.path.join(pfad_base, 'lkws', f'eingehende_lkws_loadstatus_{szenario}.csv'),
        sep=';', decimal=','
    )
    df_konf_optionen.to_csv(
        os.path.join(pfad_base, 'konf_optionen', f'konf_optionen_{szenario}.csv'),
        sep=';', decimal=',', index=False
    )

# ======================================================
# Hauptfunktion zur Szenariodurchführung
# ======================================================
def main():
    logging.info('Start: Ladehub-Konfiguration')
    df_eingehende_lkws = datenimport()

    for szenario in config.list_szenarien:
        dict_base = {
            'name': 'Base',
            'ladequote': '80-80-80',
            'cluster': '2',
            'pause': '45-540'
        }

        dict_szenario = {
            'name': szenario.split('_')[12],
            'ladequote': szenario.split('_')[3],
            'cluster': szenario.split('_')[1],
            'pause': szenario.split('_')[9]
        }

        if (
            dict_szenario['ladequote'] == dict_base['ladequote']
            and dict_szenario['cluster'] == dict_base['cluster']
            and dict_szenario['pause'] == dict_base['pause']
            and dict_szenario['name'] != dict_base['name']
        ):
            logging.info(f"Konfiguration übersprungen: {szenario}")
            print(f"Konfiguration übersprungen: {szenario}")
        else:
            logging.info(f"Konfiguration wird ausgeführt: {szenario}")
            print(f"Konfiguration Hub: {szenario}")
            konfiguration_ladehub(df_eingehende_lkws, szenario)

# ======================================================
# Ausführung
# ======================================================
if __name__ == '__main__':
    main()