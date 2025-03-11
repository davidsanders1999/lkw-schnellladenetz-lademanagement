import pandas as pd
import os
import config
import logging
logging.basicConfig(filename='logs.log', level=logging.DEBUG, format='%(asctime)s; %(levelname)s; %(message)s')

def berechne_ef(szenario):
    """
    Bearbeitet ein einzelnes Szenario, berechnet die kumulative Differenz zwischen `p_max` und `p_min`,
    und speichert die Ergebnisse in einer CSV-Datei.
    """
    # Definiere Eingabe- und Ausgabepfade
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'lastgang')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'kpis', 'ef')

    # Erstelle die Zeitliste für den Tag (5-Minuten-Intervalle für 8 Tage)
    zeit_tag = list(range(0, 1440, 5)) * 8

    # Lade die Lastgang-Daten für das Szenario
    df_lastgang = pd.read_csv(
        os.path.join(eingabe_pfad, f'lastgang_{szenario}.csv'), sep=';', decimal=','
    )

    # Erstelle ein leeres DataFrame für die Ergebnisse
    df_kombiniert = pd.DataFrame(
        columns=['Zeit_Tag', 'Leistung_Total', 'Leistung_NCS', 'Leistung_HPC', 'Leistung_MCS']
    )
    df_kombiniert['Zeit_Tag'] = zeit_tag

    # Berechne kumulative Differenzen für jede Leistungsart
    for leistung in ['Leistung_Total', 'Leistung_NCS', 'Leistung_HPC', 'Leistung_MCS']:
        df_pmax_kumsum = (
            df_lastgang[df_lastgang['Ladestrategie'] == 'p_max']
            .groupby('Zeit')[leistung].sum() * 5 / 60
        ).cumsum()

        df_pmin_kumsum = (
            df_lastgang[df_lastgang['Ladestrategie'] == 'p_min']
            .groupby('Zeit')[leistung].sum() * 5 / 60
        ).cumsum()

        # Berechne die Differenz und speichere die Ergebnisse im kombinierten DataFrame
        df_kumulative_differenz = pd.DataFrame(
            df_pmax_kumsum - df_pmin_kumsum, columns=[leistung]
        ).reset_index()

        df_kumulative_differenz[leistung] = df_kumulative_differenz[leistung].round(1)
        df_kombiniert[leistung] = df_kumulative_differenz[leistung]

    # Gruppiere nach `Zeit_Tag` und berechne den Durchschnitt über eine Woche (7 Tage)
    df_kombiniert = df_kombiniert.groupby('Zeit_Tag').sum().reset_index()
    df_kombiniert[['Leistung_Total', 'Leistung_NCS', 'Leistung_HPC', 'Leistung_MCS']] /= 7

    # Speichere die Ergebnisse im Ausgabeverzeichnis
    os.makedirs(ausgabe_pfad, exist_ok=True)
    ausgabe_datei = os.path.join(ausgabe_pfad, f'ef_{szenario}.csv')
    df_kombiniert.to_csv(ausgabe_datei, sep=';', decimal=',', index=False)

