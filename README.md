# LKW-Schnellladenetz-Lademanagement

> Dieses Repository enthält die Implementierung der Modellierung zur Analyse und Bewertung des Flexibilitätspotenzials des vom Bund ausgeschriebenen Schnellladenetzes für elektrifizierte LKW an deutschen Autobahnen. Die Implementierung basiert auf der Masterarbeit "Potenziale eines flexibilisierten Schnellladenetzwerks für den elektrifizierten Schwerlastverkehr am deutschen Autobahnnetz" von David Sanders.

## Überblick

Die Modellierung simuliert bedarfsgerechte Ladehubs und analysiert deren Flexibilitätspotenzial. Der Prozess erfolgt in mehreren Schritten:

1. **LKW-Daten-Generation**: Erzeugung von synthetischen LKW-Daten mit spezifischen Ladeanforderungen basierend auf der vorbereiteten Ladenachfrage
2. **Ladehub-Dimensionierung**: Berechnung der optimalen Anzahl an Ladepunkten pro Ladetyp unter Verwendung eines Graphenmodells
3. **Flexibilitätsanalyse**: Berechnung und Auswertung verschiedener Flexibilitätskennzahlen
4. **Anwendungsszenarien**: Preisbasierte Optimierung anhand von Day-Ahead- und Intraday-Preisen

## Projektstruktur

Das Projekt besteht aus mehreren Modulen, die je nach gewähltem Modus ("flex" oder "epex") in unterschiedlicher Reihenfolge ausgeführt werden:

### Gemeinsame Module (für beide Modi)

- `main.py`: Steuert die Ausführung aller Module je nach gewähltem Modus
- `config.py`: Enthält Konfigurationsparameter und Szenariodefinitionen
- `ALL_zuweisung_ladetyp.py`: Erzeugt ankommende LKW-Daten mit spezifischen Ladeanforderungen
- `ALL_konfiguration_ladehub.py`: Dimensioniert Ladehubs mittels Graphenmodell

### Module für den "flex"-Modus (Flexibilitätsanalyse)

- `FLEX_optimierung_p_min_max.py`: Implementiert die T_min- und T_max-Ladestrategien zur Flexibilitätsberechnung
- `FLEX_berechne_flex_kpis.py`: Berechnet verschiedene Flexibilitätskennzahlen (EFI, EFC, MPFI, APFI)
- `FLEX_daten_aufbereiten.py`: Bereitet die berechneten Daten für die Auswertung auf

### Module für den "epex"-Modus (Preisoptimierung)

- `EPEX_laden_nicht_laden.py`: Identifiziert zu ladende LKW mittels Optimierung
- `EPEX_optimierung.py`: Optimiert die Ladevorgänge anhand von Strompreisen
- `EPEX_daten_aufbereiten.py`: Bereitet die optimierten Lastgänge für die Auswertung auf

## Anforderungen

### Systemanforderungen

- Python 3.8+
- Gurobi Optimizer 11.0+ (kommerzielle Lizenz erforderlich)
- NetworkX 3.2+
- Pandas 2.2+
- NumPy 2.0+
- Matplotlib

Die vollständigen Abhängigkeiten sind in `requirements.txt` definiert.

### Datensätze

Die folgenden Eingabedateien müssen im Verzeichnis `input/` vorhanden sein:

- `ladevorgaenge_daily_cluster.csv`

