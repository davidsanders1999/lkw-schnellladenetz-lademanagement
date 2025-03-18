# import pandas as pd
# import os



# def kosten_pro_woche():

#     path_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'epex', 'lastgang_lkw' ,'lastgang_lkw_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')
#     path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results_epex.xlsx')
    
#     df = pd.read_csv(path_input, sep=';', decimal=',')
    
#     week_start = df['Woche'].min()
#     week_end = df['Woche'].max()
    
#     # DayAhead-Strategie pro Woche
#     df_dayahead = df[df['Ladestrategie'] == 'DayAhead'].copy()
#     df_tmin = df[df['Ladestrategie'] == 'T_min'].copy()
#     df_konstant = df[df['Ladestrategie'] == 'Konstant'].copy()
    
#     kosten_dayahead = df_dayahead.groupby('Woche')['Kosten_DayAhead'].sum().tolist()
#     kosten_tmin = df_tmin.groupby('Woche')['Kosten_DayAhead'].sum().tolist() 
#     kosten_konstant = df_konstant.groupby('Woche')['Kosten_DayAhead'].sum().tolist()
    
    
#     data = [
#         ['Kostenvergleich Day-Ahead'],
#         '',
#         ['Wochen'] + list(range(week_start, week_end+1)),
#         '',
#         ['Dayahead'] + kosten_dayahead,
#         ['Konstant'] + kosten_konstant,
#         ['Tmin'] + kosten_tmin,
#     ]
    
    
#     df_results = pd.DataFrame(data)

#     with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
#         df_results.to_excel(writer, sheet_name='DayAhead_Weeks', index=False, header=False, startrow=0, startcol=0)
        
    
#     df_dayahead = df[df['Ladestrategie'] == 'Intraday'].copy()
#     df_tmin = df[df['Ladestrategie'] == 'T_min'].copy()
#     df_konstant = df[df['Ladestrategie'] == 'Konstant'].copy()
    
#     kosten_intraday = df_dayahead.groupby('Woche')['Kosten_Intraday'].sum().tolist()
#     kosten_tmin = df_tmin.groupby('Woche')['Kosten_Intraday'].sum().tolist() 
#     kosten_konstant = df_konstant.groupby('Woche')['Kosten_Intraday'].sum().tolist()
    
    
#     data = [
#         ['Kostenvergleich Day-Ahead'],
#         '',
#         ['Wochen'] + list(range(week_start, week_end+1)),
#         '',
#         ['Intraday'] + kosten_intraday,
#         ['Konstant'] + kosten_konstant,
#         ['Tmin'] + kosten_tmin,
#     ]
    
    
#     df_results = pd.DataFrame(data)

#     with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
#         df_results.to_excel(writer, sheet_name='Intraday_Weeks', index=False, header=False, startrow=0, startcol=0)
    

# def kosten_pro_ladevorgang():
    
#     path_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'epex', 'lastgang_lkw' ,'lastgang_lkw_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')
#     path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results_epex.xlsx')
    
#     df = pd.read_csv(path_input, sep=';', decimal=',')

#     kosten_dayahead = {
#         'DayAhead':{
#             'NCS': 0,
#             'HPC': 0,
#             'MCS': 0
#         },
#         'Tmin':{
#             'NCS': 0,
#             'HPC': 0,
#             'MCS': 0
#         },
#         'Konstant':{
#             'NCS': 0,
#             'HPC': 0,
#             'MCS': 0
#         }
#     }

#     df_ncs_intraday = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'DayAhead')].copy()
#     df_ncs_konst = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'Konstant')].copy()
#     df_ncs_tmin = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'T_min')].copy()
    
#     df_mcs_intraday = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'DayAhead')].copy()
#     df_mcs_konst = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'Konstant')].copy()
#     df_mcs_tmin = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'T_min')].copy()
    
