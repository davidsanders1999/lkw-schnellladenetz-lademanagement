import time
import konfiguration_ladehub
import optimierung_p_min_max
import zuweisung_ladetyp
import berechne_flex_kpis
import daten_aufbereiten
import clear_data 

time_start = time.time()

# clear_data.main()
zuweisung_ladetyp.main()
konfiguration_ladehub.main()
optimierung_p_min_max.main()
berechne_flex_kpis.main()
daten_aufbereiten.main()

time_end = time.time()
print(f'Laufzeit: {time_end - time_start} Sekunden')

#Test

# Maximale Laufzeit: 