import pandas as pd
import os
import logging
logging.basicConfig(filename='logs.log', level=logging.DEBUG, format='%(asctime)s; %(levelname)s; %(message)s')

def ef_base_wochentag():
    logging.info('Wochentage')

    path_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'flex', 'kpis','ef_lang', 'ef_lang_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')
    path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results.xlsx')
    
    df = pd.read_csv(path_input, sep=';', decimal=',')
    
    data = [
        ['Base Case'],
        '',
        ['Zeit'] + list(range(0, 1440, 5)),
        '',
        ['Montag'] + df[:288]["Leistung_Total"].tolist(),
        ['Dienstag'] + df[288:576]["Leistung_Total"].tolist(),
        ['Mittwoch'] + df[576:864]["Leistung_Total"].tolist(),
        ['Donnerstag'] + df[864:1152]["Leistung_Total"].tolist(),
        ['Freitag'] + df[1152:1440]["Leistung_Total"].tolist(),
        ['Samstag'] + df[1440:1728]["Leistung_Total"].tolist(),
        ['Sonntag'] + df[1728:]["Leistung_Total"].tolist(),
    ]
    
    
    df_results = pd.DataFrame(data)

    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results.to_excel(writer, sheet_name='Base (Wochentag)', index=False, header=False, startrow=0, startcol=0)

def ef_base_ladetyp():
    path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results.xlsx')
    path_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'flex', 'kpis', 'ef', 'ef_cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base.csv')


    df = pd.read_csv(os.path.join(path_input), sep=';', decimal=',')
    
    
    data = [
        ['Base'],
        '',
        ['Zeit'] + df["Zeit_Tag"].tolist(),
        '',
        ['NCS'] + df["Leistung_NCS"].tolist(),
        ['HPC'] + df["Leistung_HPC"].tolist(),
        ['MCS'] + df["Leistung_MCS"].tolist(),
        '',
        ['Zeit'] + df["Zeit_Tag"].tolist(),
        '',
        ['Total'] + df["Leistung_Total"].tolist(),
    ]
    
    df_results = pd.DataFrame(data)

    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results.to_excel(writer, sheet_name='Base (Ladetyp)', index=False, header=False, startrow=0, startcol=0)
    
def ergebnisse_updaten():
    logging.info('Ergebnisse updaten')
    path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results.xlsx')
    path_apfi_mpfi = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'flex', 'kpis', 'apfi_mpfi')
    path_efi = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'flex', 'kpis', 'efi')
    path_ef = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'flex', 'kpis', 'ef')
    path_lastgang = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'flex', 'lastgang')
    # df_results = pd.read_excel(path_results, sheet_name='Results')
    
    # df_results.drop(columns=['Szenario'], inplace=True)
    # df_results.drop(index=0, inplace=True)
    
    dict_results = {}
    
    for file_name in os.listdir(path_apfi_mpfi):
        if file_name.endswith(".csv"):
            df_apfi_mpfi = pd.read_csv(os.path.join(path_apfi_mpfi, file_name), sep=';', decimal=',')
            apfi = df_apfi_mpfi["APFI"].sum()
            mpfi = df_apfi_mpfi["MPFI"].sum()
            
            file_base_name = file_name.split(".")[0]
            szenario = file_base_name.split("apfi_mpfi_", 1)[1]
            szenario_name = szenario.split("_")[-1]
            szenario_nummer = int(szenario.split("_")[-2])
            
            dict_results[szenario_name] = [szenario_nummer, None, None, None, None, None, None, None, apfi, None, mpfi, None, None, None]
            
    
    for file_name in os.listdir(path_lastgang):
        if file_name.endswith(".csv"):
            df_lastgang = pd.read_csv(os.path.join(path_lastgang, file_name), sep=';', decimal=',')
            ladequote = df_lastgang["Ladequote"].iloc[0]
            
            file_base_name = file_name.split(".")[0]
            szenario = file_base_name.split("lastgang_", 1)[1]
            szenario_name = szenario.split("_")[-1]
            dict_results[szenario_name][13] = ladequote

        
    
    for file_name in os.listdir(path_efi):
        if file_name.endswith(".csv"):
            df_efi = pd.read_csv(os.path.join(path_efi, file_name), sep=';', decimal=',')
            efi = df_efi["EFI"].sum()
            
            file_base_name = file_name.split(".")[0]
            szenario = file_base_name.split("efi_", 1)[1]
            szenario_name = szenario.split("_")[-1]
            dict_results[szenario_name][3] = efi
                        
    for file_name in os.listdir(path_ef):
        if file_name.endswith(".csv"):
            df_ef = pd.read_csv(os.path.join(path_ef, file_name), sep=';', decimal=',')
            ef = df_ef["Leistung_Total"].mean()
            
            file_base_name = file_name.split(".")[0]
            szenario = file_base_name.split("ef_", 1)[1]
            szenario_name = szenario.split("_")[-1]
            dict_results[szenario_name][5] = ef

    df_results = pd.DataFrame(dict_results)
    df_results = df_results.sort_values(by=0, axis=1)

    efi_base = df_results.iloc[3, 0]
    efc_base = df_results.iloc[5, 0]
    apfi_base = df_results.iloc[8, 0]
    mpfi_base = df_results.iloc[10, 0]
    
    for i in range(1, df_results.shape[1]):
        efi = df_results.iloc[3, i]
        efc = df_results.iloc[5, i]
        apfi = df_results.iloc[8, i]
        mpfi = df_results.iloc[10, i]
        
        df_results.iloc[4, i] = efi / efi_base -1
        df_results.iloc[6, i] = efc / efc_base -1
        df_results.iloc[9, i] = apfi / apfi_base -1
        df_results.iloc[11, i] = mpfi / mpfi_base -1
    
    
    
    with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_results.to_excel(writer, sheet_name='Results', index=False, header=True, startrow=0, startcol=1)
    
