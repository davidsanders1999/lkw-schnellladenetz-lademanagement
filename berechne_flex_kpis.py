import pandas as pd
import os
import config


def berechne_ef(szenario):
    """
    Bearbeitet ein einzelnes Szenario, berechnet die kumulative Differenz zwischen `p_max` und `p_min`,
    und speichert die Ergebnisse in einer CSV-Datei.
    """
    # Definiere Eingabe- und Ausgabepfade
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad = os.path.join(basis_pfad, 'data', 'lastgang')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'kpis', 'ef')

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
    ausgabe_datei = os.path.join(ausgabe_pfad, f'ef_{szenario}.csv')
    df_kombiniert.to_csv(ausgabe_datei, sep=';', decimal=',', index=False)

def berechne_ef_lang(szenario):
    """
    Bearbeitet ein einzelnes Szenario, berechnet die kumulative Differenz zwischen `p_max` und `p_min`,
    und speichert die Ergebnisse in einer CSV-Datei.
    """
    # Definiere Eingabe- und Ausgabepfade
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad = os.path.join(basis_pfad, 'data', 'lastgang')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'kpis', 'ef_lang')

    # Erstelle die Zeitliste für den Tag (5-Minuten-Intervalle für 8 Tage)
    zeit_tag = list(range(0, 11520, 5))

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

    # Speichere die Ergebnisse im Ausgabeverzeichnis
    ausgabe_datei = os.path.join(ausgabe_pfad, f'ef_lang_{szenario}.csv')
    df_kombiniert.to_csv(ausgabe_datei, sep=';', decimal=',', index=False)

def berechne_EFI(szenario):
    # Definiere Eingabe- und Ausgabepfade
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad = os.path.join(basis_pfad, 'data', 'lastgang')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'kpis', 'efi')

    # Lade die Lastgang-Daten für das Szenario
    df_lastgang = pd.read_csv(os.path.join(eingabe_pfad, f'lastgang_{szenario}.csv'), sep=';', decimal=',')

    df_lastgang_p_max = df_lastgang[df_lastgang['Ladestrategie'] == 'p_max']
    E_pot = sum(df_lastgang_p_max['Leistung_Max_Total']) * (5/60)
    E_ch = sum(df_lastgang_p_max['Leistung_Total']) * (5/60)
    EFI = 1 - E_ch/E_pot
    
    df_efi = pd.DataFrame(columns=['Szenario','EFI'])
    df_efi['Szenario'] = [szenario]
    df_efi['EFI'] = [EFI]
    df_efi.to_csv(os.path.join(ausgabe_pfad, f'efi_{szenario}.csv'), sep=';', decimal=',', index=False)
    return None

def berechne_MPFI_APFI(szenario):
    # Definiere Eingabe- und Ausgabepfade
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad_lastgang = os.path.join(basis_pfad, 'data', 'lastgang')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'kpis','apfi_mpfi')

    df_ladehub = pd.read_csv(os.path.join(basis_pfad, 'data','konfiguration_ladehub',f'anzahl_ladesaeulen_{szenario}.csv'), sep=';', decimal=',')
    
    netzanschlussfaktor = int(szenario.split('_')[5]) / 100

    ladeleistung = {
        'NCS': int(int(szenario.split('_')[7].split('-')[0])/100 * config.leistung_ladetyp['NCS']),
        'HPC': int(int(szenario.split('_')[7].split('-')[1])/100 * config.leistung_ladetyp['HPC']),
        'MCS': int(int(szenario.split('_')[7].split('-')[2])/100 * config.leistung_ladetyp['MCS'])
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
    print(df_time)
    print(df_time['Leistung_Total'].max())
    df_time['Tag'] = df_time['Zeit'] // 1440 + 1
    df_max = df_time.groupby('Tag')['Leistung_Total'].max().reset_index()
    print(df_max)
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
    
    df_apfi_mpfi.to_csv(os.path.join(ausgabe_pfad, f'apfi_mpfi_{szenario}.csv'), sep=';', decimal=',', index=False)
    
    return None

def main():
    """
    Hauptfunktion, um alle Szenarien zu verarbeiten und Ergebnisse zu speichern.
    """
    # Bearbeite jedes Szenario in der konfigurierten Szenarienliste
    for szenario in config.list_szenarien:
        berechne_ef(szenario)
        berechne_ef_lang(szenario)
        berechne_EFI(szenario)
        berechne_MPFI_APFI(szenario)


if __name__ == "__main__":
    main()