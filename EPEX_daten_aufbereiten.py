# ======================================================
# Benötigte Bibliotheken importieren
# ======================================================
import pandas as pd
import os
import time
import config

# ======================================================
# Funktion: Kostenvergleich pro Woche
# ======================================================
def kosten_pro_woche(df: pd.DataFrame, path_results: str):
    """Berechnet die Gesamtkosten pro Woche und speichert sie in einer Excel-Datei."""
    
    # Wochenintervall bestimmen
    week_start = df['Woche'].min()
    week_end = df['Woche'].max()
    
    # === DAYAHEAD-STRATEGIE ===
    df_dayahead = df[df['Ladestrategie'] == 'DayAhead'].copy()
    df_tmin = df[df['Ladestrategie'] == 'T_min'].copy()
    df_konstant = df[df['Ladestrategie'] == 'Konstant'].copy()
    
    kosten_dayahead = (df_dayahead.groupby('Woche')['Kosten_DayAhead'].sum() / 100).tolist()
    kosten_tmin = (df_tmin.groupby('Woche')['Kosten_DayAhead'].sum() / 100).tolist()
    kosten_konstant = (df_konstant.groupby('Woche')['Kosten_DayAhead'].sum() / 100).tolist()
    
    data_dayahead = [
        ['Kostenvergleich Day-Ahead'],
        '',
        ['Wochen'] + list(range(week_start, week_end + 1)),
        '',
        ['Dayahead'] + kosten_dayahead,
        ['Konstant'] + kosten_konstant,
        ['T_min'] + kosten_tmin,
    ]
    
    df_results_dayahead = pd.DataFrame(data_dayahead)
    
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results_dayahead.to_excel(writer, sheet_name='DayAhead_Weeks', index=False, header=False)

    # === INTRADAY-STRATEGIE ===
    df_intraday = df[df['Ladestrategie'] == 'Intraday'].copy()
    
    kosten_intraday = (df_intraday.groupby('Woche')['Kosten_Intraday'].sum() / 100).tolist()
    kosten_tmin = (df_tmin.groupby('Woche')['Kosten_Intraday'].sum() / 100).tolist()
    kosten_konstant = (df_konstant.groupby('Woche')['Kosten_Intraday'].sum() / 100).tolist()
    
    data_intraday = [
        ['Kostenvergleich Intraday'],
        '',
        ['Wochen'] + list(range(week_start, week_end + 1)),
        '',
        ['Intraday'] + kosten_intraday,
        ['Konstant'] + kosten_konstant,
        ['T_min'] + kosten_tmin,
    ]
    
    df_results_intraday = pd.DataFrame(data_intraday)
    
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results_intraday.to_excel(writer, sheet_name='Intraday_Weeks', index=False, header=False)

