import pandas as pd
import os
import time
import config

def kosten_pro_woche(df: pd.DataFrame, path_results: str):
    """Berechnet die Kosten pro Woche und schreibt die Ergebnisse in eine Excel-Datei."""
    
    # Welche Wochen liegen im Datensatz?
    week_start = df['Woche'].min()
    week_end = df['Woche'].max()
    
    # DayAhead-Strategie
    df_dayahead = df[df['Ladestrategie'] == 'DayAhead'].copy()
    df_tmin = df[df['Ladestrategie'] == 'T_min'].copy()
    df_konstant = df[df['Ladestrategie'] == 'Konstant'].copy()
    
    kosten_dayahead = (df_dayahead.groupby('Woche')['Kosten_DayAhead'].sum() / 100).tolist()
    kosten_tmin = (df_tmin.groupby('Woche')['Kosten_DayAhead'].sum() / 100).tolist()
    kosten_konstant = (df_konstant.groupby('Woche')['Kosten_DayAhead'].sum() / 100).tolist()
    
    data_dayahead = [
        ['Kostenvergleich Day-Ahead'],
        '',
        ['Wochen'] + list(range(week_start, week_end+1)),
        '',
        ['Dayahead'] + kosten_dayahead,
        ['Konstant'] + kosten_konstant,
        ['T_min'] + kosten_tmin,
    ]
    
    df_results_dayahead = pd.DataFrame(data_dayahead)
    
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results_dayahead.to_excel(
            writer,
            sheet_name='DayAhead_Weeks',
            index=False,
            header=False,
            startrow=0,
            startcol=0
        )
    
    # Intraday-Strategie
    df_intraday = df[df['Ladestrategie'] == 'Intraday'].copy()
    df_tmin = df[df['Ladestrategie'] == 'T_min'].copy()
    df_konstant = df[df['Ladestrategie'] == 'Konstant'].copy()
    
    kosten_intraday = (df_intraday.groupby('Woche')['Kosten_Intraday'].sum() / 100).tolist()
    kosten_tmin = (df_tmin.groupby('Woche')['Kosten_Intraday'].sum() / 100).tolist()
    kosten_konstant = (df_konstant.groupby('Woche')['Kosten_Intraday'].sum() / 100).tolist()
    
    data_intraday = [
        ['Kostenvergleich Intraday'],
        '',
        ['Wochen'] + list(range(week_start, week_end+1)),
        '',
        ['Intraday'] + kosten_intraday,
        ['Konstant'] + kosten_konstant,
        ['T_min'] + kosten_tmin,
    ]
    
    df_results_intraday = pd.DataFrame(data_intraday)
    
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results_intraday.to_excel(
            writer,
            sheet_name='Intraday_Weeks',
            index=False,
            header=False,
            startrow=0,
            startcol=0
        )

