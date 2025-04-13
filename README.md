# LKW-Schnellladenetz-Lademanagement

Dieses Repository enthält die Implementierung der Modellierung zur Analyse und Bewertung des Flexibilitätspotenzials des vom Bund ausgeschriebenen Schnellladenetzes für elektrifizierte Lkw an deutschen Autobahnen. Die Implementierung basiert auf der Masterarbeit "Potenziale eines flexibilisierten Schnellladenetzwerks für den elektrifizierten Schwerlastverkehr am deutschen Autobahnnetz" von David Sanders.

## Überblick

Die Modellierung simuliert bedarfsgerechte Ladehubs und analysiert deren Flexibilitätspotenzial. Der Prozess erfolgt in mehreren Schritten:

1. **Lkw-Daten-Generation**: Erzeugung von synthetischen Lkw-Daten mit spezifischen Ladeanforderungen basierend auf der vorbereiteten Ladenachfrage
2. **Ladehub-Dimensionierung**: Berechnung der optimalen Anzahl an Ladepunkten pro Ladetyp unter Verwendung eines Graphenmodells
3. **Optimierung der Ladevorgänge**: Optimierung von Lastprofilen für verschiedene Ladestrategien
4. **Flexibilitätsanalyse**: Berechnung und Auswertung verschiedener Flexibilitätskennzahlen
5. **Anwendungsszenarien**: Preisbasierte Optimierung anhand von Day-Ahead- und Intraday-Preisen

## Projektstruktur

Das Projekt besteht aus mehreren Modulen, die je nach gewähltem Modus ("flex" oder "epex") in unterschiedlicher Reihenfolge ausgeführt werden:

### Gemeinsame Module (für beide Modi)

- `main.py`: Steuert die Ausführung aller Module je nach gewähltem Modus
- `config.py`: Enthält Konfigurationsparameter und Szenariodefinitionen
- `ALL_zuweisung_ladetyp.py`: Erzeugt ankommende Lkw-Daten mit spezifischen Ladeanforderungen
- `ALL_konfiguration_ladehub.py`: Dimensioniert Ladehubs mittels Graphenmodell

### Module für den "flex"-Modus (Flexibilitätsanalyse)

- `FLEX_optimierung_p_min_max.py`: Implementiert die T_min- und T_max-Ladestrategien zur Flexibilitätsberechnung
- `FLEX_berechne_flex_kpis.py`: Berechnet verschiedene Flexibilitätskennzahlen (EFI, EFC, MPFI, APFI)
- `FLEX_daten_aufbereiten.py`: Bereitet die berechneten Daten für die Visualisierung auf

### Module für den "epex"-Modus (Preisoptimierung)

- `EPEX_laden_nicht_laden.py`: Identifiziert zu ladende Lkw mittels Optimierung
- `EPEX_optimierung.py`: Optimiert die Ladevorgänge anhand von Strompreisen
- `EPEX_daten_aufbereiten.py`: Bereitet die optimierten Lastgänge für die Auswertung auf

Die Module werden je nach Modus in unterschiedlicher Reihenfolge aufgerufen, wie in der `main.py` definiert:

## Anforderungen

### Systemanforderungen

- Python 3.8+
- Gurobi Optimizer 11.0+ (kommerzielle Lizenz erforderlich)
- NetworkX 3.2+
- Pandas 2.2+
- NumPy 2.0+
- Matplotlib (für Visualisierungen)

Die vollständigen Abhängigkeiten sind in `requirements.txt` definiert.

### Datensätze

Die folgenden Eingabedateien müssen im Verzeichnis `input/` vorhanden sein:

- `verteilungsfunktion_mcs-ncs.csv`: Wahrscheinlichkeitsdichtefunktionen für Ankunftszeiten der Lkw
- `ladevorgaenge_daily_cluster.csv`: Tägliche Ladevorgänge pro Cluster, Wochentag und Ladetyp (Output der Ladenachfragemodellierung)
- `dayahead_2024_5min.csv`: Day-Ahead-Preise für das Jahr 2024 in 5-Minuten-Intervallen
- `intraday_2024_5min.csv`: Intraday-Preise für das Jahr 2024 in 5-Minuten-Intervallen
- `reBAP_5min.csv`: Regelenergiepreise in 5-Minuten-Intervallen

## Modi und Ausführung

Das Modell unterstützt zwei Hauptmodi, die in der `config.py` gesetzt werden können:

- `flex`: Berechnung allgemeingültiger Flexibilitätskennzahlen und Sensitivitätsanalyse
- `epex`: Anwendungsoptimierung der Ladevorgänge basierend auf Börsenpreisen