#     df_hpc_intraday = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'DayAhead')].copy()
#     df_hpc_konst = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'Konstant')].copy()
#     df_hpc_tmin = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'T_min')].copy()
    
    
#     kosten_dayahead['DayAhead']['NCS'] = df_ncs_intraday.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() / 100
#     kosten_dayahead['Konstant']['NCS'] = df_ncs_konst.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() / 100
#     kosten_dayahead['Tmin']['NCS']     = df_ncs_tmin.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() / 100
    
#     kosten_dayahead['DayAhead']['MCS'] = df_mcs_intraday.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() / 100
#     kosten_dayahead['Konstant']['MCS'] = df_mcs_konst.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() / 100
#     kosten_dayahead['Tmin']['MCS']     = df_mcs_tmin.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() / 100
    
#     kosten_dayahead['DayAhead']['HPC'] = df_hpc_intraday.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() /100
#     kosten_dayahead['Konstant']['HPC'] = df_hpc_konst.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() / 100
#     kosten_dayahead['Tmin']['HPC'] = df_hpc_tmin.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() / 100
    
#     print(kosten_dayahead)
    
#     kosten_intraday = {
#         'Intraday':{
#             'NCS': 0,
#             'HPC': 0,
#             'MCS': 0
#         },
#         'Tmin':{
#             'NCS': 0,
#             'HPC': 0,
#             'MCS': 0
#         },
#         'Konstant':{
#             'NCS': 0,
#             'HPC': 0,
#             'MCS': 0
#         }
#     }
    
#     df_ncs_intraday = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'Intraday')].copy()
#     df_ncs_konst = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'Konstant')].copy()
#     df_ncs_tmin = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'T_min')].copy()
    
#     df_mcs_intraday = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'Intraday')].copy()
#     df_mcs_konst = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'Konstant')].copy()
#     df_mcs_tmin = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'T_min')].copy()
    
#     df_hpc_intraday = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'Intraday')].copy()
#     df_hpc_konst = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'Konstant')].copy()
#     df_hpc_tmin = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'T_min')].copy()
    
    
#     kosten_intraday['Intraday']['NCS'] = df_ncs_intraday.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() / 100 / 10
#     kosten_intraday['Konstant']['NCS'] = df_ncs_konst.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() / 100 /10 
#     kosten_intraday['Tmin']['NCS']     = df_ncs_tmin.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() / 100/10
    
#     kosten_intraday['Intraday']['MCS'] = df_mcs_intraday.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() / 100/10
#     kosten_intraday['Konstant']['MCS'] = df_mcs_konst.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() / 100/10
#     kosten_intraday['Tmin']['MCS']     = df_mcs_tmin.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() / 100/10
    
#     kosten_intraday['Intraday']['HPC'] = df_hpc_intraday.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() / 100 /10
#     kosten_intraday['Konstant']['HPC'] = df_hpc_konst.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() / 100/10
#     kosten_intraday['Tmin']['HPC'] = df_hpc_tmin.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() / 100/10
    
#     print(kosten_intraday)
    
#     # Export DayAhead KPIs zu Excel
#     data_dayahead = [
#         ['Durchschnittliche Kosten pro Ladevorgang (Day-Ahead) in Euro'],
#         '',
#         ['Ladetyp', 'DayAhead-Strategie', 'Konstant-Strategie', 'Differenz absolut', 'Differenz relativ'],
#         ['NCS', 
#          kosten_dayahead['DayAhead']['NCS'], 
#          kosten_dayahead['Konstant']['NCS'], 
#          kosten_dayahead['Tmin']['NCS'],
#         ],
#         ['MCS', 
#          kosten_dayahead['DayAhead']['MCS'], 
#          kosten_dayahead['Konstant']['MCS'], 
#          kosten_dayahead['Tmin']['MCS'],
#         ],
#         ['HPC', 
#          kosten_dayahead['DayAhead']['HPC'], 
#          kosten_dayahead['Konstant']['HPC'], 
#          kosten_dayahead['Tmin']['HPC'],
#         ]
#     ]
    
#     df_results_dayahead = pd.DataFrame(data_dayahead)