def berechne_ef_lang(szenario):
    """
    Bearbeitet ein einzelnes Szenario, berechnet die kumulative Differenz zwischen `p_max` und `p_min`,
    und speichert die Ergebnisse in einer CSV-Datei.
    """
    # Definiere Eingabe- und Ausgabepfade
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'lastgang')
    eingabe_pfad_lkw = os.path.join(basis_pfad, 'data', 'flex', 'lastgang_lkw')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'kpis', 'ef_lang')

    # Erstelle die Zeitliste für den Tag (5-Minuten-Intervalle für 8 Tage)
    zeit_tag = list(range(0, 11520, 5))

    # Lade die Lastgang-Daten für das Szenario
    df_lastgang = pd.read_csv(
        os.path.join(eingabe_pfad, f'lastgang_{szenario}.csv'), sep=';', decimal=','
    )
    
    df_lastgang_lkw = pd.read_csv(
        os.path.join(eingabe_pfad_lkw, f'lastgang_lkw_{szenario}.csv'), sep=';', decimal=','
    )

    # Erstelle ein leeres DataFrame für die Ergebnisse
    df_kombiniert = pd.DataFrame(
        columns=['Zeit_Tag', 'Leistung_Total', 'Leistung_NCS', 'Leistung_HPC', 'Leistung_MCS']
    )
    df_kombiniert['Zeit_Tag'] = zeit_tag

    # Berechne kumulative Differenzen für jede Leistungsart
    for leistung in ['Leistung_Total', 'Leistung_NCS', 'Leistung_HPC', 'Leistung_MCS']:
        df_pmax_kumsum = (
            df_lastgang[df_lastgang['Ladestrategie'] == 'p_max']
            .groupby('Zeit')[leistung].sum() * (5 / 60)
        ).cumsum()

        df_pmin_kumsum = (
            df_lastgang[df_lastgang['Ladestrategie'] == 'p_min']
            .groupby('Zeit')[leistung].sum() * (5 / 60)
        ).cumsum()

        # Berechne die Differenz und speichere die Ergebnisse im kombinierten DataFrame
        df_kumulative_differenz = pd.DataFrame(
            df_pmax_kumsum - df_pmin_kumsum, columns=[leistung]
        ).reset_index()

        df_kumulative_differenz[leistung] = df_kumulative_differenz[leistung].round(1)
        df_kombiniert[leistung] = df_kumulative_differenz[leistung]

    anzahl_lkw_hpc = df_lastgang_lkw[df_lastgang_lkw['Ladetyp'] == 'HPC']['LKW_ID'].nunique()
    anzahl_lkw_ncs = df_lastgang_lkw[df_lastgang_lkw['Ladetyp'] == 'NCS']['LKW_ID'].nunique()
    anzahl_lkw_mcs = df_lastgang_lkw[df_lastgang_lkw['Ladetyp'] == 'MCS']['LKW_ID'].nunique()
    
    efc_hpc = df_kombiniert['Leistung_HPC'].sum() * (5/60) / anzahl_lkw_hpc
    efc_ncs = df_kombiniert['Leistung_NCS'].sum() * (5/60) / anzahl_lkw_ncs
    efc_mcs = df_kombiniert['Leistung_MCS'].sum() * (5/60) / anzahl_lkw_mcs
    
    print(f'EFC pro NCS [kWh^2]: {efc_ncs}')
    print(f'EFC pro HPC [kWh^2]: {efc_hpc}')
    print(f'EFC pro MCS [kWh^2]: {efc_mcs}')
    print()
    print(f'EFC pro NCS [kWh]: {efc_ncs/9}')
    print(f'EFC pro HPC [kWh]: {efc_hpc/0.75}')
    print(f'EFC pro MCS [kWh]: {efc_mcs/0.75}')
    print()

    # Speichere die Ergebnisse im Ausgabeverzeichnis
    os.makedirs(ausgabe_pfad, exist_ok=True)
    ausgabe_datei = os.path.join(ausgabe_pfad, f'ef_lang_{szenario}.csv')
    df_kombiniert.to_csv(ausgabe_datei, sep=';', decimal=',', index=False)

