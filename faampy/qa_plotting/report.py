#!/usr/bin/python

"""
Quality Assurance-Quality Check (QA-QC) report. This report is useful to
specialised users of the FAAM BAe 146 aircraft; especially the FAAM team and
project/campaigns PIs.

It summarises the core instruments used on each flight and provides a first
quick look at the data from an individual flight. Instrument issues might be
spotted in those plots.

"""


import datetime

import matplotlib as mpl
mpl.use('Agg')  # Not to use X server
import matplotlib.pyplot as plt
import netCDF4
import tempfile
import os
import shutil
import sys


import temperature
import bbr
import buck
import cabin_pressure
import co
import cpc
import flags
import humidity
import nephelometer
import nevzorov
import ozone
import psap
import so2
import static_pressure
import turbulence
import twc

from utils import get_fid
from style import *
from tcp_data_file import tcp_file_checker

TEX_PREAMBLE = r"""\documentclass{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[a4paper,left=1cm,right=1cm,top=2.0cm]{geometry}
\usepackage{fancyhdr}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{rotating}
\usepackage{longtable}
\pagestyle{fancy}
\pagenumbering{gobble}
\lhead{FAAM QA{-}QC Report}
\rhead{\thepage}
\renewcommand{\familydefault}{\sfdefault}
\newcommand\Tstrut{\rule{0pt}{2.6ex}}       % "top" strut
\newcommand\Bstrut{\rule[-0.9ex]{0pt}{0pt}} % "bottom" strut
\newcommand{\TBstrut}{\Tstrut\Bstrut}
\begin{document}
"""

TEX_TITLEPAGE = r"""\begin{titlepage}
    \centering
    \vspace*{3.0cm}
    {\color{blue} \Huge \textsf{\textbf{\textit{FAAM}}}\par}
    \vspace{1.4cm}
    {\huge\textsf{\textbf{Qa-Qc Data Report}}\par}
    \vspace{0.6cm}
    {\large %s\par}
    \vfill
    {\large created\par}
    {\large \today\par}
\end{titlepage}
"""


TEX_FIGURE = r"""\begin{figure}[htbp]
\centering
\includegraphics[angle=%i, width=1\textwidth]{%s}
\end{figure}
"""

TEX_FINAL=r"\end{document}"


def create_titlepage(fid, datestring):
    """
    This functions creates the title page for the QA-QC report

    """
    doc = TEX_TITLEPAGE % ('%s - %s' % (fid, datestring))
    return doc


def create_preamble():
    """
    This function creates the style/layout of how the QA-QC report should look

    """
    doc = TEX_PREAMBLE
    return doc


def create_figure(ds, instr):
    """
    This function creates the QA-QC report by looking in the individual modules
    (e.g. temperature, nevzorov, bbr, buck, nephelometer, psap, cabin_pressure, co,
    humidity, twc, static_pressure, turbulence)

    """
    doc=''

    sys.stdout.write('Working on %s ...\n' % (instr.__name__,))
    fig = instr.main(ds)
    plt.pause(0.25)
    imgfilename = tempfile.mktemp(suffix='.png')
    fig.savefig(imgfilename, dpi=300)
    if fig.orientation == 'landscape':
        angle = 90
    else:
        angle = 0
    doc += '\n'
    doc += TEX_FIGURE % (angle, imgfilename)
    doc += r'\clearpage'
    doc += '\n'
    sys.stdout.write('Success ...\n')
    return doc


def flag_table(ds):
    """
    Creates flag table to be included in the report.

    """
    flag_array = flags.get_flag_data(ds)
    doc = ''
    doc += r'\section*{Parameter Flag Overiew}'
    doc += r"""\begin{longtable}{|l|c|c|c|c|c|c|}
    \hline
    \textbf{Variable} & \textbf{Percentage} & \textbf{Percentage}  & \textbf{Percentage}   & \textbf{Percentage}  & \textbf{Percentage}   & \textbf{Percentage} \\
    \textbf{Name}     & \textbf{Flag -1}    & \textbf{Flag 0}      & \textbf{Flag 1}       & \textbf{Flag 2}      & \textbf{Flag 3}       & \textbf{Flag na}    \\
    \hline
    \hline
    \endfirsthead
    \multicolumn{7}{c}%
    {\textit{Continued from previous page}} \\
    \hline
    \textbf{Variable} & \textbf{Percentage} & \textbf{Percentage}  & \textbf{Percentage}   & \textbf{Percentage}  & \textbf{Percentage}   & \textbf{Percentage} \\
    \textbf{Name}     & \textbf{Flag -1}    & \textbf{Flag 0}      & \textbf{Flag 1}       & \textbf{Flag 2}      & \textbf{Flag 3}       & \textbf{Flag na}    \\
    \hline
    \hline
    \endhead
    \hline \multicolumn{7}{r}{\textit{Continued on next page}} \\
    \endfoot
    \hline
    \endlastfoot
    """
    for line in flag_array:
        l = ' & '.join([line[0],]+['%.1f' % i for i in line[1:]]) + r' \\'
        l = l.replace('_', '\_')
        doc += l
        doc += '\n'

    doc += r"\end{longtable}"
    doc += "\n"
    doc += r"\clearpage"
    return doc