#     with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
#         df_results_dayahead.to_excel(writer, sheet_name='KPI_DayAhead', index=False, header=False, startrow=0, startcol=0)
        
#     # Export Intraday KPIs zu Excel
#     data_intraday = [
#         ['Durchschnittliche Kosten pro Ladevorgang (Intraday) in Euro'],
#         '',
#         ['Ladetyp', 'Intraday-Strategie', 'Konstant-Strategie', 'Differenz absolut', 'Differenz relativ'],
#         ['NCS', 
#          kosten_intraday['Intraday']['NCS'], 
#          kosten_intraday['Konstant']['NCS'], 
#         kosten_intraday['Intraday']['NCS'],
#         ],
#         ['MCS', 
#          kosten_intraday['Intraday']['MCS'], 
#          kosten_intraday['Konstant']['MCS'], 
#             kosten_intraday['Intraday']['MCS'],
#         ],
#         ['HPC', 
#          kosten_intraday['Intraday']['HPC'], 
#          kosten_intraday['Konstant']['HPC'], 
#         kosten_intraday['Intraday']['HPC'],
#         ]
#     ]
    
#     df_results_intraday = pd.DataFrame(data_intraday)

#     with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
#         df_results_intraday.to_excel(writer, sheet_name='KPI_Intraday', index=False, header=False, startrow=0, startcol=0)
    
    
# def kostendifferenz_pro_stunde():
#     path_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'epex', 'lastgang_lkw' ,'lastgang_lkw_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')
#     path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results_epex.xlsx')
    
#     df = pd.read_csv(path_input, sep=';', decimal=',')
#     df['Datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d %H:%M:%S')
#     df['Stunde'] = df['Datum'].dt.hour  
    
#     df_dayahead_nacht = df[(df['Ladestrategie'] == 'DayAhead') & (df['Ladetyp'] == 'NCS')].copy()
#     df_dayahead_schnell = df[(df['Ladestrategie'] == 'DayAhead') & ((df['Ladetyp'] == 'HPC') | (df['Ladetyp'] == 'MCS'))].copy()
 
    
#     df_nicht_optimiert_nacht = df[(df['Ladestrategie'] == 'Konstant') & (df['Ladetyp'] == 'NCS')].copy()
#     df_nicht_optimiert_schnell = df[(df['Ladestrategie'] == 'Konstant') & ((df['Ladetyp'] == 'HPC') | (df['Ladetyp'] == 'MCS'))].copy()
    
#     df_tmin = df[(df['Ladestrategie'] == 'T_min')].copy()
        
#     kosten_opt_nacht = df_dayahead_nacht.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0).tolist()
#     kosten_opt_schnell = df_dayahead_schnell.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0).tolist()
    
#     kosten_nicht_optimiert_nacht = df_nicht_optimiert_nacht.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0).tolist()
#     kosten_nicht_optimiert_schnell = df_nicht_optimiert_schnell.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0).tolist()
    
#     kosten_tmin = df_tmin.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0).tolist()
    
#     data = [
#         ['Kostenvergleich Stunde Intraday'],
#         '',
#         ['Stunden'] + list(range(24)),
#         '',
#         ['Total Cost Tmin'] + kosten_tmin,
#         ['Total Cost Konstant'] + [kosten_nicht_optimiert_nacht[i] + kosten_nicht_optimiert_schnell[i] for i in range(len(kosten_nicht_optimiert_nacht))],
#         ['Total Cost Intraday'] + [kosten_opt_nacht[i] + kosten_opt_schnell[i] for i in range(len(kosten_opt_nacht))],
#         ['Total Delta'] + [kosten_opt_nacht[i] + kosten_opt_schnell[i] - kosten_nicht_optimiert_nacht[i] - kosten_nicht_optimiert_schnell[i] for i in range(len(kosten_opt_nacht))],
#         ['Delta Nachtlader'] + [kosten_opt_nacht[i] - kosten_nicht_optimiert_nacht[i] for i in range(len(kosten_opt_nacht))],
#         ['Delta Schnelllader'] + [kosten_opt_schnell[i] - kosten_nicht_optimiert_schnell[i] for i in range(len(kosten_opt_schnell))],
#     ]
    
