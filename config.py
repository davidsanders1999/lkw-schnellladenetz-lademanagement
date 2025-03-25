
mode = 'flex' # 'flex' or 'epex'

leistung_ladetyp = {
    'NCS': 100,
    'HPC': 350,
    'MCS': 1000
}

# ======================================================
list_szenarien = [
# 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_1_Base', # Base

'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_B_2_Bidirektional', # Bidirektional 

# 'cl_1_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_3_Cluster-1', # Cluster 
# 'cl_3_quote_80-80-80_netz_100_pow_100-100-100_pause_45-540_M_4_Cluster-3',

# 'cl_2_quote_80-80-80_netz_100_pow_110-100-100_pause_45-540_M_5_Leistung-NCS-110',
# 'cl_2_quote_80-80-80_netz_100_pow_120-100-100_pause_45-540_M_6_Leistung-NCS-120',
# 'cl_2_quote_80-80-80_netz_100_pow_130-100-100_pause_45-540_M_7_Leistung-NCS-130', # Leistung NCS
# 'cl_2_quote_80-80-80_netz_100_pow_140-100-100_pause_45-540_M_8_Leistung-NCS-140', 

# 'cl_2_quote_80-80-80_netz_100_pow_100-110-100_pause_45-540_M_9_Leistung-HPC-110',
# 'cl_2_quote_80-80-80_netz_100_pow_100-120-100_pause_45-540_M_10_Leistung-HPC-120',
# 'cl_2_quote_80-80-80_netz_100_pow_100-130-100_pause_45-540_M_11_Leistung-HPC-130', # Leistung HPC
# 'cl_2_quote_80-80-80_netz_100_pow_100-140-100_pause_45-540_M_12_Leistung-HPC-140',

# 'cl_2_quote_80-80-80_netz_100_pow-110_100-100-110_pause_45-540_M_13_Leistung-MCS-110',
# 'cl_2_quote_80-80-80_netz_100_pow-120_100-100-120_pause_45-540_M_14_Leistung-MCS-120',
# 'cl_2_quote_80-80-80_netz_100_pow-130_100-100-130_pause_45-540_M_15_Leistung-MCS-130', # Leistung MCS
# 'cl_2_quote_80-80-80_netz_100_pow-140_100-100-140_pause_45-540_M_16_Leistung-MCS-140',

# 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_50-540_M_17_Schnellzeit-110', # Pausenzeiten
# 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_55-540_M_18_Schnellzeit-120',
# 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_60-540_M_19_Schnellzeit-130',
# 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_65-540_M_20_Schnellzeit-140',

# 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-595_M_21_Nachtzeit-110',
# 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-650_M_22_Nachtzeit-120', 
# 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-705_M_23_Nachtzeit-130', 
# 'cl_2_quote_80-80-80_netz_100_pow_100-100-100_pause_45-760_M_24_Nachtzeit-140', 

# 'cl_2_quote_80-80-80_netz_90_pow_100-100-100_pause_45-540_M_25_Netzanschluss-90',
# 'cl_2_quote_80-80-80_netz_80_pow_100-100-100_pause_45-540_M_26_Netzanschluss-80', 
# 'cl_2_quote_80-80-80_netz_70_pow_100-100-100_pause_45-540_M_27_Netzanschluss-70', # Netzanschluss
# 'cl_2_quote_80-80-80_netz_60_pow_100-100-100_pause_45-540_M_28_Netzanschluss-60', 
# 'cl_2_quote_80-80-80_netz_50_pow_100-100-100_pause_45-540_M_29_Netzanschluss-50',
# 'cl_2_quote_80-80-80_netz_40_pow_100-100-100_pause_45-540_M_30_Netzanschluss-40',
# 'cl_2_quote_80-80-80_netz_30_pow_100-100-100_pause_45-540_M_31_Netzanschluss-30',
# 'cl_2_quote_80-80-80_netz_20_pow_100-100-100_pause_45-540_M_32_Netzanschluss-20',
# 'cl_2_quote_80-80-80_netz_10_pow_100-100-100_pause_45-540_M_33_Netzanschluss-10',
]

if __name__ == '__main__':
    for szenario in list_szenarien:
        print(szenario)