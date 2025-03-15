# ======================================================
# Importing Required Libraries
# ======================================================
import pandas as pd
import numpy as np
import os
from scipy.interpolate import interp1d
import config as config_file

np.random.seed(42)

# ======================================================
# Main Function
# ======================================================
def main():
    """
    Main function to execute the truck simulation pipeline.
    """
    # Load configurations and data
    CONFIG = load_configurations()
    df_verteilungsfunktion, df_ladevorgaenge_daily = load_input_data(CONFIG['path'])

    # Generate truck data
    df_lkws = generate_truck_data(CONFIG, df_verteilungsfunktion, df_ladevorgaenge_daily)
    print("Truck data generated successfully.")
    
    # Assign charging stations
    df_lkws = assign_charging_stations(df_lkws, CONFIG)

    # Add datetime and export results
    finalize_and_export_data(df_lkws, CONFIG)

    # Analyze charging types
    analyze_charging_types(df_lkws)

# ======================================================
# Configuration and Input Data
# ======================================================
def load_configurations():
    """
    Load and return the configurations for the simulation.
    """
    path = os.path.dirname(os.path.abspath(__file__))
    freq = 5  # Frequency of updates (in minutes)
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
        'energie_pro_abschnitt': 80 * 4.5 * 1.26,
        'sicherheitspuffer': 0.1
    }

def load_input_data(path):
    """
    Load input data from CSV files.
    """
    df_verteilungsfunktion = pd.read_csv(
        os.path.join(path, 'input/verteilungsfunktion_mcs-ncs.csv'), sep=','
    )
    df_ladevorgaenge_daily = pd.read_csv(
        os.path.join(path, 'input/ladevorgaenge_daily_cluster.csv'), sep=';', decimal=','
    )
    return df_verteilungsfunktion, df_ladevorgaenge_daily

# ======================================================
# Helper Functions
# ======================================================
def get_soc(ankunftszeit):
    """
    Calculate the State of Charge (SOC) based on arrival time.
    """
    if ankunftszeit < 360:  # Early morning
        soc = 0.2 + np.random.uniform(-0.1, 0.1)
    else:
        soc = -(0.00028) * ankunftszeit + 0.6
        soc += np.random.uniform(-0.1, 0.1)
    
    # soc = 0.2 + np.random.uniform(-0.1, 0.1)
      
    return soc

def get_leistungsfaktor(soc):
    """
    Adjust power factor based on SOC using the minimum of two linear functions.
    """
    return min(-0.177038 * soc + 0.970903, -1.51705 * soc + 1.6336)

def tage_im_jahr(jahr):
    return pd.date_range(start=f"{jahr}-01-01", end=f"{jahr}-12-31", freq="D").size

def wochentag_im_jahr(nummer, jahr):
    """
    Return the weekday for a given day number in a specific year.
    """
    date = pd.to_datetime(f"{jahr}-01-01") + pd.Timedelta(days=nummer)
    return date.weekday() + 1  # Monday is 1 and Sunday is 7