def szenarien_vergleichen():
    logging.info('Szenarien vergleichen')
    list_name_vergleiche = ['Cluster', 'Pow_NCS', 'Pow_HPC', 'Pow_MCS', 'Schnellzeit', 'Nachtzeit', 'Netzanschluss', 'Ladequoten', 'Bidirektional']
    
    list_bidirektional = [
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base', # Base
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_B_2_Bidirektional', # Bidirektional 
    ]
    
    list_cluster = [
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base',
        'cl_1_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_3_Cluster-1',
        'cl_3_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_4_Cluster-3'   
    ]
    
    list_pow_ncs = [
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base',
        'cl_2_quote_80-80-80_netz_100_pow_110-100-100_pause_45-540_M_5_Leistung-NCS-110',
        'cl_2_quote_80-80-80_netz_100_pow_120-100-100_pause_45-540_M_6_Leistung-NCS-120',
        'cl_2_quote_80-80-80_netz_100_pow_130-100-100_pause_45-540_M_7_Leistung-NCS-130',
        'cl_2_quote_80-80-80_netz_100_pow_140-100-100_pause_45-540_M_8_Leistung-NCS-140'
    ]
    
    list_pow_hpc = [
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base',
        'cl_2_quote_80-80-80_netz_100_pow_100-110-100_pause_45-540_M_9_Leistung-HPC-110',
        'cl_2_quote_80-80-80_netz_100_pow_100-120-100_pause_45-540_M_10_Leistung-HPC-120',
        'cl_2_quote_80-80-80_netz_100_pow_100-130-100_pause_45-540_M_11_Leistung-HPC-130',
        'cl_2_quote_80-80-80_netz_100_pow_100-140-100_pause_45-540_M_12_Leistung-HPC-140'
    ]
    
    list_pow_mcs = [
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base',
        'cl_2_quote_80-80-80_netz_100_pow-110_100-100-110_pause_45-540_M_13_Leistung-MCS-110',
        'cl_2_quote_80-80-80_netz_100_pow-120_100-100-120_pause_45-540_M_14_Leistung-MCS-120',
        'cl_2_quote_80-80-80_netz_100_pow-130_100-100-130_pause_45-540_M_15_Leistung-MCS-130',
        'cl_2_quote_80-80-80_netz_100_pow-140_100-100-140_pause_45-540_M_16_Leistung-MCS-140',
    ]

    list_schnellzeit = [
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base',
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_50-540_M_17_Schnellzeit-110',
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_55-540_M_18_Schnellzeit-120',
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_60-540_M_19_Schnellzeit-130',
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_65-540_M_20_Schnellzeit-140'
    ]

    list_nachtzeit = [
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base',
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-595_M_21_Nachtzeit-110',
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-650_M_22_Nachtzeit-120',
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-705_M_23_Nachtzeit-130',
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-760_M_24_Nachtzeit-140'
    ]
    
    list_netzanschluss = [
        'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base',
        'cl_2_quote_80-80-80_netz_90_pow_100-100-100_pause_45-540_M_25_Netzanschluss-90',
        'cl_2_quote_80-80-80_netz_80_pow_100-100-100_pause_45-540_M_26_Netzanschluss-80',
        'cl_2_quote_80-80-80_netz_70_pow_100-100-100_pause_45-540_M_27_Netzanschluss-70',
        'cl_2_quote_80-80-80_netz_60_pow_100-100-100_pause_45-540_M_28_Netzanschluss-60',
        'cl_2_quote_80-80-80_netz_50_pow_100-100-100_pause_45-540_M_29_Netzanschluss-50',
        'cl_2_quote_80-80-80_netz_40_pow_100-100-100_pause_45-540_M_30_Netzanschluss-40',
        'cl_2_quote_80-80-80_netz_30_pow_100-100-100_pause_45-540_M_31_Netzanschluss-30',
        'cl_2_quote_80-80-80_netz_20_pow_100-100-100_pause_45-540_M_32_Netzanschluss-20',
        'cl_2_quote_80-80-80_netz_10_pow_100-100-100_pause_45-540_M_33_Netzanschluss-10'
    ]

    
    list_vergleiche = [list_cluster, list_pow_ncs, list_pow_hpc, list_pow_mcs, list_schnellzeit, list_nachtzeit, list_netzanschluss, list_bidirektional]
    
    
        
    for index, list in enumerate(list_vergleiche):
        list_szenario = []
        list_ef = []
        
        for szenario in list:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'flex', 'kpis', 'ef', f'ef_{szenario}.csv')
            df = pd.read_csv(path, sep=';', decimal=',')
            scenario_name = szenario.split("_")[-1]
            total_leistung = df["Leistung_Total"].tolist()
            
            list_szenario.append(scenario_name)
            list_ef.append(total_leistung)
        
        data = [
            [list_name_vergleiche[index]],
            '',
            ['Zeit'] + df["Zeit_Tag"].tolist(),
            '',
        ]
        
        for i in range(len(list_szenario)):
            data.append([list_szenario[i]] + list_ef[i])
        
        df_results = pd.DataFrame(data)
        
        path_results = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'results.xlsx')
        with pd.ExcelWriter(path_results, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            sheet_name = f'Vergleich ({list_name_vergleiche[index]})'
            df_results.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=0, startcol=0)
    
        
        
def main():
    logging.info('Start: Daten aufbereiten')
    ef_base_wochentag()
    ef_base_ladetyp()
    ergebnisse_updaten()
    szenarien_vergleichen()

if __name__ == '__main__':
    main()