def kosten_pro_ladevorgang(df: pd.DataFrame, path_results: str):
    """Berechnet die durchschnittlichen Kosten pro kWh und schreibt die Ergebnisse in eine Excel-Datei."""
    
    # Dictionaries für die Kosten und Energie, um eine strukturierte Ablage zu haben
    kosten_dayahead = {
        'DayAhead': {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'T_min':     {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'Konstant': {'NCS': 0, 'HPC': 0, 'MCS': 0}
    }
    kosten_intraday = {
        'Intraday': {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'T_min':     {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'Konstant': {'NCS': 0, 'HPC': 0, 'MCS': 0}
    }
    
    # Energie-Dictionaries, um die geladene Energiemenge zu erfassen
    energie_dayahead = {
        'DayAhead': {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'T_min':     {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'Konstant': {'NCS': 0, 'HPC': 0, 'MCS': 0}
    }
    energie_intraday = {
        'Intraday': {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'T_min':     {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'Konstant': {'NCS': 0, 'HPC': 0, 'MCS': 0}
    }

    # Berechnung der geladenen Energie pro LKW
    # Wir nutzen die Leistung und multiplizieren mit dem Zeitintervall (5 Minuten = 5/60 Stunden)
    df['Energie'] = df['Leistung'] * (5/60)  # Leistung in kW * Zeit in Stunden = Energie in kWh
    
    # Filter-Funktionen zur Wiederverwendung
    def filter_df(ladetyp, strategie):
        return df[(df['Ladetyp'] == ladetyp) & (df['Ladestrategie'] == strategie)].copy()

    # DayAhead Strategie - Kosten und Energie pro LKW berechnen
    for ladetyp in ['NCS', 'HPC', 'MCS']:
        for strategie in ['DayAhead', 'T_min', 'Konstant']:
            df_filtered = filter_df(ladetyp, strategie)
            
            if not df_filtered.empty:
                # Kosten und Energie pro LKW berechnen
                kosten_pro_lkw = df_filtered.groupby('LKW_ID')['Kosten_DayAhead'].sum()   # Division durch 100 wie im Original
                energie_pro_lkw = df_filtered.groupby('LKW_ID')['Energie'].sum()
                
                # Nur LKWs mit tatsächlich geladener Energie berücksichtigen
                valid_lkws = energie_pro_lkw[energie_pro_lkw > 0].index
                kosten_pro_lkw = kosten_pro_lkw.loc[valid_lkws]
                energie_pro_lkw = energie_pro_lkw.loc[valid_lkws]
                
                # Kosten pro kWh für jeden LKW berechnen
                if not energie_pro_lkw.empty:
                    kosten_dayahead[strategie][ladetyp] = kosten_pro_lkw.mean() / energie_pro_lkw.mean()  
                    energie_dayahead[strategie][ladetyp] = energie_pro_lkw.mean()

    # Intraday Strategie - Kosten und Energie pro LKW berechnen
    for ladetyp in ['NCS', 'HPC', 'MCS']:
        for strategie in ['Intraday', 'T_min', 'Konstant']:
            df_filtered = filter_df(ladetyp, strategie)
            
            if not df_filtered.empty:
                # Kosten und Energie pro LKW berechnen
                kosten_pro_lkw = df_filtered.groupby('LKW_ID')['Kosten_Intraday'].sum() / 10  # Division wie im Original
                energie_pro_lkw = df_filtered.groupby('LKW_ID')['Energie'].sum()
                
                # Nur LKWs mit tatsächlich geladener Energie berücksichtigen
                valid_lkws = energie_pro_lkw[energie_pro_lkw > 0].index
                kosten_pro_lkw = kosten_pro_lkw.loc[valid_lkws]
                energie_pro_lkw = energie_pro_lkw.loc[valid_lkws]
                
                # Kosten pro kWh für jeden LKW berechnen
                if not energie_pro_lkw.empty:

                    kosten_intraday[strategie][ladetyp] = kosten_pro_lkw.mean() / energie_pro_lkw.mean()  
                    energie_intraday[strategie][ladetyp] = energie_pro_lkw.mean()
        
    # Excel-Export: DayAhead-Kosten pro kWh
    data_dayahead = [
            ['Durchschnittliche Kosten pro kWh (Day-Ahead) in Euro/kWh'],
            '',
            ['Strategie', 'NCS', 'MCS', 'HPC'],
            ['Tmin-Strategie', 
            kosten_dayahead['T_min']['NCS'], 
            kosten_dayahead['T_min']['MCS'], 
            kosten_dayahead['T_min']['HPC']
            ],
            ['Konstant-Strategie', 
            kosten_dayahead['Konstant']['NCS'], 
            kosten_dayahead['Konstant']['MCS'], 
            kosten_dayahead['Konstant']['HPC']
            ],
            ['DayAhead-Strategie', 
            kosten_dayahead['DayAhead']['NCS'], 
            kosten_dayahead['DayAhead']['MCS'], 
            kosten_dayahead['DayAhead']['HPC']
            ],
            [''],
            ['Durchschnittliche Energie pro Ladevorgang (Day-Ahead) in kWh'],
            '',
            ['Strategie', 'NCS', 'MCS', 'HPC'],
            ['Tmin-Strategie', 
            energie_dayahead['T_min']['NCS'], 
            energie_dayahead['T_min']['MCS'], 
            energie_dayahead['T_min']['HPC']
            ],
            ['Konstant-Strategie', 
            energie_dayahead['Konstant']['NCS'], 
            energie_dayahead['Konstant']['MCS'], 
            energie_dayahead['Konstant']['HPC']
            ],
            ['DayAhead-Strategie', 
            energie_dayahead['DayAhead']['NCS'], 
            energie_dayahead['DayAhead']['MCS'], 
            energie_dayahead['DayAhead']['HPC']
            ]
        ]
    
    df_results_dayahead = pd.DataFrame(data_dayahead)
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results_dayahead.to_excel(
            writer,
            sheet_name='KPI_DayAhead',
            index=False,
            header=False,
            startrow=0,
            startcol=0
        )
        
    # Excel-Export: Intraday-Kosten pro kWh
    data_intraday = [
        ['Durchschnittliche Kosten pro kWh (Intraday) in Euro/kWh'],
        '',
        ['Strategie', 'NCS', 'MCS', 'HPC'],
        ['Tmin-Strategie', 
         kosten_intraday['T_min']['NCS'], 
         kosten_intraday['T_min']['MCS'], 
         kosten_intraday['T_min']['HPC']
        ],
        ['Konstant-Strategie', 
         kosten_intraday['Konstant']['NCS'], 
         kosten_intraday['Konstant']['MCS'], 
         kosten_intraday['Konstant']['HPC']
        ],
        ['Intraday-Strategie', 
         kosten_intraday['Intraday']['NCS'], 
         kosten_intraday['Intraday']['MCS'], 
         kosten_intraday['Intraday']['HPC']
        ],
        [''],
        ['Durchschnittliche Energie pro Ladevorgang (Intraday) in kWh'],
        '',
        ['Strategie', 'NCS', 'MCS', 'HPC'],
        ['Tmin-Strategie', 
         energie_intraday['T_min']['NCS'], 
         energie_intraday['T_min']['MCS'], 
         energie_intraday['T_min']['HPC']
        ],
        ['Konstant-Strategie', 
         energie_intraday['Konstant']['NCS'], 
         energie_intraday['Konstant']['MCS'], 
         energie_intraday['Konstant']['HPC']
        ],
        ['Intraday-Strategie', 
         energie_intraday['Intraday']['NCS'], 
         energie_intraday['Intraday']['MCS'], 
         energie_intraday['Intraday']['HPC']
        ]
    ]
    
    df_results_intraday = pd.DataFrame(data_intraday)
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results_intraday.to_excel(
            writer,
            sheet_name='KPI_Intraday',
            index=False,
            header=False,
            startrow=0,
            startcol=0
        )


def kostendifferenz_pro_stunde(df: pd.DataFrame, path_results: str):
    """Berechnet stündliche Kostendifferenzen zwischen Strategien und schreibt die Ergebnisse in eine Excel-Datei."""
    
    df['Datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d %H:%M:%S')
    df['Stunde'] = df['Datum'].dt.hour
    
    # # Zähle für jede Stunde, an wie vielen Tagen diese in df auftritt, für jede Ladestrategie einzeln
    # df['Datum_Tag'] = df['Datum'].dt.date
    
    # ladestrategien = df['Ladestrategie'].unique()
    # data_stunden_zaehler = [['Anzahl der Tage pro Stunde']]
    
    # for strategie in ladestrategien:
    #     df_strategie = df[df['Ladestrategie'] == strategie]
    #     stunden_zaehler = df_strategie.groupby('Stunde')['Datum_Tag'].nunique().reindex(range(24), fill_value=0).tolist()
    #     data_stunden_zaehler.append([''])
    #     data_stunden_zaehler.append([strategie])
    #     data_stunden_zaehler.append(['Stunden'] + list(range(24)))
    #     data_stunden_zaehler.append(['Anzahl Tage'] + stunden_zaehler)
        
    # print(data_stunden_zaehler)

    
    # Für DayAhead
    df_dayahead_nacht = df[(df['Ladestrategie'] == 'DayAhead') & (df['Ladetyp'] == 'NCS')]
    df_dayahead_schnell = df[(df['Ladestrategie'] == 'DayAhead') & (df['Ladetyp'].isin(['HPC', 'MCS']))]
    
    df_konstant_nacht = df[(df['Ladestrategie'] == 'Konstant') & (df['Ladetyp'] == 'NCS')]
    df_konstant_schnell = df[(df['Ladestrategie'] == 'Konstant') & (df['Ladetyp'].isin(['HPC', 'MCS']))]
    
    df_tmin_nacht = df[(df['Ladestrategie'] == 'T_min') & (df['Ladetyp'] == 'NCS')]
    df_tmin_schnell = df[(df['Ladestrategie'] == 'T_min') & (df['Ladetyp'].isin(['HPC', 'MCS']))]
    
    # Gruppenbildung
    kosten_opt_nacht = (df_dayahead_nacht.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0) / 100 / 366).tolist()
    kosten_opt_schnell = (df_dayahead_schnell.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0) / 100 / 366).tolist()
    kosten_konstant_nacht = (df_konstant_nacht.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0) / 100 / 366).tolist()
    kosten_konstant_schnell = (df_konstant_schnell.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0) / 100 / 366).tolist()
    kosten_tmin_nacht = (df_tmin_nacht.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0) / 100 / 366).tolist()
    kosten_tmin_schnell = (df_tmin_schnell.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0) / 100 / 366).tolist()
    
    data_dayahead = [
        ['Kostenvergleich Stunde DayAhead'],
        '',
        ['Stunden'] + list(range(24)),
        '',
        ['Total Cost Tmin'] + [kosten_tmin_nacht[i] + kosten_tmin_schnell[i] for i in range(24)],
        ['Total Cost Konstant'] + [kosten_konstant_nacht[i] + kosten_konstant_schnell[i] for i in range(24)],
        ['Total Cost DayAhead'] + [kosten_opt_nacht[i] + kosten_opt_schnell[i]for i in range(24)],
        '',
        ['Schnell Cost Tmin'] + kosten_tmin_schnell,
        ['Schnell Cost Konstant'] + kosten_konstant_schnell,
        ['Schnell Cost DayAhead'] + kosten_opt_schnell,
        '',
        ['Nacht Cost Tmin'] + kosten_tmin_nacht,
        ['Nacht Cost Konstant'] + kosten_konstant_nacht,
        ['Nacht Cost DayAhead'] + kosten_opt_nacht,
    ]
    
    df_results_dayahead = pd.DataFrame(data_dayahead)
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results_dayahead.to_excel(
            writer,
            sheet_name='DayAhead_Hours',
            index=False,
            header=False,
            startrow=0,
            startcol=0
        )
    
    # Für Intraday
    df_intraday_nacht = df[(df['Ladestrategie'] == 'Intraday') & (df['Ladetyp'] == 'NCS')]
    df_intraday_schnell = df[(df['Ladestrategie'] == 'Intraday') & (df['Ladetyp'].isin(['HPC', 'MCS']))]
    
    df_konstant_nacht = df[(df['Ladestrategie'] == 'Konstant') & (df['Ladetyp'] == 'NCS')]
    df_konstant_schnell = df[(df['Ladestrategie'] == 'Konstant') & (df['Ladetyp'].isin(['HPC', 'MCS']))]
    
    df_tmin_nacht = df[(df['Ladestrategie'] == 'T_min') & (df['Ladetyp'] == 'NCS')]
    df_tmin_schnell = df[(df['Ladestrategie'] == 'T_min') & (df['Ladetyp'].isin(['HPC', 'MCS']))]
    
    
    kosten_opt_nacht_intra = (df_intraday_nacht.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0) / 100 / 10 / 366).tolist()
    kosten_opt_schnell_intra = (df_intraday_schnell.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0) / 100 / 10 / 366).tolist()
    
    kosten_konstant_nacht_intra = (df_konstant_nacht.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0) / 100 / 10 / 366).tolist()
    kosten_konstant_schnell_intra = (df_konstant_schnell.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0) / 100 / 10 / 366).tolist()
    
    kosten_tmin_nacht_intra = (df_tmin_nacht.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0) / 100 / 10 / 366).tolist()
    kosten_tmin_schnell_intra = (df_tmin_schnell.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0) / 100 / 10 / 366).tolist()
    
    data_intraday = [
        ['Kostenvergleich Stunde Intraday'],
        '',
        ['Stunden'] + list(range(24)),
        '',
        ['Total Cost Tmin'] + [kosten_tmin_nacht_intra[i] + kosten_tmin_schnell_intra[i] for i in range(24)],
        ['Total Cost Konstant'] + [kosten_konstant_nacht_intra[i] + kosten_konstant_schnell_intra[i]for i in range(24)],
        ['Total Cost Intraday'] + [kosten_opt_nacht_intra[i] + kosten_opt_schnell_intra[i]for i in range(24)],
        '',
        ['Schnell Cost Tmin'] + kosten_tmin_schnell_intra,
        ['Schnell Cost Konstant'] + kosten_konstant_schnell_intra,
        ['Schnell Cost Intraday'] + kosten_opt_schnell_intra,
        '',
        ['Nacht Cost Tmin'] + kosten_tmin_nacht_intra,
        ['Nacht Cost Konstant'] + kosten_konstant_nacht_intra,
        ['Nacht Cost Intraday'] + kosten_opt_nacht_intra,   
    ]
    
    df_results_intraday = pd.DataFrame(data_intraday)
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results_intraday.to_excel(
            writer,
            sheet_name='Intraday_Hours',
            index=False,
            header=False,
            startrow=0,
            startcol=0
        )


