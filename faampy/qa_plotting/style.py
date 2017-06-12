# See:
# http://matplotlib.org/users/customizing.html

import matplotlib as mpl

from cycler import cycler

rcParams=mpl.rcParams

#to get the complete list of settings type
#print(plt.rcParams)

#mpl.rcParams=mpl.rcParamsDefault
#plt.style.use('bmh')
#plt.style.use('seaborn-pastel')

#sets standard way to plot axes titles.
axes_title_style = {'fontweight' : 'bold',
                    'verticalalignment' : 'top',
                    'horizontalalignment' : 'left'}


# general settings that apply to everything
rcParams['lines.linewidth'] = 1.2

# colour cycle
#rcParams['axes.color_cycle'] = [u'#33adff',    #blue
rcParams['axes.prop_cycle'] = cycler('color', [u'#33adff',    # blue
                                               u'#ffaf4d',    # orange
                                               u'#ff4d4d',    # red
                                               u'#9acd32',    # green
                                               u'#c284e1',    # purple
                                               u'#d57676',    # darker red
                                               u'#00b3b3',    # teal
                                               u'#d279a6',    # pink
                                               u'#4dffc3',    # green
                                               u'#7070db'])   # bluey purple

#grid options
rcParams['axes.grid'] = True                # shows grid
rcParams['grid.color'] = 'LightSlateGrey'   # light grey colour for grid lines

# legend options
rcParams['legend.fontsize'] = 'small'
rcParams['legend.fancybox'] = True

##figure options
rcParams['figure.facecolor'] = 'w'


##CHOOSE: which version you want - pdf, presentation or screen output:
#output_device = 'screen'
#output_device = 'presentation'
output_device = 'pdf'


if output_device == 'screen':
     #add some layout settings here
    rcParams['axes.facecolor'] = '#f2f2f2'
    rcParams['axes.edgecolor'] = 'k'
    #mpl.rcParams['legend.facecolor'] = '#f2f2f2'
elif output_device == 'pdf':
     #add some pdf specific layout settings here
    rcParams['axes.edgecolor'] = 'k'
elif output_device == 'presentation':
    rcParams['lines.linewidth'] = 2.5
    rcParams['axes.labelsize'] = 'large'
    rcParams['legend.fontsize'] = 'medium'
    rcParams['font.size'] = 14.0
    rcParams['xtick.labelsize'] = 'large'
    rcParams['ytick.labelsize'] = 'large'
else:
    pass