Um die Modellierung auszuführen:

```bash
python main.py
```

### Szenario-Konfiguration

Die zu analysierenden Szenarien werden in `config.py` definiert. Die Szenarionamen folgen einem strukturierten Namensschema:

```
cl_X_quote_Y-Y-Y_netz_Z_pow_A-B-C_pause_D-E_F_G_H
```

Dabei steht:
- `X`: Cluster-ID (1, 2, 3)
- `Y-Y-Y`: Ladequoten für NCS-HPC-MCS in Prozent
- `Z`: Netzanschlusskapazität in Prozent der installierten Leistung
- `A-B-C`: Ladeleistungsfaktoren für NCS-HPC-MCS in Prozent
- `D-E`: Pausendauern für Schnellladungen und Nachtladungen in Minuten
- `F`: Ladeverhalten (M: monodirektional, B: bidirektional)
- `G_H`: Szenario-ID und Name

## Detaillierte Funktionsweise

### Gemeinsame Module (für beide Modi)

#### 1. LKW-Daten-Generation (ALL_zuweisung_ladetyp.py)

Dieses Modul generiert synthetische Lkw-Daten mit spezifischen Ladeanforderungen:

- Zufällige Generierung von Lkw-Ankunftszeiten basierend auf Verteilungsfunktionen
- Zuweisung von technischen Parametern (Batteriekapazität, maximale Ladeleistung)
- Berechnung von Anfangs-SoC basierend auf Tageszeit
- Zuweisung optimaler Ladetypen (NCS, HPC, MCS) basierend auf Ladeanforderungen

##### Konfigurationsmöglichkeiten:
- Lkw-Typverteilung: Prozentuale Verteilung der vier Lkw-Typen
- Batteriekapazitäten: 600 kWh - 960 kWh je nach Lkw-Typ
- Pausenzeiten: Standardmäßig 45 min für Schnellladungen, 540 min für Nachtladungen

#### 2. Ladehub-Dimensionierung (ALL_konfiguration_ladehub.py)

Dieses Modul bestimmt die optimale Anzahl an Ladestationen je Ladetyp:

- Erstellung eines Flussnetzwerks mit Lkw-Knoten und Zeitkanten
- Iterative Lösung des Max-Flow-Min-Cost-Problems zur Bestimmung der Mindestanzahl an Ladepunkten
- Einhaltung einer vorgegebenen Ladequote (z.B. 80%)
- Ausgabe der optimalen Dimensionierung sowie der ausgewählten Lkw

### Module für den "flex"-Modus (Flexibilitätsanalyse)

#### 3. Flexibilitätsberechnung (FLEX_optimierung_p_min_max.py)

Dieses Modul implementiert die mathematische Modellierung der T_min- und T_max-Ladestrategien:

- Formulierung und Lösung eines gemischt-ganzzahligen Optimierungsproblems mit Gurobi
- Berücksichtigung verschiedener Nebenbedingungen:
  - SoC-abhängige Ladekurven
  - Physikalische Leistungsbegrenzungen der Ladesäulen und Fahrzeuge
  - Netzanschlusskapazitäten
  - Ladeenergieanforderungen der Lkw
- Generierung zeitlich hochaufgelöster Lastverläufe für beide Strategien
- Die Optimierung erfolgt für eine charakteristische Woche mit 2304 Zeitintervallen (7 Tage × 288 Intervalle/Tag)

##### Konfigurationsmöglichkeiten:
- Bidirektionales Laden: Ein-/Ausschalten der Rückspeisefähigkeit
- Netzanschlusskapazität: Prozentsatz der kumulierten installierten Leistung

#### 4. Flexibilitätskennzahlen (FLEX_berechne_flex_kpis.py)

Berechnet verschiedene Kennzahlen zur Quantifizierung der Flexibilität:

- **Energy Flexibility Capacity (EFC)**: Kumulierte Differenz zwischen T_max und T_min
- **Energy Flexibility Index (EFI)**: Verhältnis von nicht genutzter zu potenzieller Ladeleistung
- **Minimum/Average Power Flexibility Index (MPFI/APFI)**: Leistungspuffer zu Spitzenlastzeiten bzw. im Durchschnitt
- Die EFC wird sowohl für einen einzelnen Tag (EF) als auch für eine Woche (EF_lang) berechnet

##### Konfigurationsmöglichkeiten:
- Zeitauflösung der Analyse: Standard 5 Minuten
- Aggregationsebenen: Täglich, wöchentlich, ladetyp-spezifisch

