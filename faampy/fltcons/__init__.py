import os

__version__ = '0.3'
__author__ = 'axll[at]faam[dot]ac[dot]uk'

DB_NAME = os.path.join(os.environ['HOME'], '.faampy', 'dbs', 'fltcons.sqlite')
FIGURES_PATH = os.path.join(os.environ['HOME'], '.faampy', 'figures', 'fltcons')

# Setting for web service
#FIGURES_PATH = '/home/htdocs.dacru/figures/fltcons/'
FIGURES_URL = '/'

PARAMETERS = ['TASCORR', 'CALCABT', 'GELIMS',  'CALGE',   'PRTCCAL',
              'HEIMCAL', 'INSLEVL', 'CALLWC',  'CALNPRS', 'CALNTMP',
              'CALNBTS', 'CALNGTS', 'CALNRTS', 'CALNBBS', 'CALNGBS',
              'CALNRBS', 'CALNHUM', 'CALNSTS', 'CALNVLW', 'CALNVLR',
              'CALNVLC', 'CALNVTW', 'CALNVTR', 'CALNVTC', 'CALRSL',
              'CALRST',  'CALO3',   'CALO3P',  'CALO3T',  'CALO3F',
              'CALO3MX', 'CALNO',   'CALNO2',  'CALNOX',  'CALNOMX',
              'CALSO2',  'CALCOMR', 'CALCOMX', 'CALCABP', 'CALS9SP',
              'CALPLIN', 'CALPLOG', 'CALUP1S', 'CALUP2S', 'CALUIRS',
              'CALLP1S', 'CALLP2S', 'CALLIRS', 'CALCUCF', 'CALCURF',
              'CALCUIF', 'CALCLCF', 'CALCLRF', 'CALCLIF', 'TRFCTR',
              'CALDIT',  'CALNDT',  'CALTP1',  'CALTP2',  'CALTP3',
              'CALTP4',  'CALTP5',  'AOA_A0',  'AOA_A1',  'AOSS_B0',
              'AOSS_B1', 'TOLER',   'TASCOR1', 'ALPH0',   'ALPH1',
              'BET0',    'BET1',    'CALTNOS', 'CALTSAM', 'CALTAMB',
              'CALTSRC', 'CALHTR1', 'CALHTR2', 'CALISRC', 'INSPOSN',
              'BUCK']
