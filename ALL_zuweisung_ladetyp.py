# ======================================================
# Benötigte Bibliotheken importieren
# ======================================================
import pandas as pd
import numpy as np
import os
from scipy.interpolate import interp1d
import config as config_file

# Zufalls-Seed setzen für Reproduzierbarkeit
np.random.seed(42)

# ======================================================
# Hauptfunktion der Simulation
# ======================================================
def main():
    """
    Hauptfunktion zum Ausführen der LKW-Simulationspipeline.
    """
    # Konfigurationen und Input-Daten laden
    CONFIG = load_configurations()
    df_verteilungsfunktion, df_ladevorgaenge_daily = load_input_data(CONFIG['path'])

    # LKW-Daten generieren
    df_lkws = generate_truck_data(CONFIG, df_verteilungsfunktion, df_ladevorgaenge_daily)
    print("LKW-Daten erfolgreich generiert.")
    
    # Ladesäulen zuweisen
    df_lkws = assign_charging_stations(df_lkws, CONFIG)

    # Daten finalisieren und exportieren
    finalize_and_export_data(df_lkws, CONFIG)

    # Auswertung der Ladesäulenarten
    analyze_charging_types(df_lkws)

# ======================================================
# Konfigurationen & Inputdaten laden
# ======================================================
def load_configurations():
    """
    Lädt und gibt die Konfigurationen für die Simulation zurück.
    """
    path = os.path.dirname(os.path.abspath(__file__))
    freq = 5  # Frequenz in Minuten
    return {
        'path': path,
        'freq': freq,
        'year': 2024,
        'lkw_id':{
            '1': 0.093,
            '2': 0.187,
            '3': 0.289,
            '4': 0.431
        },
        'kapazitaeten_lkws': {
            '1': 600,
            '2': 720,
            '3': 840,
            '4': 960
        },
        'leistungen_lkws': {
            '1': 750,
            '2': 750,
            '3': 1200,
            '4': 1200
        },
        'pausentypen': ['Schnelllader', 'Nachtlader'],
        'pausenzeiten_lkws': {
            'Schnelllader': 45,
            'Nachtlader': 540
        },
        'leistung': {'HPC': 350, 'NCS': 100, 'MCS': 1000},
        'energie_pro_abschnitt': 80 * 4.5 * 1.26,  # Energiebedarf in Wh
        'sicherheitspuffer': 0.1  # Sicherheitsaufschlag
    }

def load_input_data(path):
    """
    Lädt die Inputdaten aus CSV-Dateien.
    """
    df_verteilungsfunktion = pd.read_csv(
        os.path.join(path, 'input/verteilungsfunktion_mcs-ncs.csv'), sep=','
    )
    df_ladevorgaenge_daily = pd.read_csv(
        os.path.join(path, 'input/ladevorgaenge_daily_cluster.csv'), sep=';', decimal=','
    )
    return df_verteilungsfunktion, df_ladevorgaenge_daily

# ======================================================
# Hilfsfunktionen
# ======================================================
def get_soc(ankunftszeit):
    """
    Berechnet den Ladezustand (SOC) basierend auf der Ankunftszeit.
    """
    if ankunftszeit < 360:
        soc = 0.2 + np.random.uniform(-0.1, 0.1)
    else:
        soc = -(0.00028) * ankunftszeit + 0.6
        soc += np.random.uniform(-0.1, 0.1)
    return soc

def get_leistungsfaktor(soc):
    """
    Bestimmt den Leistungsfaktor abhängig vom SOC.
    """
    return min(-0.177038 * soc + 0.970903, -1.51705 * soc + 1.6336)

def tage_im_jahr(jahr):
    """
    Gibt die Anzahl der Tage im Jahr zurück.
    """
    return pd.date_range(start=f"{jahr}-01-01", end=f"{jahr}-12-31", freq="D").size

def wochentag_im_jahr(nummer, jahr):
    """
    Gibt den Wochentag für eine bestimmte Tagesnummer im Jahr zurück (Montag=1).
    """
    date = pd.to_datetime(f"{jahr}-01-01") + pd.Timedelta(days=nummer)
    return date.weekday() + 1

