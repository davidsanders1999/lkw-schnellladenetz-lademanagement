import config
import time
import FLEX_konfiguration_ladehub
import FLEX_optimierung_p_min_max
import ALL_zuweisung_ladetyp
import ALL_berechne_flex_kpis
import FLEX_daten_aufbereiten
import EPEX_laden_nicht_laden
import EPEX_optimierung
import EPEX_daten_aufbereiten
import clear_data 
import logging
logging.basicConfig(filename='logs.log', level=logging.DEBUG, format='%(asctime)s; %(levelname)s; %(message)s')

time_start = time.time() # Simulation aller Szenarien 27 min
logging.info('Start: Main')


if config.mode == 'flex':
    # clear_data.main()
    # zuweisung_ladetyp.main()
    # FLEX_konfiguration_ladehub.main()
    FLEX_optimierung_p_min_max.main()
    # berechne_flex_kpis.main()
    # FLEX_daten_aufbereiten.main()
    
elif config.mode == 'epex':
    # zuweisung_ladetyp.main()
    # FLEX_konfiguration_ladehub.main()
    EPEX_laden_nicht_laden.main()
    EPEX_optimierung.main()
    EPEX_daten_aufbereiten.main()
    
    

time_end = time.time()
print(f'Laufzeit: {time_end - time_start} Sekunden')