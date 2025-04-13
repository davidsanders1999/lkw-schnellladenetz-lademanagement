# ======================================================
# Benötigte Bibliotheken importieren
# ======================================================
import pandas as pd
import os
import config
import logging

# Logging konfigurieren
logging.basicConfig(filename='logs.log', level=logging.DEBUG, format='%(asctime)s; %(levelname)s; %(message)s')

# ======================================================
# Funktion: Effektive Flexibilität berechnen (EF)
# ======================================================
def berechne_ef(szenario: str):
    """Berechnet die durchschnittliche kumulative Differenz zwischen `p_max` und `p_min` für verschiedene Leistungstypen."""
    
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'lastgang')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'kpis', 'ef')
    zeit_tag = list(range(0, 1440, 5)) * 8
    
    df_lastgang = pd.read_csv(os.path.join(eingabe_pfad, f'lastgang_{szenario}.csv'), sep=';', decimal=',')
    df_kombiniert = pd.DataFrame({'Zeit_Tag': zeit_tag})
    
    for leistung in ['Leistung_Total', 'Leistung_NCS', 'Leistung_HPC', 'Leistung_MCS']:
        df_pmax = df_lastgang[df_lastgang['Ladestrategie'] == 'p_max'].groupby('Zeit')[leistung].sum() * (5 / 60)
        df_pmin = df_lastgang[df_lastgang['Ladestrategie'] == 'p_min'].groupby('Zeit')[leistung].sum() * (5 / 60)
        df_diff = (df_pmax.cumsum() - df_pmin.cumsum()).round(1).reset_index()
        df_kombiniert[leistung] = df_diff[leistung]

    df_kombiniert = df_kombiniert.groupby('Zeit_Tag').sum().reset_index()
    for col in ['Leistung_Total', 'Leistung_NCS', 'Leistung_HPC', 'Leistung_MCS']:
        df_kombiniert[col] /= 7

    os.makedirs(ausgabe_pfad, exist_ok=True)
    df_kombiniert.to_csv(os.path.join(ausgabe_pfad, f'ef_{szenario}.csv'), sep=';', decimal=',', index=False)

    print(f"✅ EF erfolgreich berechnet: {szenario}")
    logging.info(f"EF erfolgreich berechnet für Szenario: {szenario}")

# ======================================================
# Funktion: Langfristige kumulative Differenz (EF Lang)
# ======================================================
def berechne_ef_lang(szenario: str):
    """Berechnet die kumulierte Differenz (p_max - p_min) über lange Zeiträume und leitet daraus den EFC ab."""
    
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'lastgang')
    eingabe_pfad_lkw = os.path.join(basis_pfad, 'data', 'flex', 'lastgang_lkw')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'kpis', 'ef_lang')
    zeit_tag = list(range(0, 11520, 5))
    
    df_lastgang = pd.read_csv(os.path.join(eingabe_pfad, f'lastgang_{szenario}.csv'), sep=';', decimal=',')
    df_lkw = pd.read_csv(os.path.join(eingabe_pfad_lkw, f'lastgang_lkw_{szenario}.csv'), sep=';', decimal=',')
    df_kombiniert = pd.DataFrame({'Zeit_Tag': zeit_tag})

    for leistung in ['Leistung_Total', 'Leistung_NCS', 'Leistung_HPC', 'Leistung_MCS']:
        df_pmax = df_lastgang[df_lastgang['Ladestrategie'] == 'p_max'].groupby('Zeit')[leistung].sum() * (5 / 60)
        df_pmin = df_lastgang[df_lastgang['Ladestrategie'] == 'p_min'].groupby('Zeit')[leistung].sum() * (5 / 60)
        df_diff = (df_pmax.cumsum() - df_pmin.cumsum()).round(1).reset_index()
        df_kombiniert[leistung] = df_diff[leistung]

    anzahl = {
        'NCS': df_lkw[df_lkw['Ladetyp'] == 'NCS']['LKW_ID'].nunique(),
        'HPC': df_lkw[df_lkw['Ladetyp'] == 'HPC']['LKW_ID'].nunique(),
        'MCS': df_lkw[df_lkw['Ladetyp'] == 'MCS']['LKW_ID'].nunique()
    }

    efc = {
        typ: df_kombiniert[f'Leistung_{typ}'].sum() * (5 / 60) / anzahl[typ]
        for typ in ['NCS', 'HPC', 'MCS']
    }

    for typ, val in efc.items():
        print(f"EFC pro {typ} [kWh²]: {val:.2f}")
        logging.info(f"EFC pro {typ} [kWh²]: {val:.2f}")

    os.makedirs(ausgabe_pfad, exist_ok=True)
    df_kombiniert.to_csv(os.path.join(ausgabe_pfad, f'ef_lang_{szenario}.csv'), sep=';', decimal=',', index=False)

    print(f"✅ EF_Lang erfolgreich berechnet: {szenario}")
    logging.info(f"EF_Lang erfolgreich berechnet für Szenario: {szenario}")