# ======================================================
# LKW-Daten generieren
# ======================================================
def generate_truck_data(config, df_verteilungsfunktion, df_ladevorgaenge_daily):
    """
    Generiert LKW-Daten basierend auf Konfiguration und Inputdaten.
    """
    dict_lkws = {
        'Cluster': [], 'Tag': [], 'Ankunftszeit': [], 'Nummer': [],
        'Pausentyp': [], 'Kapazitaet': [], 'Max_Leistung': [], 'SOC': [],
        'SOC_Target': [], 'Pausenlaenge': [], 'Lkw_ID': []
    }

    for cluster_id in range(1, 4):
        horizon = 7 if config_file.mode == 'flex' else (tage_im_jahr(config['year']) - 1)
        
        for day in range(horizon):
            wochentag = wochentag_im_jahr(day, config['year'])
            anzahl_lkws = {
                pausentyp: df_ladevorgaenge_daily[
                    (df_ladevorgaenge_daily['Cluster'] == cluster_id) &
                    (df_ladevorgaenge_daily['Wochentag'] == wochentag) &
                    (df_ladevorgaenge_daily['Ladetype'] == pausentyp)
                ]['Anzahl'].values[0]
                for pausentyp in config['pausentypen']
            }

            for pausentyp in config['pausentypen']:
                for _ in range(int(anzahl_lkws[pausentyp])):
                    lkw_id = np.random.choice(list(config['lkw_id'].keys()), p=list(config['lkw_id'].values()))
                    pausenzeit = config['pausenzeiten_lkws'][pausentyp]
                    kapazitaet = config['kapazitaeten_lkws'][lkw_id]
                    leistung = config['leistungen_lkws'][lkw_id]
                    minuten = np.random.choice(df_verteilungsfunktion['Zeit'], p=df_verteilungsfunktion[pausentyp])
                    soc = get_soc(minuten)

                    soc_target = 1.0 if pausentyp == 'Nachtlader' else min(
                        max(config['energie_pro_abschnitt'] / kapazitaet + config['sicherheitspuffer'], soc), 1.0
                    )

                    # Einfügen in Dictionary
                    dict_lkws['Cluster'].append(cluster_id)
                    dict_lkws['Tag'].append(day + 1)
                    dict_lkws['Kapazitaet'].append(kapazitaet)
                    dict_lkws['Max_Leistung'].append(leistung)
                    dict_lkws['Nummer'].append(None)
                    dict_lkws['SOC'].append(soc)
                    dict_lkws['SOC_Target'].append(soc_target)
                    dict_lkws['Pausentyp'].append(pausentyp)
                    dict_lkws['Pausenlaenge'].append(pausenzeit)
                    dict_lkws['Ankunftszeit'].append(minuten)
                    dict_lkws['Lkw_ID'].append(int(lkw_id))

    df_lkws = pd.DataFrame(dict_lkws)
    df_lkws.sort_values(by=['Cluster', 'Tag', 'Ankunftszeit'], inplace=True)
    df_lkws.reset_index(drop=True, inplace=True)
    df_lkws['Nummer'] = df_lkws.groupby('Cluster').cumcount() + 1
    df_lkws['Nummer'] = df_lkws['Nummer'].apply(lambda x: f'{x:04}')
    return df_lkws