#     df_results = pd.DataFrame(data)

#     with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
#         df_results.to_excel(writer, sheet_name='DayAhead_Hours', index=False, header=False, startrow=0, startcol=0)


#     df_intraday_nacht = df[(df['Ladestrategie'] == 'Intraday') & (df['Ladetyp'] == 'NCS')].copy()
#     df_intraday_schnell = df[(df['Ladestrategie'] == 'Intraday') & ((df['Ladetyp'] == 'HPC') | (df['Ladetyp'] == 'MCS'))].copy()

#     df_nicht_optimiert_nacht = df[(df['Ladestrategie'] == 'Konstant') & (df['Ladetyp'] == 'NCS')].copy()
#     df_nicht_optimiert_schnell = df[(df['Ladestrategie'] == 'Konstant') & ((df['Ladetyp'] == 'HPC') | (df['Ladetyp'] == 'MCS'))].copy()
    
#     kosten_opt_nacht = df_intraday_nacht.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0).tolist()
#     kosten_opt_schnell = df_intraday_schnell.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0).tolist()
    
#     kosten_nicht_optimiert_nacht = df_nicht_optimiert_nacht.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0).tolist()
#     kosten_nicht_optimiert_schnell = df_nicht_optimiert_schnell.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0).tolist()
        
#     kosten_tmin = df_tmin.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0).tolist()

        
#     data = [
#         ['Kostenvergleich Stunde Intraday'],
#         '',
#         ['Stunden'] + list(range(24)),
#         '',
#         ['Total Cost Tmin'] + kosten_tmin,
#         ['Total Cost Konstant'] + [kosten_nicht_optimiert_nacht[i] + kosten_nicht_optimiert_schnell[i] for i in range(len(kosten_nicht_optimiert_nacht))],
#         ['Total Cost Intraday'] + [kosten_opt_nacht[i] + kosten_opt_schnell[i] for i in range(len(kosten_opt_nacht))],
#         ['Total Delta'] + [kosten_opt_nacht[i] + kosten_opt_schnell[i] - kosten_nicht_optimiert_nacht[i] - kosten_nicht_optimiert_schnell[i] for i in range(len(kosten_opt_nacht))],
#         ['Delta Nachtlader'] + [kosten_opt_nacht[i] - kosten_nicht_optimiert_nacht[i] for i in range(len(kosten_opt_nacht))],
#         ['Delta Schnelllader'] + [kosten_opt_schnell[i] - kosten_nicht_optimiert_schnell[i] for i in range(len(kosten_opt_schnell))],
#     ]
    
#     df_results = pd.DataFrame(data)

#     with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
#         df_results.to_excel(writer, sheet_name='Intraday_Hours', index=False, header=False, startrow=0, startcol=0)


# def main():
#     kosten_pro_woche()
#     kosten_pro_ladevorgang()
#     kostendifferenz_pro_stunde()

# if __name__ == '__main__':
#     main()


import pandas as pd
import os
import time

