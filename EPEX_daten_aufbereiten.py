import pandas as pd
import os

def weeks_intraday():

    path_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'epex', 'lastgang_lkw' ,'lastgang_lkw_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')
    path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results_epex.xlsx')
    
    df = pd.read_csv(path_input, sep=';', decimal=',')
    
    week_start = df['Woche'].min()
    week_end = df['Woche'].max()
    
    # Intraday-Strategie pro Woche
    df_intraday = df[df['Ladestrategie'] == 'Intraday'].copy()
    kosten_intraday = df_intraday.groupby('Woche')['Kosten_Intraday'].sum().tolist()
    print(kosten_intraday)
    
    df_tmin = df[df['Ladestrategie'] == 'T_min'].copy()
    kosten_tmin = df_tmin.groupby('Woche')['Kosten_Intraday'].sum().tolist()
    print(kosten_tmin)
    
    difference = [kosten_intraday[i] - kosten_tmin[i] for i in range(len(kosten_intraday))]
    
    data = [
        ['Kostenvergleich Intraday'],
        '',
        ['Wochen'] + list(range(week_start, week_end+1)),
        '',
        ['Intraday-Strategie'] + kosten_intraday,
        ['Tmin-Strategie'] + kosten_tmin,
        ['Delta Abs'] + difference,
        ['Delta Rel'] + [kosten_intraday[i] / kosten_tmin[i] for i in range(len(kosten_intraday))]
    ]
    
    df_results = pd.DataFrame(data)

    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results.to_excel(writer, sheet_name='Intraday_Weeks', index=False, header=False, startrow=0, startcol=0)


def weeks_dayahead():

    path_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'epex', 'lastgang_lkw' ,'lastgang_lkw_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')
    path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results_epex.xlsx')
    
    df = pd.read_csv(path_input, sep=';', decimal=',')
    
    week_start = df['Woche'].min()
    week_end = df['Woche'].max()
    
    # DayAhead-Strategie pro Woche
    df_dayahead = df[df['Ladestrategie'] == 'DayAhead'].copy()
    kosten_dayahead = df_dayahead.groupby('Woche')['Kosten_DayAhead'].sum().tolist()
    
    df_tmin = df[df['Ladestrategie'] == 'T_min'].copy()
    kosten_tmin = df_tmin.groupby('Woche')['Kosten_DayAhead'].sum().tolist()
    
    difference = [kosten_dayahead[i] - kosten_tmin[i] for i in range(len(kosten_dayahead))]
    
    data = [
        ['Kostenvergleich Day-Ahead'],
        '',
        ['Wochen'] + list(range(week_start, week_end+1)),
        '',
        ['DayAhead-Strategie'] + kosten_dayahead,
        ['Tmin-Strategie'] + kosten_tmin,
        ['Delta Abs'] + difference,
        ['Delta Rel'] + [kosten_dayahead[i] / kosten_tmin[i] for i in range(len(kosten_dayahead))],
    ]
    
    df_results = pd.DataFrame(data)

    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results.to_excel(writer, sheet_name='DayAhead_Weeks', index=False, header=False, startrow=0, startcol=0)
    