# ======================================================
# Ladesäulen zuweisen
# ======================================================
def assign_charging_stations(df_lkws, config):
    """
    Weist Ladesäulen basierend auf SOC und Ladezeiten zu.
    """
    df_lkws['Ladesäule'] = None
    nicht_erfüllt = 0

    for index in range(len(df_lkws)):
        kapazitaet = float(df_lkws.loc[index, 'Kapazitaet'])
        soc_init = df_lkws.loc[index, 'SOC']
        pausentyp = df_lkws.loc[index, 'Pausentyp']
        pausenzeit = df_lkws.loc[index, 'Pausenlaenge']
        max_leistung_lkw = df_lkws.loc[index, 'Max_Leistung']
        soc_target = df_lkws.loc[index, 'SOC_Target']

        if pausentyp == 'Nachtlader':
            df_lkws.loc[index, 'Ladesäule'] = 'NCS'
            continue
        
        if soc_target < soc_init:
            print(f"⚠️ Achtung: LKW {df_lkws.loc[index, 'Nummer']} hat Ziel-SOC < Initial-SOC!")

        ladezeiten = {}
        for station, leistung_init in config['leistung'].items():
            ladezeit = 0
            soc = soc_init
            while soc < soc_target:
                ladezeit += config['freq']
                leistungsfaktor = get_leistungsfaktor(soc)
                aktuelle_leistung = min(leistung_init, leistungsfaktor * max_leistung_lkw)
                energie = aktuelle_leistung * config['freq'] / 60
                soc += energie / kapazitaet
            ladezeiten[station] = pausenzeit - ladezeit

        if ladezeiten['HPC'] >= 0:
            df_lkws.loc[index, 'Ladesäule'] = 'HPC'
        elif ladezeiten['MCS'] >= 0:
            df_lkws.loc[index, 'Ladesäule'] = 'MCS'
        else:
            df_lkws.loc[index, 'Ladesäule'] = 'MCS'
            nicht_erfüllt += 1

    if nicht_erfüllt > 0:
        print(f"⚠️ {nicht_erfüllt} Ladevorgänge konnten innerhalb der Pausenzeit nicht vollständig erfüllt werden.")

    # Ausgabe der Verteilung der LKW-IDs
    anteile = df_lkws['Lkw_ID'].value_counts(normalize=True).sort_index().to_dict()
    print("Verteilung der LKW-Typen:", anteile)

    return df_lkws

# ======================================================
# Daten finalisieren und exportieren
# ======================================================
def finalize_and_export_data(df_lkws, config):
    """
    Ergänzt Zeitspalten, sortiert und exportiert die Ergebnisse als CSV.
    """
    df_lkws['Zeit_DateTime'] = pd.to_datetime(
        df_lkws['Ankunftszeit'] + ((df_lkws['Tag'] - 1) * 1440),
        unit='m', origin='2024-01-01'
    )
    df_lkws['Ankunftszeit_total'] = df_lkws['Ankunftszeit'] + ((df_lkws['Tag'] - 1) * 1440)
    df_lkws['Wochentag'] = df_lkws['Zeit_DateTime'].dt.weekday
    df_lkws['KW'] = df_lkws['Zeit_DateTime'].dt.isocalendar().week
    df_lkws.loc[(df_lkws['Tag'] > 300) & (df_lkws['KW'] == 1), 'KW'] = 53

    df_lkws.sort_values(by=['Cluster', 'Zeit_DateTime'], inplace=True)

    df_lkws = df_lkws[[
        'Cluster', 'Zeit_DateTime', 'Ankunftszeit_total', 'Tag', 'KW', 'Wochentag',
        'Ankunftszeit', 'Nummer', 'Pausentyp', 'Kapazitaet', 'Max_Leistung',
        'SOC', 'SOC_Target', 'Pausenlaenge', 'Lkw_ID', 'Ladesäule'
    ]]

    output_dir = os.path.join(config['path'], 'data', config_file.mode, 'lkw_eingehend')
    os.makedirs(output_dir, exist_ok=True)

    df_lkws.to_csv(
        os.path.join(output_dir, 'eingehende_lkws_ladesaeule.csv'),
        sep=';', decimal=','
    )

# ======================================================
# Auswertung der Ladesäulenarten
# ======================================================
def analyze_charging_types(df_lkws):
    """
    Gibt die Anzahl der verwendeten Ladesäulenarten aus.
    """
    df_ladetypen = df_lkws.groupby('Ladesäule').size().reset_index(name='Anzahl')
    print(df_ladetypen)

# ======================================================
# Starte das Hauptprogramm
# ======================================================
if __name__ == "__main__":
    main()