def berechne_EFI(szenario):
    # Definiere Eingabe- und Ausgabepfade
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'lastgang_lkw')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'kpis', 'efi')

    # Lade die Lastgang-Daten für das Szenario
    df_lastgang = pd.read_csv(os.path.join(eingabe_pfad, f'lastgang_lkw_{szenario}.csv'), sep=';', decimal=',')

    df_lastgang_p_max = df_lastgang[df_lastgang['Ladestrategie'] == 'p_max']
    df_lastgang_p_max = df_lastgang_p_max[df_lastgang_p_max['Max_Leistung'].notna()]
    
    # EFI Total berechnen
    E_pot = sum(df_lastgang_p_max['Max_Leistung']) * (5/60)
    E_ch = sum(df_lastgang_p_max['Leistung']) * (5/60)
    EFI = 1 - E_ch/E_pot
    
    # EFI NCS berechnen
    E_pot_NCS = sum(df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'NCS']['Max_Leistung']) * (5/60)
    E_ch_NCS = sum(df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'NCS']['Leistung']) * (5/60)
    EFI_NCS = 1 - E_ch_NCS/E_pot_NCS
   
    
    # Avg. Energiemenge pro NCS Ladevorgang
    num_ladevorgaenge = df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'NCS']['LKW_ID'].nunique()
    E_ch_NCS_avg = E_ch_NCS / num_ladevorgaenge
    
    # EFI HPC berechnen
    E_pot_HPC = sum(df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'HPC']['Max_Leistung']) * (5/60)
    E_ch_HPC = sum(df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'HPC']['Leistung']) * (5/60)
    EFI_HPC = 1 - E_ch_HPC/E_pot_HPC
    
    # Avg. Energiemenge pro HPC Ladevorgang
    num_ladevorgaenge = df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'HPC']['LKW_ID'].nunique()
    E_ch_HPC_avg = E_ch_HPC / num_ladevorgaenge
    
    # EFI MCS berechnen
    E_pot_MCS = sum(df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'MCS']['Max_Leistung']) * (5/60)
    E_ch_MCS = sum(df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'MCS']['Leistung']) * (5/60)
    EFI_MCS = 1 - E_ch_MCS/E_pot_MCS
    
    # Avg. Energiemenge pro MCS Ladevorgang
    num_ladevorgaenge = df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'MCS']['LKW_ID'].nunique()
    E_ch_MCS_avg = E_ch_MCS / num_ladevorgaenge
    
    # Anzahl Schnellladevorgänge und Nachtladevorgänge
    num_nachtladevorgaenge = df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'NCS']['LKW_ID'].nunique()
    num_hpcladevorgaenge = df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'HPC']['LKW_ID'].nunique()
    num_mcs_ladevorgaenge = df_lastgang_p_max[df_lastgang_p_max['Ladetyp'] == 'MCS']['LKW_ID'].nunique()
    
    
    print(f'EFI (NCS): {EFI_NCS}')
    print(f'EFI (HPC): {EFI_HPC}')
    print(f'EFI (MCS): {EFI_MCS}')
    print()
    print(f'Energie pro NCS: {E_ch_NCS_avg}')
    print(f'Energie pro HPC: {E_ch_HPC_avg}')
    print(f'Energie pro MCS: {E_ch_MCS_avg}')
    print()
    print(f'Anzahl NCS Ladevorgänge: {num_nachtladevorgaenge}')
    print(f'Anzahl HPC Ladevorgänge: {num_mcs_ladevorgaenge}')
    print(f'Anzahl NCS Ladevorgänge: {num_hpcladevorgaenge}')

    df_efi = pd.DataFrame(columns=['Szenario','EFI'])
    df_efi['Szenario'] = [szenario]
    df_efi['EFI'] = [EFI]
    df_efi['EFI_NCS'] = [EFI_NCS]
    df_efi['EFI_HPC'] = [EFI_HPC]
    df_efi['EFI_MCS'] = [EFI_MCS]
    os.makedirs(ausgabe_pfad, exist_ok=True)
    df_efi.to_csv(os.path.join(ausgabe_pfad, f'efi_{szenario}.csv'), sep=';', decimal=',', index=False)
    return None