# ======================================================
# Truck Data Generation
# ======================================================
def generate_truck_data(config, df_verteilungsfunktion, df_ladevorgaenge_daily):
    """
    Generate truck data based on the input configurations.
    """
    dict_lkws = {
        'Cluster': [],
        'Tag': [],
        'Ankunftszeit': [],
        'Nummer': [],
        'Pausentyp': [],
        'Kapazitaet': [],
        'Max_Leistung': [],
        'SOC': [],
        'SOC_Target': [],
        'Pausenlaenge': [],
        'Lkw_ID': []
    }

    for cluster_id in range(1, 4):  # Loop through clusters
        
        horizon = (7 if config_file.mode == 'flex' else tage_im_jahr(config['year']))
        
        for day in range(horizon):  # Loop through days
            wochentag = wochentag_im_jahr(day, config['year'])
            anzahl_lkws = {
                pausentyp: df_ladevorgaenge_daily[(df_ladevorgaenge_daily['Cluster'] == cluster_id) & (df_ladevorgaenge_daily['Wochentag'] == wochentag) & (df_ladevorgaenge_daily['Ladetype'] == pausentyp)]['Anzahl'].values[0]
                for pausentyp in config['pausentypen']
            }
            for pausentyp in config['pausentypen']:  # Loop through break types
                for _ in range(int(anzahl_lkws[pausentyp])):
                    lkw_id = np.random.choice(
                        list(config['lkw_id'].keys()),
                        p=list(config['lkw_id'].values())
                    )
                    
                    pausenzeit = config['pausenzeiten_lkws'][pausentyp]
                    kapazitaet = config['kapazitaeten_lkws'][lkw_id]
                    leistung = config['leistungen_lkws'][lkw_id]
                    minuten = np.random.choice(
                        df_verteilungsfunktion['Zeit'],
                        p=df_verteilungsfunktion[pausentyp]
                    )
                    soc = get_soc(minuten)
                    
                    if pausentyp == 'Nachtlader':
                        soc_target = 1.0
                    else:
                        soc_target = config['energie_pro_abschnitt'] / kapazitaet + config['sicherheitspuffer']
                        soc_target = min(soc_target, 1.0)
                        soc_target = max(soc_target, soc)
                    
                    dict_lkws['Cluster'].append(cluster_id)
                    dict_lkws['Tag'].append(day + 1)
                    dict_lkws['Kapazitaet'].append(kapazitaet)
                    dict_lkws['Max_Leistung'].append(leistung)
                    dict_lkws['Nummer'].append(None)  # Placeholder for ID
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
# Assign Charging Stations
# ======================================================
def assign_charging_stations(df_lkws, config):
    """
    Assign charging stations to each truck based on configurations.
    """
    df_lkws['Ladesäule'] = None
    count = 0
    for index in range(len(df_lkws)):
        
        kapazitaet = float(df_lkws.loc[index, 'Kapazitaet'])
        soc_init = df_lkws.loc[index, 'SOC']
        pausentyp = df_lkws.loc[index, 'Pausentyp']
        pausenzeit = df_lkws.loc[index, 'Pausenlaenge']
        max_leistung_lkw = df_lkws.loc[index, 'Max_Leistung']
        soc_target = df_lkws.loc[index, 'SOC_Target']
        df_lkws.loc[index, 'SOC_Target'] = soc_target

        if pausentyp == 'Nachtlader':
            df_lkws.loc[index, 'Ladesäule'] = 'NCS'
            continue
        
        if soc_target < soc_init:
            print(f"Warning: Truck {df_lkws.loc[index, 'Nummer']} has a target SOC less than initial SOC!")
            # raise ValueError("Error: Target SOC is less than initial SOC!")

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
            count += 1
    if count > 0:
        print(f"Warning: {count} trucks have been assigned to MCS due to insufficient charging capacity.")
        
    dict_anteile = {
        1: df_lkws[df_lkws['Lkw_ID'] == 1].shape[0] / df_lkws.shape[0],
        2: df_lkws[df_lkws['Lkw_ID'] == 2].shape[0] / df_lkws.shape[0],
        3: df_lkws[df_lkws['Lkw_ID'] == 3].shape[0] / df_lkws.shape[0],
        4: df_lkws[df_lkws['Lkw_ID'] == 4].shape[0] / df_lkws.shape[0]
    }

    print(dict_anteile)
    
    return df_lkws

# ======================================================
# Finalize and Export Data
# ======================================================
def finalize_and_export_data(df_lkws, config):
    """
    Finalize the DataFrame, add datetime, and export to a CSV file.
    """
    df_lkws['Zeit_DateTime'] = pd.to_datetime(
        df_lkws['Ankunftszeit'] + ((df_lkws['Tag'] - 1) * 1440),
        unit='m',
        origin='2024-01-01'
    )
    df_lkws['Ankunftszeit_total'] = df_lkws['Ankunftszeit'] + ((df_lkws['Tag'] - 1) * 1440)
    df_lkws['Wochentag'] = df_lkws['Zeit_DateTime'].dt.weekday
    df_lkws['KW'] = df_lkws['Zeit_DateTime'].dt.isocalendar().week
    df_lkws.loc[(df_lkws['Tag'] > 300) & (df_lkws['KW'] == 1), 'KW'] = 53
    df_lkws.sort_values(by=['Cluster', 'Zeit_DateTime'], inplace=True)
    # Reorder the columns
    df_lkws = df_lkws[[
        'Cluster',  'Zeit_DateTime', 'Ankunftszeit_total', 'Tag',  'KW','Wochentag',
        'Ankunftszeit', 'Nummer', 'Pausentyp', 'Kapazitaet', 'Max_Leistung', 'SOC',
        'SOC_Target', 'Pausenlaenge', 'Lkw_ID', 'Ladesäule'
    ]]
    
    # Ensure the directories exist
    output_dir = os.path.join(config['path'], 'data', config_file.mode, 'lkw_eingehend')
    os.makedirs(output_dir, exist_ok=True)

    # Export the DataFrame to a CSV file
    df_lkws.to_csv(
        os.path.join(output_dir, 'eingehende_lkws_ladesaeule.csv'),
        sep=';', decimal=','
    )

# ======================================================
# Analyze Charging Types
# ======================================================
def analyze_charging_types(df_lkws):
    """
    Analyze and print the proportion of each charging type.
    """
    df_ladetypen = df_lkws.groupby('Ladesäule').size().reset_index(name='Anzahl')
    print(df_ladetypen)

# ======================================================
# Main Execution
# ======================================================
if __name__ == "__main__":
    main()