def ladetype_dayahead():
    
    path_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'epex', 'lastgang_lkw' ,'lastgang_lkw_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')
    path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results_epex.xlsx')
    
    df = pd.read_csv(path_input, sep=';', decimal=',')

    kosten_dayahead = {
        'DayAhead':{
            'NCS': 0,
            'HPC': 0,
            'MCS': 0
        },
        'Tmin':{
            'NCS': 0,
            'HPC': 0,
            'MCS': 0
        }
    }

    df_ncs_intraday = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'DayAhead')].copy()
    kosten_dayahead['DayAhead']['NCS'] = df_ncs_intraday.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() /100
    df_ncs_tmin = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'T_min')].copy()
    kosten_dayahead['Tmin']['NCS'] = df_ncs_tmin.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() /100
    
    df_mcs_intraday = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'DayAhead')].copy()
    kosten_dayahead['DayAhead']['MCS'] = df_mcs_intraday.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() /100
    df_mcs_tmin = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'T_min')].copy()
    kosten_dayahead['Tmin']['MCS'] = df_mcs_tmin.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() /100
    
    df_hpc_intraday = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'DayAhead')].copy()
    kosten_dayahead['DayAhead']['HPC'] = df_hpc_intraday.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() /100
    df_hpc_tmin = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'T_min')].copy()
    kosten_dayahead['Tmin']['HPC'] = df_hpc_tmin.groupby('LKW_ID')['Kosten_DayAhead'].sum().mean() / 100
    
    print(kosten_dayahead)
    
    kosten_intraday = {
        'Intraday':{
            'NCS': 0,
            'HPC': 0,
            'MCS': 0
        },
        'Tmin':{
            'NCS': 0,
            'HPC': 0,
            'MCS': 0
        }
    }
    
    df_ncs_intraday = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'Intraday')].copy()
    kosten_intraday['Intraday']['NCS'] = df_ncs_intraday.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() /100
    df_ncs_tmin = df[(df['Ladetyp'] == 'NCS') & (df['Ladestrategie'] == 'T_min')].copy()
    kosten_intraday['Tmin']['NCS'] = df_ncs_tmin.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() /100
    
    df_mcs_intraday = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'Intraday')].copy()
    kosten_intraday['Intraday']['MCS'] = df_mcs_intraday.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() /100
    df_mcs_tmin = df[(df['Ladetyp'] == 'MCS') & (df['Ladestrategie'] == 'T_min')].copy()
    kosten_intraday['Tmin']['MCS'] = df_mcs_tmin.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() /100
    
    df_hpc_intraday = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'Intraday')].copy()
    kosten_intraday['Intraday']['HPC'] = df_hpc_intraday.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() /100
    df_hpc_tmin = df[(df['Ladetyp'] == 'HPC') & (df['Ladestrategie'] == 'T_min')].copy()
    kosten_intraday['Tmin']['HPC'] = df_hpc_tmin.groupby('LKW_ID')['Kosten_Intraday'].sum().mean() /100
    
    print(kosten_intraday)
    
    
def days_dayahead():
    path_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'epex', 'lastgang_lkw' ,'lastgang_lkw_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')
    path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results_epex.xlsx')
    
    df = pd.read_csv(path_input, sep=';', decimal=',')
    df['Datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d %H:%M:%S')
    df['Stunde'] = df['Datum'].dt.hour  
            
    # DayAhead-Strategie pro Woche
    df_dayahead = df[df['Ladestrategie'] == 'DayAhead'].copy()
    kosten_dayahead = df_dayahead.groupby('Stunde')['Kosten_DayAhead'].sum().tolist()
    print(kosten_dayahead)
    
    df_tmin = df[df['Ladestrategie'] == 'T_min'].copy()
    kosten_tmin = df_tmin.groupby('Stunde')['Kosten_DayAhead'].sum().tolist()
        
    data = [
        ['Kostenvergleich Stunde Day-Ahead'],
        '',
        ['Stunden'] + list(range(24)),
        '',
        ['DayAhead-Strategie'] + kosten_dayahead,
        ['Tmin-Strategie'] + kosten_tmin,
        ['Delta Abs'] + [kosten_dayahead[i] - kosten_tmin[i] for i in range(len(kosten_dayahead))],
    ]
    
    df_results = pd.DataFrame(data)

    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results.to_excel(writer, sheet_name='DayAhead_Hours', index=False, header=False, startrow=0, startcol=0)

def days_intraday():
    path_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'epex', 'lastgang_lkw' ,'lastgang_lkw_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')
    path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results_epex.xlsx')
    
    df = pd.read_csv(path_input, sep=';', decimal=',')
    df['Datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d %H:%M:%S')
    df['Stunde'] = df['Datum'].dt.hour  
            
    # DayAhead-Strategie pro Woche
    df_dayahead = df[df['Ladestrategie'] == 'Intraday'].copy()
    kosten_intraday = df_dayahead.groupby('Stunde')['Kosten_Intraday'].sum().tolist()
    print(kosten_intraday)
    
    df_tmin = df[df['Ladestrategie'] == 'T_min'].copy()
    kosten_tmin = df_tmin.groupby('Stunde')['Kosten_Intraday'].sum().tolist()
    
    
        
    data = [
        ['Kostenvergleich Stunde Intraday'],
        '',
        ['Stunden'] + list(range(24)),
        '',
        ['Intraday-Strategie'] + kosten_intraday,
        ['Tmin-Strategie'] + kosten_tmin,
        ['Delta Abs'] + [kosten_intraday[i] - kosten_tmin[i] for i in range(len(kosten_intraday))],
        ['Delta Rel'] + [kosten_intraday[i] / kosten_tmin[i] - 1 for i in range(len(kosten_intraday))],
    ]
    
    df_results = pd.DataFrame(data)

    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results.to_excel(writer, sheet_name='Intraday_Hours', index=False, header=False, startrow=0, startcol=0)


def main():
    # weeks_intraday()
    # weeks_dayahead()
    # ladetype_dayahead()
    # days_dayahead()
    days_intraday()


if __name__ == '__main__':
    main()