Tägliche Ladevorgänge pro Cluster, Wochentag und Ladetyp (Output der Ladenachfragemodellierung) [LINK](https://github.com/davidsanders1999/LKW-schnellladenetz-ladenachfrage)

- `verteilungsfunktion_mcs-ncs.csv`

Wahrscheinlichkeitsdichtefunktionen für Ankunftszeiten der LKW nach Burges und Kippelt [LINK](https://www.transportenvironment.org/uploads/files/2022_01_TE_grid_integration_long_haul_truck_charging_study_final.pdf) 


- `dayahead_2024_5min.csv`

Day-Ahead-Preise für das Jahr 2024 in 5-Minuten-Intervallen extrapoliert [LINK](https://www.netztransparenz.de/de-de/Erneuerbare-Energien-und-Umlagen/EEG/Transparenzanforderungen/Marktpr%C3%A4mie/Spotmarktpreis-nach-3-Nr-42a-EEG)


- `intraday_2024_5min.csv`

Intraday-Preise für das Jahr 2024 in 5-Minuten-Intervallen extrapoliert [LINK](https://www.netztransparenz.de/en/Balancing-Capacity/Imbalance-price/IP-Index)


## Modi und Ausführung

Das Modell unterstützt zwei Hauptmodi, die in der `config.py` gewählt werden können:

- `flex`: Berechnung allgemeingültiger Flexibilitätskennzahlen und Sensitivitätsanalyse
- `epex`: Anwendungsoptimierung der Ladevorgänge basierend auf Börsenpreisen

Um die Modellierung auszuführen:

```bash
python main.py
```

### Szenario-Konfiguration

Die zu analysierenden Szenarien werden in `config.py` definiert und bestimmen die Inputwerte der Modellierungsmodule. Die Szenarionamen folgen einem strukturierten Namensschema:

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

#### 1. LKW-Daten-Generation `ALL_zuweisung_ladetyp.py`

Dieses Modul generiert synthetische LKW-Daten mit spezifischen Ladeanforderungen:

- Zufällige Generierung von LKW-Ankunftszeiten basierend auf Verteilungsfunktionen
- Zuweisung von technischen Parametern (Batteriekapazität, maximale Ladeleistung)
- Berechnung von Anfangs-SoC basierend auf Tageszeit
- Zuweisung optimaler Ladetypen (NCS, HPC, MCS) basierend auf Ladeanforderungen

##### Konfigurationsmöglichkeiten:
- LKW-Typverteilung: Prozentuale Verteilung der vier LKW-Typen
- Batteriekapazitäten: 600 kWh - 960 kWh je nach LKW-Typ

#### 2. Ladehub-Dimensionierung `ALL_konfiguration_ladehub.py`

Dieses Modul bestimmt die optimale Anzahl an Ladestationen je Ladetyp:

- Erstellung eines Flussnetzwerks mit LKW-Knoten und Zeitkanten
- Iterative Lösung des Max-Flow-Min-Cost-Problems zur Bestimmung der Mindestanzahl an Ladepunkten
- Einhaltung einer vorgegebenen Ladequote (z.B. 80%)
- Ausgabe der optimalen Dimensionierung sowie der ausgewählten LKW

### Module für den "flex"-Modus (Flexibilitätsanalyse)

#### 3. Flexibilitätsberechnung `FLEX_optimierung_p_min_max.py`

Dieses Modul implementiert die Modellierung der T_min- und T_max-Ladestrategien:

- Formulierung und Lösung eines gemischt-ganzzahligen Optimierungsproblems mit Gurobi
- Berücksichtigung verschiedener Nebenbedingungen:
  - SoC-abhängige Ladekurven
  - Physikalische Leistungsbegrenzungen der Ladesäulen und Fahrzeuge
  - Netzanschlusskapazitäten
  - Ladeenergieanforderungen der LKW
- Generierung zeitlich hochaufgelöster Lastverläufe für beide Strategien

#### 4. Flexibilitätskennzahlen `FLEX_berechne_flex_kpis.py`

Berechnet verschiedene Kennzahlen zur Quantifizierung der Flexibilität:

- **Energy Flexibility Capacity (EFC)**: Kumulierte Differenz zwischen T_max und T_min
- **Energy Flexibility Index (EFI)**: Verhältnis von nicht genutzter zu potenzieller Ladeleistung
- **Minimum/Average Power Flexibility Index (MPFI/APFI)**: Leistungspuffer zu Spitzenlastzeiten bzw. im Durchschnitt

#### 5. Datenaufbereitung für Flexibilitätsanalyse `FLEX_daten_aufbereiten.py`

Dieses Modul dienet der Ergebnisaufbereitung:


- Bereitet die berechneten Flexibilitätskennzahlen für die Visualisierung und weitere Analysen auf
- Die Ergebnisse werden in Excel-Tabellen exportiert

### Module für den "epex"-Modus (Preisoptimierung)

#### 6. Ladeplanung `EPEX_laden_nicht_laden.py`

Dieses Modul identifiziert die zu ladenden LKW für ein vollständiges Jahr:

- Durchführung einer wöchentlichen Optimierung für jede der 52 Kalenderwochen
- Maximierung der Anzahl geladener LKW unter Berücksichtigung der verfügbaren Ladepunkte
- Erzeugung eines binären Ladestatus für jeden LKW (0: nicht ausgewählt, 1: zum Laden ausgewählt)
- Anders als im "flex"-Modus werden hier 52 vollständige Wochen modelliert, um eine Jahresanalyse zu ermöglichen

#### 7. Preisbasierte Optimierung `EPEX_optimierung.py`

Dieses Modul optimiert die Ladevorgänge anhand von Marktpreisen:

- Wochenweise Optimierung über das gesamte Jahr (52 Wochen)
- Implementierung verschiedener Ladestrategien:
  - T_min: Möglichst frühes Laden ohne Rücksicht auf Preise (1. Referenzstrategie)
  - Konstant: Gleichmäßiges Laden über die gesamte Standzeit (2. Referenzstrategie)
  - DayAhead: Preisoptimiertes Laden basierend auf Day-Ahead-Marktpreisen
  - Intraday: Preisoptimiertes Laden basierend auf Intraday-Marktpreisen

#### 8. Datenaufbereitung für Preisoptimierung `EPEX_daten_aufbereiten.py`

Dieses Modul dienet der Ergebnisaufbereitung:

- Bereitet die optimierten Lastgänge für die Analyse auf
- Die Ergebnisse werden in Excel-Tabellen exportiert, die eine detaillierte wirtschaftliche Bewertung ermöglichen

## Ausgabedateien

Die Modellierung erzeugt Ausgabedateien in verschiedenen Verzeichnissen:

```
data/
├── flex/
│   ├── konfiguration_ladehub/: Anzahl der Ladesäulen nach Typ
│   ├── konf_optionen/: Konfigurationsoptionen je Szenario
│   ├── lastgang/: Lastgänge der T_min und T_max Strategien
│   ├── lastgang_LKW/: Detaillierte Ladevorgänge auf LKW-Ebene
│   ├── LKWs/: Generierte LKW-Daten mit Ladestatus
│   └── kpis/: Berechnete Flexibilitätskennzahlen
└── epex/
    ├── lastgang/: Optimierte Lastgänge nach Preisstrategie
    ├── lastgang_LKW/: Detaillierte preisoptimierte Ladevorgänge
    └── LKWs/: Generierte LKW-Daten für EPEX-Szenarien
output/
├── results.xlsx: Aggregierte Ergebnisse der Flexibilitätsanalyse
└── results_epex_*.xlsx: Ergebnisse der Preisoptimierung je Szenario
```

## Lizenz

Dieses Projekt steht unter einer OpenSource-Lizenz. Die Modellierung basiert auf der Masterarbeit "Potenziale eines flexibilisierten Schnellladenetzwerks für den elektrifizierten Schwerlastverkehr am deutschen Autobahnnetz" von David Sanders am Institut für Energiesystemökonomik (FCN-ESE) des E.ON Energy Research Center der RWTH Aachen.


## Kontakt

Für Fragen zur Modellierung oder zur Masterarbeit wenden Sie sich an David Sanders.