# ======================================================
# Funktion: Kosten & Energie pro Ladevorgang (durchschnittlich)
# ======================================================
def kosten_pro_ladevorgang(df: pd.DataFrame, path_results: str):
    """Berechnet die durchschnittlichen Kosten pro kWh sowie durchschnittlich geladene Energie pro Ladevorgang."""
    
    # Energie berechnen (5 Minuten Intervall)
    df['Energie'] = df['Leistung'] * (5 / 60)
    
    # Helper-Funktion zur Filterung
    def filter_df(ladetyp, strategie):
        return df[(df['Ladetyp'] == ladetyp) & (df['Ladestrategie'] == strategie)].copy()

    # Initialisierung von Dictionaries
    kosten_dayahead, kosten_intraday = {}, {}
    energie_dayahead, energie_intraday = {}, {}

    for mode, kosten_dict, energie_dict, kosten_key in [
        ('DayAhead', kosten_dayahead, energie_dayahead, 'Kosten_DayAhead'),
        ('Intraday', kosten_intraday, energie_intraday, 'Kosten_Intraday')
    ]:
        for strategie in ['T_min', 'Konstant', mode]:
            kosten_dict[strategie] = {}
            energie_dict[strategie] = {}
            for ladetyp in ['NCS', 'HPC', 'MCS']:
                df_filtered = filter_df(ladetyp, strategie)
                if df_filtered.empty:
                    kosten_dict[strategie][ladetyp] = 0
                    energie_dict[strategie][ladetyp] = 0
                    continue
                kosten_pro_lkw = df_filtered.groupby('LKW_ID')[kosten_key].sum()
                energie_pro_lkw = df_filtered.groupby('LKW_ID')['Energie'].sum()
                valid_lkws = energie_pro_lkw[energie_pro_lkw > 0].index
                kosten_pro_lkw = kosten_pro_lkw.loc[valid_lkws]
                energie_pro_lkw = energie_pro_lkw.loc[valid_lkws]
                if not energie_pro_lkw.empty:
                    kosten_dict[strategie][ladetyp] = kosten_pro_lkw.mean() / energie_pro_lkw.mean()
                    energie_dict[strategie][ladetyp] = energie_pro_lkw.mean()
                else:
                    kosten_dict[strategie][ladetyp] = 0
                    energie_dict[strategie][ladetyp] = 0

    # Ergebnisse in Excel schreiben
    def write_kosten_sheet(sheet_name, kosten, energie):
        data = [
            [f'Durchschnittliche Kosten pro kWh ({sheet_name}) in Euro/kWh'],
            '',
            ['Strategie', 'NCS', 'MCS', 'HPC'],
            ['Tmin-Strategie', kosten['T_min']['NCS'], kosten['T_min']['MCS'], kosten['T_min']['HPC']],
            ['Konstant-Strategie', kosten['Konstant']['NCS'], kosten['Konstant']['MCS'], kosten['Konstant']['HPC']],
            [f'{sheet_name}-Strategie', kosten[sheet_name]['NCS'], kosten[sheet_name]['MCS'], kosten[sheet_name]['HPC']],
            [''],
            [f'Durchschnittliche Energie pro Ladevorgang ({sheet_name}) in kWh'],
            '',
            ['Strategie', 'NCS', 'MCS', 'HPC'],
            ['Tmin-Strategie', energie['T_min']['NCS'], energie['T_min']['MCS'], energie['T_min']['HPC']],
            ['Konstant-Strategie', energie['Konstant']['NCS'], energie['Konstant']['MCS'], energie['Konstant']['HPC']],
            [f'{sheet_name}-Strategie', energie[sheet_name]['NCS'], energie[sheet_name]['MCS'], energie[sheet_name]['HPC']],
        ]
        df_result = pd.DataFrame(data)
        with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            df_result.to_excel(writer, sheet_name=f'KPI_{sheet_name}', index=False, header=False)

    write_kosten_sheet('DayAhead', kosten_dayahead, energie_dayahead)
    write_kosten_sheet('Intraday', kosten_intraday, energie_intraday)