def kosten_pro_woche(df: pd.DataFrame, path_results: str):
    """Berechnet die Kosten pro Woche und schreibt die Ergebnisse in eine Excel-Datei."""
    
    # Welche Wochen liegen im Datensatz?
    week_start = df['Woche'].min()
    week_end = df['Woche'].max()
    
    # DayAhead-Strategie
    df_dayahead = df[df['Ladestrategie'] == 'DayAhead'].copy()
    df_tmin = df[df['Ladestrategie'] == 'T_min'].copy()
    df_konstant = df[df['Ladestrategie'] == 'Konstant'].copy()
    
    kosten_dayahead = df_dayahead.groupby('Woche')['Kosten_DayAhead'].sum().tolist()
    kosten_tmin = df_tmin.groupby('Woche')['Kosten_DayAhead'].sum().tolist() 
    kosten_konstant = df_konstant.groupby('Woche')['Kosten_DayAhead'].sum().tolist()
    
    data_dayahead = [
        ['Kostenvergleich Day-Ahead'],
        '',
        ['Wochen'] + list(range(week_start, week_end+1)),
        '',
        ['Dayahead'] + kosten_dayahead,
        ['Konstant'] + kosten_konstant,
        ['Tmin'] + kosten_tmin,
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
    
    kosten_intraday = df_intraday.groupby('Woche')['Kosten_Intraday'].sum().tolist()
    kosten_tmin = df_tmin.groupby('Woche')['Kosten_Intraday'].sum().tolist() 
    kosten_konstant = df_konstant.groupby('Woche')['Kosten_Intraday'].sum().tolist()
    
    data_intraday = [
        ['Kostenvergleich Intraday'],
        '',
        ['Wochen'] + list(range(week_start, week_end+1)),
        '',
        ['Intraday'] + kosten_intraday,
        ['Konstant'] + kosten_konstant,
        ['Tmin'] + kosten_tmin,
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
    """Berechnet die durchschnittlichen Kosten pro Ladevorgang und schreibt die Ergebnisse in eine Excel-Datei."""
    
    # Dictionaries für die Kosten, um eine strukturierte Ablage zu haben
    kosten_dayahead = {
        'DayAhead': {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'Tmin':     {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'Konstant': {'NCS': 0, 'HPC': 0, 'MCS': 0}
    }
    kosten_intraday = {
        'Intraday': {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'Tmin':     {'NCS': 0, 'HPC': 0, 'MCS': 0},
        'Konstant': {'NCS': 0, 'HPC': 0, 'MCS': 0}
    }

    # DayAhead: Daten filtern und in Dictionary packen
    df_ncs_dayahead   = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'DayAhead')].copy()
    df_ncs_konstant   = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'Konstant')].copy()
    df_ncs_tmin       = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'T_min')].copy()
    
    df_mcs_dayahead   = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'DayAhead')].copy()
    df_mcs_konstant   = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'Konstant')].copy()
    df_mcs_tmin       = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'T_min')].copy()
    
    df_hpc_dayahead   = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'DayAhead')].copy()
    df_hpc_konstant   = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'Konstant')].copy()
    df_hpc_tmin       = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'T_min')].copy()
    
    # Mittelwerte für DayAhead-Kosten ermitteln
    kosten_dayahead['DayAhead']['NCS']  = df_ncs_dayahead.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean()   / 100
    kosten_dayahead['Konstant']['NCS']  = df_ncs_konstant.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean()  / 100
    kosten_dayahead['Tmin']['NCS']      = df_ncs_tmin.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean()      / 100
    
    kosten_dayahead['DayAhead']['MCS']  = df_mcs_dayahead.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean()  / 100
    kosten_dayahead['Konstant']['MCS']  = df_mcs_konstant.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean()  / 100
    kosten_dayahead['Tmin']['MCS']      = df_mcs_tmin.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean()      / 100
    
    kosten_dayahead['DayAhead']['HPC']  = df_hpc_dayahead.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean()  / 100
    kosten_dayahead['Konstant']['HPC']  = df_hpc_konstant.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean()  / 100
    kosten_dayahead['Tmin']['HPC']      = df_hpc_tmin.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean()      / 100

    # Intraday: Daten filtern und in Dictionary packen
    df_ncs_intraday   = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'Intraday')].copy()
    df_ncs_konstant   = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'Konstant')].copy()
    df_ncs_tmin       = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'T_min')].copy()
    
    df_mcs_intraday   = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'Intraday')].copy()
    df_mcs_konstant   = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'Konstant')].copy()
    df_mcs_tmin       = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'T_min')].copy()
    
    df_hpc_intraday   = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'Intraday')].copy()
    df_hpc_konstant   = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'Konstant')].copy()
    df_hpc_tmin       = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'T_min')].copy()
    
    # Mittelwerte für Intraday-Kosten ermitteln
    # Hier werden zusätzlich /10 dividiert, wie im Originalcode
    kosten_intraday['Intraday']['NCS']  = df_ncs_intraday.groupby('LKW_ID')['Kosten_Intraday'].sum().mean()   / 100 / 10
    kosten_intraday['Konstant']['NCS']  = df_ncs_konstant.groupby('LKW_ID')['Kosten_Intraday'].sum().mean()   / 100 / 10
    kosten_intraday['Tmin']['NCS']      = df_ncs_tmin.groupby('LKW_ID')['Kosten_Intraday'].sum().mean()       / 100 / 10
    
    kosten_intraday['Intraday']['MCS']  = df_mcs_intraday.groupby('LKW_ID')['Kosten_Intraday'].sum().mean()   / 100 / 10
    kosten_intraday['Konstant']['MCS']  = df_mcs_konstant.groupby('LKW_ID')['Kosten_Intraday'].sum().mean()   / 100 / 10
    kosten_intraday['Tmin']['MCS']      = df_mcs_tmin.groupby('LKW_ID')['Kosten_Intraday'].sum().mean()       / 100 / 10
    
    kosten_intraday['Intraday']['HPC']  = df_hpc_intraday.groupby('LKW_ID')['Kosten_Intraday'].sum().mean()   / 100 / 10
    kosten_intraday['Konstant']['HPC']  = df_hpc_konstant.groupby('LKW_ID')['Kosten_Intraday'].sum().mean()   / 100 / 10
    kosten_intraday['Tmin']['HPC']      = df_hpc_tmin.groupby('LKW_ID')['Kosten_Intraday'].sum().mean()       / 100 / 10
    
    # Excel-Export: DayAhead-Kosten
    data_dayahead = [
        ['Durchschnittliche Kosten pro Ladevorgang (Day-Ahead) in Euro'],
        '',
        ['Ladetyp', 'DayAhead-Strategie', 'Konstant-Strategie', 'Tmin-Strategie'],
        ['NCS', 
         kosten_dayahead['DayAhead']['NCS'], 
         kosten_dayahead['Konstant']['NCS'], 
         kosten_dayahead['Tmin']['NCS']
        ],
        ['MCS', 
         kosten_dayahead['DayAhead']['MCS'], 
         kosten_dayahead['Konstant']['MCS'], 
         kosten_dayahead['Tmin']['MCS']
        ],
        ['HPC', 
         kosten_dayahead['DayAhead']['HPC'], 
         kosten_dayahead['Konstant']['HPC'], 
         kosten_dayahead['Tmin']['HPC']
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
        
    # Excel-Export: Intraday-Kosten
    data_intraday = [
        ['Durchschnittliche Kosten pro Ladevorgang (Intraday) in Euro'],
        '',
        ['Ladetyp', 'Intraday-Strategie', 'Konstant-Strategie', 'Tmin-Strategie'],
        ['NCS', 
         kosten_intraday['Intraday']['NCS'], 
         kosten_intraday['Konstant']['NCS'],
         kosten_intraday['Tmin']['NCS'],
        ],
        ['MCS', 
         kosten_intraday['Intraday']['MCS'], 
         kosten_intraday['Konstant']['MCS'],
         kosten_intraday['Tmin']['MCS'],
        ],
        ['HPC', 
         kosten_intraday['Intraday']['HPC'], 
         kosten_intraday['Konstant']['HPC'],
         kosten_intraday['Tmin']['HPC'],
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
    
    # Für DayAhead
    df_dayahead_nacht = df[(df['Ladestrategie'] == 'DayAhead') & (df['Ladetyp'] == 'NCS')]
    df_dayahead_schnell = df[(df['Ladestrategie'] == 'DayAhead') & (df['Ladetyp'].isin(['HPC', 'MCS']))]
    
    df_konstant_nacht = df[(df['Ladestrategie'] == 'Konstant') & (df['Ladetyp'] == 'NCS')]
    df_konstant_schnell = df[(df['Ladestrategie'] == 'Konstant') & (df['Ladetyp'].isin(['HPC', 'MCS']))]
    
    df_tmin = df[df['Ladestrategie'] == 'T_min']
    
    # Gruppenbildung
    kosten_opt_nacht = df_dayahead_nacht.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0).tolist()
    kosten_opt_schnell = df_dayahead_schnell.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0).tolist()
    kosten_konstant_nacht = df_konstant_nacht.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0).tolist()
    kosten_konstant_schnell = df_konstant_schnell.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0).tolist()
    
    kosten_tmin_dayahead = df_tmin.groupby('Stunde')['Kosten_DayAhead'].sum().reindex(range(24), fill_value=0).tolist()
    
    data_dayahead = [
        ['Kostenvergleich Stunde DayAhead'],
        '',
        ['Stunden'] + list(range(24)),
        '',
        ['Total Cost Tmin'] + kosten_tmin_dayahead,
        ['Total Cost Konstant'] + [kosten_konstant_nacht[i] + kosten_konstant_schnell[i] for i in range(24)],
        ['Total Cost DayAhead'] + [kosten_opt_nacht[i] + kosten_opt_schnell[i]for i in range(24)],
        ['Total Delta'] + [(kosten_opt_nacht[i] + kosten_opt_schnell[i]) - (kosten_konstant_nacht[i] + kosten_konstant_schnell[i]) for i in range(24)],
        ['Delta Nachtlader'] + [kosten_opt_nacht[i] - kosten_konstant_nacht[i]for i in range(24)],
        ['Delta Schnelllader'] + [kosten_opt_schnell[i] - kosten_konstant_schnell[i]for i in range(24)],
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
    
    kosten_opt_nacht_intra = df_intraday_nacht.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0).tolist()
    kosten_opt_schnell_intra = df_intraday_schnell.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0).tolist()
    kosten_konstant_nacht_intra = df_konstant_nacht.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0).tolist()
    kosten_konstant_schnell_intra = df_konstant_schnell.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0).tolist()
    
    kosten_tmin_intra = df_tmin.groupby('Stunde')['Kosten_Intraday'].sum().reindex(range(24), fill_value=0).tolist()
    
    data_intraday = [
        ['Kostenvergleich Stunde Intraday'],
        '',
        ['Stunden'] + list(range(24)),
        '',
        ['Total Cost Tmin'] + kosten_tmin_intra,
        ['Total Cost Konstant'] + [kosten_konstant_nacht_intra[i] + kosten_konstant_schnell_intra[i]for i in range(24)],
        ['Total Cost Intraday'] + [kosten_opt_nacht_intra[i] + kosten_opt_schnell_intra[i]for i in range(24)],
        ['Total Delta'] + [(kosten_opt_nacht_intra[i] + kosten_opt_schnell_intra[i])  - (kosten_konstant_nacht_intra[i] + kosten_konstant_schnell_intra[i]) for i in range(24)],
        ['Delta Nachtlader'] + [kosten_opt_nacht_intra[i] - kosten_konstant_nacht_intra[i] for i in range(24)],
        ['Delta Schnelllader'] + [kosten_opt_schnell_intra[i] - kosten_konstant_schnell_intra[i] for i in range(24)],
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


def main():
    # Verzeichnisse/Dateipfade zentral angeben
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path_input = os.path.join(base_dir, 'data', 'epex', 'lastgang_lkw','lastgang_lkw_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')
    path_results = os.path.join(base_dir, 'output', 'results_epex.xlsx')
    
    # Lastgang nur einmal einlesen
    df = pd.read_csv(path_input, sep=';', decimal=',')
    
    # Aufrufe der Funktionen mit demselben DataFrame
    kosten_pro_woche(df, path_results)
    kosten_pro_ladevorgang(df, path_results)
    kostendifferenz_pro_stunde(df, path_results)


if __name__ == '__main__':
    time_start = time.time()
    main()
    time_end = time.time()
    
    print(f"Laufzeit: {time_end - time_start:.2f} Sekunden")