def file_table(core_rawdlu_zip):
    """
    Creates file table to be included in the report.

    """
    doc = ''
    doc += r'\section*{TCP Data File Summary}'
    doc += '\n'
    doc += r"""\begin{longtable}{|l|l|r|r|r|r|r|r|}
    \hline
    \textbf{File name} & \textbf{Data Start}  & \textbf{Dur} & \textbf{\#}        & \textbf{Unique}     & \textbf{PTP}  & \textbf{Comple-} & \textbf{Packet} \\
    \textbf{}          & \textbf{Data End}    & \textbf{}    & \textbf{packets}   & \textbf{Times}      & \textbf{sync} & \textbf{teness}  & \textbf{Sizes} \\
    \hline
    \hline
    \endfirsthead
    \multicolumn{8}{c}%
    {\textit{Continued from previous page}} \\
    \hline
    \textbf{File name} & \textbf{Data Start}  & \textbf{Dur} & \textbf{\#}        & \textbf{Unique}     & \textbf{PTP}  & \textbf{Comple-} & \textbf{Packet} \\
    \textbf{}          & \textbf{Data End}    & \textbf{}    & \textbf{packets}   & \textbf{Times}      & \textbf{sync} & \textbf{teness}  & \textbf{Sizes} \\
    \hline
    \hline
    \endhead
    \hline \multicolumn{7}{r}{\textit{Continued on next page}} \\
    \endfoot
    \hline
    \endlastfoot
    """

    table=tcp_file_checker(core_rawdlu_zip)
    for line in table:
        line[-1] = '\Tstrut'+r' \\ '.join(['%i: {%5.1f}' % (l[0], l[1]) for l in line[-1]])
        l = r'%s & \shortstack{%s\Tstrut\\%s\Bstrut} & %i & %i & %i & %i & %.1f & \shortstack{%s}\\' % tuple(line)
        l = l.replace('_', '\_')
        doc += l
        doc += '\n'
        doc += r'\hline'
        doc += '\n'

    doc += r'\hline'
    doc += '\n'
    doc += r'\end{longtable}'
    doc += '\n'
    doc += r'\clearpage'
    doc += '\n'
    return doc


def process(decades_dataset=None, core_rawdlu_zip=None, ncfilename=None, outpath=None):
    if outpath:
        if not os.path.exists(outpath):
            sys.stdout.write('Output path does not exist ...\nLeaving ...\n')
        else:
            outpath = outpath
    else:
        outpath = os.path.expanduser('~')

    if ncfilename:
        if os.path.exists(ncfilename):
            nc_dataset = netCDF4.Dataset(ncfilename, 'r')

    if decades_dataset:
        fid = decades_dataset['FLIGHT'].data
        date = datetime.datetime(decades_dataset['DATE'][2],
                                 decades_dataset['DATE'][1],
                                 decades_dataset['DATE'][0])
        datestring = date.strftime('%Y-%m-%d')
        ds = decades_dataset
    elif nc_dataset:
        fid = get_fid(nc_dataset)
        date = datetime.datetime(int(nc_dataset.Data_Date[0:4]),
                                 int(nc_dataset.Data_Date[4:6]),
                                 int(nc_dataset.Data_Date[6:8]))
        datestring = date.strftime('%Y-%m-%d')
        ds = nc_dataset

    doc = ''
    doc += create_preamble()
    doc += create_titlepage(fid, datestring)
    for instr in [temperature, nevzorov, bbr, buck, nephelometer, cpc, psap,
                  cabin_pressure, co, ozone, so2, static_pressure,
                  humidity, twc, turbulence]:
        figure_success = False
        if instr.__name__.split('.')[-1] == 'turbulence':
            try:
                doc += create_figure(nc_dataset, instr)
                figure_success = True
            except:
                plt.close()
                continue
        else:
            try:
                doc += create_figure(ds, instr)
                figure_success = True
            except:
                continue

        if figure_success:
            qa_figure_outpath = outpath
            ofilename = os.path.join(qa_figure_outpath, 'qa-%s_%s_%s.png' % (instr.__name__.split('.')[-1], date.strftime('%Y%m%d'), fid))
            plt.savefig(ofilename, dpi=120)
            sys.stdout.write('Figure created: %s\n ...\n' % ofilename)

    if decades_dataset:
        doc += flag_table(decades_dataset)
    else:
        doc += flag_table(nc_dataset)
    if core_rawdlu_zip:
        doc += file_table(core_rawdlu_zip)
    doc += TEX_FINAL

    tmppath = tempfile.mkdtemp()
    texfile = os.path.join(tmppath, 'qa-report_faam_%s.tex' % (fid,))
    f = open(texfile, 'w')
    f.write(doc)
    f.close()

    os.chdir(tmppath)
    # We need to run pdflatex twice to get the tables adjusted properly
    os.system('pdflatex %s' % (texfile,))
    os.system('pdflatex %s' % (texfile,))
    pdf_filename = os.path.basename(texfile)[:-4]+'.pdf'
    shutil.move(os.path.join(tmppath, os.path.basename(texfile)[:-4]+'.pdf'),
                os.path.join(outpath, pdf_filename))
    return os.path.join(outpath, pdf_filename)


def _argparser():
    import argparse
    from argparse import RawTextHelpFormatter
    sys.argv.insert(0, 'faampy qa_plotting')
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('-o', '--outpath',
                        action="store",
                        default=os.path.expanduser('~'),
                        type=str,
                        help='outpath for QA-Report')
    parser.add_argument('ncfilename',
                        action="store",
                        type=str,
                        default=0,
                        help='FAAM core netcdf')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    if not os.path.exists(args.ncfilename):
        sys.stdout.write('File does not exist ...\nLeaving ...\n')
        sys.exit(1)
    outfile = process(ncfilename=args.ncfilename,
                      outpath=args.outpath)
    sys.stdout.write('Created ... %s. \n' % outfile)


if __name__ == '__main__':
    main()