# ======================================================
# Funktion: Kostendifferenz pro Stunde
# ======================================================
def kostendifferenz_pro_stunde(df: pd.DataFrame, path_results: str):
    """Berechnet stündliche Kostendifferenzen zwischen Strategien und schreibt sie in Excel."""
    
    df['Datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d %H:%M:%S')
    df['Stunde'] = df['Datum'].dt.hour
    
    # Strategie- & Typkombinationen definieren
    def gruppiere_kosten(strategie, ladetypen, key, divisor=100):
        df_ = df[(df['Ladestrategie'] == strategie) & (df['Ladetyp'].isin(ladetypen))]
        return (df_.groupby('Stunde')[key].sum().reindex(range(24), fill_value=0) / divisor / 366).tolist()
    
    # DayAhead vs Konstant vs T_min
    kosten = {
        'DayAhead': {
            'nacht': gruppiere_kosten('DayAhead', ['NCS'], 'Kosten_DayAhead'),
            'schnell': gruppiere_kosten('DayAhead', ['HPC', 'MCS'], 'Kosten_DayAhead')
        },
        'Konstant': {
            'nacht': gruppiere_kosten('Konstant', ['NCS'], 'Kosten_DayAhead'),
            'schnell': gruppiere_kosten('Konstant', ['HPC', 'MCS'], 'Kosten_DayAhead')
        },
        'T_min': {
            'nacht': gruppiere_kosten('T_min', ['NCS'], 'Kosten_DayAhead'),
            'schnell': gruppiere_kosten('T_min', ['HPC', 'MCS'], 'Kosten_DayAhead')
        }
    }

    data_dayahead = [
        ['Kostenvergleich Stunde DayAhead'],
        '',
        ['Stunden'] + list(range(24)),
        '',
        ['Total Cost Tmin'] + [kosten['T_min']['nacht'][i] + kosten['T_min']['schnell'][i] for i in range(24)],
        ['Total Cost Konstant'] + [kosten['Konstant']['nacht'][i] + kosten['Konstant']['schnell'][i] for i in range(24)],
        ['Total Cost DayAhead'] + [kosten['DayAhead']['nacht'][i] + kosten['DayAhead']['schnell'][i] for i in range(24)],
        '',
        ['Schnell Cost Tmin'] + kosten['T_min']['schnell'],
        ['Schnell Cost Konstant'] + kosten['Konstant']['schnell'],
        ['Schnell Cost DayAhead'] + kosten['DayAhead']['schnell'],
        '',
        ['Nacht Cost Tmin'] + kosten['T_min']['nacht'],
        ['Nacht Cost Konstant'] + kosten['Konstant']['nacht'],
        ['Nacht Cost DayAhead'] + kosten['DayAhead']['nacht'],
    ]

    df_result = pd.DataFrame(data_dayahead)
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_result.to_excel(writer, sheet_name='DayAhead_Hours', index=False, header=False)

    # Intraday mit Faktor /10
    kosten_intraday = {
        'Intraday': {
            'nacht': gruppiere_kosten('Intraday', ['NCS'], 'Kosten_Intraday', divisor=1000),
            'schnell': gruppiere_kosten('Intraday', ['HPC', 'MCS'], 'Kosten_Intraday', divisor=1000)
        },
        'Konstant': {
            'nacht': gruppiere_kosten('Konstant', ['NCS'], 'Kosten_Intraday', divisor=1000),
            'schnell': gruppiere_kosten('Konstant', ['HPC', 'MCS'], 'Kosten_Intraday', divisor=1000)
        },
        'T_min': {
            'nacht': gruppiere_kosten('T_min', ['NCS'], 'Kosten_Intraday', divisor=1000),
            'schnell': gruppiere_kosten('T_min', ['HPC', 'MCS'], 'Kosten_Intraday', divisor=1000)
        }
    }

    data_intraday = [
        ['Kostenvergleich Stunde Intraday'],
        '',
        ['Stunden'] + list(range(24)),
        '',
        ['Total Cost Tmin'] + [kosten_intraday['T_min']['nacht'][i] + kosten_intraday['T_min']['schnell'][i] for i in range(24)],
        ['Total Cost Konstant'] + [kosten_intraday['Konstant']['nacht'][i] + kosten_intraday['Konstant']['schnell'][i] for i in range(24)],
        ['Total Cost Intraday'] + [kosten_intraday['Intraday']['nacht'][i] + kosten_intraday['Intraday']['schnell'][i] for i in range(24)],
        '',
        ['Schnell Cost Tmin'] + kosten_intraday['T_min']['schnell'],
        ['Schnell Cost Konstant'] + kosten_intraday['Konstant']['schnell'],
        ['Schnell Cost Intraday'] + kosten_intraday['Intraday']['schnell'],
        '',
        ['Nacht Cost Tmin'] + kosten_intraday['T_min']['nacht'],
        ['Nacht Cost Konstant'] + kosten_intraday['Konstant']['nacht'],
        ['Nacht Cost Intraday'] + kosten_intraday['Intraday']['nacht'],
    ]

    df_result = pd.DataFrame(data_intraday)
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_result.to_excel(writer, sheet_name='Intraday_Hours', index=False, header=False)

# ======================================================
# Hauptfunktion
# ======================================================
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    for szenario in config.list_szenarien:
        print(f"Verarbeite Szenario: {szenario}")
        path_input = os.path.join(base_dir, 'data', 'epex', 'lastgang_lkw', f'lastgang_lkw_{szenario}.csv')
        szenario_kuerzel = szenario.split('_')[-1]
        path_results = os.path.join(base_dir, 'output', f'results_epex_{szenario_kuerzel}.xlsx')

        if not os.path.exists(path_input):
            print(f"⚠️ Eingabedatei nicht gefunden: {path_input}")
            continue

        os.makedirs(os.path.dirname(path_results), exist_ok=True)

        try:
            df = pd.read_csv(path_input, sep=';', decimal=',')
            with pd.ExcelWriter(path_results, engine='openpyxl', mode='w') as writer:
                pd.DataFrame().to_excel(writer)

            kosten_pro_woche(df, path_results)
            kosten_pro_ladevorgang(df, path_results)
            kostendifferenz_pro_stunde(df, path_results)

            print(f"✅ Excel-Datei erfolgreich erstellt: {path_results}")
        except Exception as e:
            print(f"❌ Fehler in Szenario {szenario}: {str(e)}")

# ======================================================
# Ausführung
# ======================================================
if __name__ == '__main__':
    time_start = time.time()
    main()
    time_end = time.time()
    print(f"🔚 Gesamtlaufzeit: {time_end - time_start:.2f} Sekunden")