def berechne_MPFI_APFI(szenario):
    # Definiere Eingabe- und Ausgabepfade
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad_lastgang = os.path.join(basis_pfad, 'data', 'flex', 'lastgang')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'kpis','apfi_mpfi')

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
    
    if dict_szenario['ladequote'] == dict_base['ladequote'] and dict_szenario['cluster'] == dict_base['cluster'] and dict_szenario['pause'] == dict_base['pause']:
        df_ladehub = pd.read_csv(os.path.join(basis_pfad, 'data','konfiguration_ladehub',f'anzahl_ladesaeulen_{base_case}.csv'), sep=';', decimal=',')
    else:
        df_ladehub = pd.read_csv(os.path.join(basis_pfad, 'data','konfiguration_ladehub',f'anzahl_ladesaeulen_{szenario}.csv'), sep=';', decimal=',')
        

    
    netzanschlussfaktor = int(szenario.split('_')[5]) / 100

    # ladeleistung = {
    #     'NCS': int(int(szenario.split('_')[7].split('-')[0])/100 * config.leistung_ladetyp['NCS']),
    #     'HPC': int(int(szenario.split('_')[7].split('-')[1])/100 * config.leistung_ladetyp['HPC']),
    #     'MCS': int(int(szenario.split('_')[7].split('-')[2])/100 * config.leistung_ladetyp['MCS'])
    # }

    ladeleistung = {
        'NCS': int(config.leistung_ladetyp['NCS']),
        'HPC': int(config.leistung_ladetyp['HPC']),
        'MCS': int(config.leistung_ladetyp['MCS'])
    }

    max_saeulen = {
        'NCS': int(df_ladehub['NCS'][0]),
        'HPC': int(df_ladehub['HPC'][0]),
        'MCS': int(df_ladehub['MCS'][0])
    }
    
    netzanschluss = netzanschlussfaktor * (ladeleistung['NCS'] * max_saeulen['NCS'] + ladeleistung['HPC'] * max_saeulen['HPC'] + ladeleistung['MCS'] * max_saeulen['MCS'])
    
    # Lade die Lastgang-Daten für das Szenario
    df_lastgang = pd.read_csv(os.path.join(eingabe_pfad_lastgang, f'lastgang_{szenario}.csv'), sep=';', decimal=',')
    
    df_lastgang_p_max = df_lastgang[df_lastgang['Ladestrategie'] == 'p_max']
     
    df_time = df_lastgang_p_max.groupby('Zeit')['Leistung_Total'].sum().reset_index()
    df_time['Tag'] = df_time['Zeit'] // 1440 + 1
    df_max = df_time.groupby('Tag')['Leistung_Total'].max().reset_index()
    p_max = df_max['Leistung_Total'].mean()
    
    df_lastgang_not_zero = df_lastgang_p_max[df_lastgang_p_max['Leistung_Max_Total'] != 0]
    df_lastgang_not_zero_time = df_lastgang_not_zero.groupby('Zeit')['Leistung_Total'].sum().reset_index()
    p_avg = df_lastgang_not_zero_time['Leistung_Total'].mean()
    
    
    MPFI = 1 - p_max/netzanschluss
    APFI = 1 - p_avg/netzanschluss
    
    df_apfi_mpfi = pd.DataFrame(columns=['Szenario','MPFI','APFI'])
    
    df_apfi_mpfi['Szenario'] = [szenario]
    df_apfi_mpfi['MPFI'] = [MPFI]
    df_apfi_mpfi['APFI'] = [APFI]
    
    os.makedirs(ausgabe_pfad, exist_ok=True)
    df_apfi_mpfi.to_csv(os.path.join(ausgabe_pfad, f'apfi_mpfi_{szenario}.csv'), sep=';', decimal=',', index=False)
    
    return None

def main():
    """
    Hauptfunktion, um alle Szenarien zu verarbeiten und Ergebnisse zu speichern.
    """
    logging.info('Start: Flex KPIs')
    # Bearbeite jedes Szenario in der konfigurierten Szenarienliste
    for szenario in config.list_szenarien:
        logging.info(f'Flex KPIs: {szenario}')
        berechne_ef(szenario)
        berechne_ef_lang(szenario)
        berechne_EFI(szenario)
        berechne_MPFI_APFI(szenario)


if __name__ == "__main__":
    main()