# Änderung in der main-Funktion:
def main():
    # Basisverzeichnis definieren
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Alle Szenarien aus der Konfiguration verarbeiten
    for szenario in config.list_szenarien:
        print(f"Verarbeite Szenario: {szenario}")
        
        # Pfade für dieses Szenario
        path_input = os.path.join(base_dir, 'data', 'epex', 'lastgang_lkw', f'lastgang_lkw_{szenario}.csv')
        
        # Extrahiere nur das Kürzel nach dem letzten Unterstrich für den Dateinamen
        szenario_kuerzel = szenario.split('_')[-1]
        path_results = os.path.join(base_dir, 'output', f'results_epex_{szenario_kuerzel}.xlsx')
        
        # Prüfen, ob die Eingabedatei existiert
        if not os.path.exists(path_input):
            print(f"Eingabedatei für Szenario {szenario} nicht gefunden: {path_input}")
            continue
        
        # Verzeichnis für Ausgabe erstellen, falls nicht vorhanden
        os.makedirs(os.path.dirname(path_results), exist_ok=True)
        
        try:
            # Lastgang einlesen
            df = pd.read_csv(path_input, sep=';', decimal=',')
            
            # Leere Excel-Datei erstellen (wird überschrieben, falls vorhanden)
            with pd.ExcelWriter(path_results, engine='openpyxl', mode='w') as writer:
                pd.DataFrame().to_excel(writer)
            
            # Funktionen mit diesem DataFrame aufrufen
            kosten_pro_woche(df, path_results)
            kosten_pro_ladevorgang(df, path_results)
            kostendifferenz_pro_stunde(df, path_results)
            
            print(f"Excel-Datei für Szenario {szenario} erfolgreich erstellt: {path_results}")
        except Exception as e:
            print(f"Fehler bei der Verarbeitung von Szenario {szenario}: {str(e)}")


if __name__ == '__main__':
    time_start = time.time()
    main()
    time_end = time.time()
    
    print(f"Gesamtlaufzeit: {time_end - time_start:.2f} Sekunden")
