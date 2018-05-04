"""

Find the names of the principal investigators for the FAAM campaigns

"""

campaigns = ['ACAS', 'ACCACIA', 'ACEMED', 'ADIENT', 'ADRIEX', 'AEGEAN-GAME', 'AETIAQ', 'AMMA', 'AMPEP', 'APPRAISE',
             'AQUM', 'AUTEX', 'BBR', 'BORTAS', 'BUNCE', 'CAESAR', 'CALI', 'CAP-2009', 'CAP-2010', 'CAPEX', 'CASCADE',
             'CAVIAR', 'CIMS', 'CIRRUS', 'CLOPAP', 'CLPX', 'COALESC', 'CONSTRAIN', 'CONTRAILS', 'COPS', 'COSIC',
             'COVEX', 'DABEX', 'DIAMET', 'DODO', 'EAQUATE', 'EM25', 'ESA', 'EXMIX', 'FENNEC', 'FLUXEX', 'GERBIL',
             'GFDEX', 'IASI/JAIVEX', 'ICEPIC', 'ISMAR', 'ITOP', 'LAND-EMISS', 'MARVAL', 'MEVALI', 'MEVEX', 'MICROMIX',
             'MIXED', 'MacCloud', 'NCAS', 'NEON', 'NU-WAVE', 'OMEGA', 'OP3', 'PIK', 'POSE', 'QUEFA', 'RAINCLOUDS',
             'RICO', 'RONOCO', 'SAVEX', 'SEPTEX', 'SONATA', 'T-NAWDEX', 'T-REX', 'THAW', 'TOFAMS', 'TROMPEX', 'VACAR',
             'VIROSS', 'VISURB', 'VOCALS', 'VOLCANIC', 'WINTEX']



f = open('/home/axel/pi_list.txt', 'r')
lines = f.readlines()
f.close()
email = []
for line in lines:
    tmp = line.strip().split(';')
    for i in tmp:
        if '@' in i:
            email.append(i.split('#')[1].strip())
email=set(email)
print(';'.join(email))