# ======================================================
# Funktion: Energy Flexibility Index (EFI)
# ======================================================
def berechne_EFI(szenario: str):
    """Berechnet den EFI für das Szenario – gesamt & pro Ladesäulentyp."""
    
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    eingabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'lastgang_lkw')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'kpis', 'efi')
    
    df = pd.read_csv(os.path.join(eingabe_pfad, f'lastgang_lkw_{szenario}.csv'), sep=';', decimal=',')
    df = df[(df['Ladestrategie'] == 'p_max') & df['Max_Leistung'].notna()]

    def berechne_efi(df_typ):
        E_pot = df_typ['Max_Leistung'].sum() * (5 / 60)
        E_ch = df_typ['Leistung'].sum() * (5 / 60)
        return 1 - E_ch / E_pot if E_pot > 0 else 0

    df_efi = pd.DataFrame({
        'Szenario': [szenario],
        'EFI': [berechne_efi(df)],
        'EFI_NCS': [berechne_efi(df[df['Ladetyp'] == 'NCS'])],
        'EFI_HPC': [berechne_efi(df[df['Ladetyp'] == 'HPC'])],
        'EFI_MCS': [berechne_efi(df[df['Ladetyp'] == 'MCS'])],
    })

    for col in ['EFI', 'EFI_NCS', 'EFI_HPC', 'EFI_MCS']:
        print(f"{col}: {df_efi[col].iloc[0]:.3f}")
        logging.info(f"{col} für {szenario}: {df_efi[col].iloc[0]:.3f}")

    os.makedirs(ausgabe_pfad, exist_ok=True)
    df_efi.to_csv(os.path.join(ausgabe_pfad, f'efi_{szenario}.csv'), sep=';', decimal=',', index=False)

    print(f"✅ EFI erfolgreich berechnet: {szenario}")
    logging.info(f"EFI erfolgreich berechnet für Szenario: {szenario}")

# ======================================================
# Funktion: MPFI & APFI berechnen
# ======================================================
def berechne_MPFI_APFI(szenario: str):
    """Berechnet MPFI & APFI zur Bewertung der Netzanschlussausnutzung."""
    
    basis_pfad = os.path.dirname(os.path.abspath(__file__))
    pfad_ladehub = os.path.join(basis_pfad, 'data', 'flex','konfiguration_ladehub')
    pfad_lastgang = os.path.join(basis_pfad, 'data', 'flex', 'lastgang')
    ausgabe_pfad = os.path.join(basis_pfad, 'data', 'flex', 'kpis', 'apfi_mpfi')

    base_case = 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base'

    ladehub_datei = (
        f'anzahl_ladesaeulen_{base_case}.csv'
        if all(x in szenario for x in base_case.split('_')[1:4])
        else f'anzahl_ladesaeulen_{szenario}.csv'
    )

    df_ladehub = pd.read_csv(os.path.join(pfad_ladehub, ladehub_datei), sep=';', decimal=',')
    df_lastgang = pd.read_csv(os.path.join(pfad_lastgang, f'lastgang_{szenario}.csv'), sep=';', decimal=',')
    df_lastgang = df_lastgang[df_lastgang['Ladestrategie'] == 'p_max']

    faktor = int(szenario.split('_')[5]) / 100
    leistung = {k: int(config.leistung_ladetyp[k]) for k in ['NCS', 'HPC', 'MCS']}
    max_saeulen = {k: int(df_ladehub[k][0]) for k in ['NCS', 'HPC', 'MCS']}

    netzanschluss = faktor * sum(leistung[t] * max_saeulen[t] for t in leistung)

    df_time = df_lastgang.groupby('Zeit')['Leistung_Total'].sum().reset_index()
    df_time['Tag'] = df_time['Zeit'] // 1440 + 1
    p_max = df_time.groupby('Tag')['Leistung_Total'].max().mean()
    p_avg = df_lastgang[df_lastgang['Leistung_Max_Total'] != 0].groupby('Zeit')['Leistung_Total'].sum().mean()

    df_result = pd.DataFrame({
        'Szenario': [szenario],
        'MPFI': [1 - p_max / netzanschluss],
        'APFI': [1 - p_avg / netzanschluss]
    })

    print(f"MPFI: {df_result['MPFI'].iloc[0]:.3f}")
    print(f"APFI: {df_result['APFI'].iloc[0]:.3f}")
    logging.info(f"MPFI/APFI berechnet für {szenario}: MPFI={df_result['MPFI'].iloc[0]:.3f}, APFI={df_result['APFI'].iloc[0]:.3f}")

    os.makedirs(ausgabe_pfad, exist_ok=True)
    df_result.to_csv(os.path.join(ausgabe_pfad, f'apfi_mpfi_{szenario}.csv'), sep=';', decimal=',', index=False)

# ======================================================
# Hauptfunktion zur Szenarioverarbeitung
# ======================================================
def main():
    """Startet die Berechnung aller Flexibilitätskennzahlen für alle Szenarien."""
    logging.info('Starte Flex KPI Berechnungen')
    print("Flex KPI Berechnung gestartet")

    for szenario in config.list_szenarien:
        logging.info(f"Szenario: {szenario}")
        print(f"▶️ Verarbeite Szenario: {szenario}")
        berechne_ef(szenario)
        berechne_ef_lang(szenario)
        berechne_EFI(szenario)
        berechne_MPFI_APFI(szenario)

    print("✅ Alle Szenarien erfolgreich verarbeitet.")
    logging.info("✅ Alle Szenarien abgeschlossen.")

# ======================================================
# Ausführung
# ======================================================
if __name__ == "__main__":
    main()