#### 5. Datenaufbereitung für Flexibilitätsanalyse (FLEX_daten_aufbereiten.py)

Bereitet die berechneten Flexibilitätskennzahlen für die Visualisierung und weitere Analyse auf:

- Generierung von wochentagsspezifischen EFC-Verläufen
- Erstellung von ladetyp-spezifischen Analysen
- Sensitivitätsbetrachtungen für verschiedene Parameter
- Szenarien-Vergleiche für Cluster, Leistungen, Pausenzeiten und Netzanschlüsse
- Die Ergebnisse werden in Excel-Tabellen exportiert, die direkt für die Berichterstellung verwendet werden können

### Module für den "epex"-Modus (Preisoptimierung)

#### 6. Ladeplanung (EPEX_laden_nicht_laden.py)

Dieses Modul identifiziert die zu ladenden Lkw für ein vollständiges Jahr:

- Durchführung einer wöchentlichen Optimierung für jede der 52 Kalenderwochen
- Maximierung der Anzahl geladener Lkw unter Berücksichtigung der verfügbaren Ladepunkte
- Erzeugung eines binären Ladestatus für jeden Lkw (0: nicht ausgewählt, 1: zum Laden ausgewählt)
- Anders als im "flex"-Modus werden hier 52 vollständige Wochen modelliert, um eine Jahresanalyse zu ermöglichen

#### 7. Preisbasierte Optimierung (EPEX_optimierung.py)

Dieses Modul optimiert die Ladevorgänge anhand von Marktpreisen:

- Wochenweise Optimierung über das gesamte Jahr (52 Wochen)
- Implementation verschiedener Ladestrategien:
  - T_min: Möglichst frühes Laden ohne Rücksicht auf Preise (Referenzstrategie)
  - Konstant: Gleichmäßiges Laden über die gesamte Standzeit (Referenzstrategie)
  - DayAhead: Preisoptimiertes Laden basierend auf Day-Ahead-Marktpreisen
  - Intraday: Preisoptimiertes Laden basierend auf Intraday-Marktpreisen
- Die Optimierung erfolgt mit 5-Minuten-Zeitintervallen und berücksichtigt mehr als 100.000 Zeitschritte für das gesamte Jahr
- Optimale Lastverschiebung unter Berücksichtigung von SoC-Restriktionen und Netzanschlusskapazitäten

#### 8. Datenaufbereitung für Preisoptimierung (EPEX_daten_aufbereiten.py)

Bereitet die optimierten Lastgänge für die Analyse auf:

- Berechnung von Kosteneinsparungen pro Woche im Vergleich zu Referenzstrategien
- Ermittlung von durchschnittlichen Kosten pro kWh und Ladetyp
- Analyse der stündlichen Kostendifferenzen zwischen Strategien
- Visualisierung der tages- und wochentagsspezifischen Kostenverläufe
- Die Ergebnisse werden in Excel-Tabellen exportiert, die eine detaillierte wirtschaftliche Bewertung ermöglichen

## Ausgabedateien

Die Modellierung erzeugt Ausgabedateien in verschiedenen Verzeichnissen:

```
data/
├── flex/
│   ├── konfiguration_ladehub/: Anzahl der Ladesäulen nach Typ
│   ├── konf_optionen/: Konfigurationsoptionen je Szenario
│   ├── lastgang/: Lastgänge der T_min und T_max Strategien
│   ├── lastgang_lkw/: Detaillierte Ladevorgänge auf LKW-Ebene
│   ├── lkws/: Generierte LKW-Daten mit Ladestatus
│   └── kpis/: Berechnete Flexibilitätskennzahlen
└── epex/
    ├── lastgang/: Optimierte Lastgänge nach Preisstrategie
    ├── lastgang_lkw/: Detaillierte preisoptimierte Ladevorgänge
    └── lkws/: Generierte LKW-Daten für EPEX-Szenarien
output/
├── results.xlsx: Aggregierte Ergebnisse der Flexibilitätsanalyse
└── results_epex_*.xlsx: Ergebnisse der Preisoptimierung je Szenario
```

## Lizenz

Dieses Projekt steht unter einer OpenSource-Lizenz. Die Modellierung basiert auf der Masterarbeit "Potenziale eines flexibilisierten Schnellladenetzwerks für den elektrifizierten Schwerlastverkehr am deutschen Autobahnnetz" von David Sanders am Institut für Energiesystemökonomik (FCN-ESE) des E.ON Energy Research Center der RWTH Aachen.

## Kontakt

Für Fragen zur Modellierung oder zur Masterarbeit wenden Sie sich an David Sanders.
