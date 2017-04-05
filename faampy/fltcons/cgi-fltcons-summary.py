#!/usr/bin/env python

import sys
import os
import matplotlib
matplotlib.use('Agg')
import cgi

import faampy.fltcons
from faampy.fltcons.db import DB
from faampy.fltcons.Summary import Summary
from faampy.fltcons.Plot import Plot

fltcons_list = faampy.fltcons.PARAMETERS
fltcons_list.sort()

#faampy.fltcons.FIGURES_PATH = '/home/axel/.faampy/tmp/'

dirname, filename = os.path.split(os.path.abspath(__file__))

faampy.fltcons.FIGURES_PATH = os.path.join(dirname, '..', 'img')


spacer = "<p>&nbsp;</p>"

form_header = """<FORM ACTION="cgi-fltcons-summary.py">
                   <DIV id="FLTCONS-SELECT"><table width=200>
                   <tr>
                     <td width="45%"><strong>Flight-Constant: </strong></td>
                     <td width="45%" align="left">
                       <SELECT size="1" NAME="cgi_fltcons" style="width:100px">"""

form_options = """<OPTION VALUE="%s"> %s \n"""
form_footer = """</SELECT></td></tr>
<tr><td>&nbsp;</td>

<td align="right"><INPUT TYPE=checkbox NAME="cgi_filtered" value="on" %s/>Filter off
<tr><td>&nbsp;</td>
<td align="right"><INPUT TYPE=submit VALUE="Go!"></td></tr></table></DIV>


</FORM>"""

html_header = 'Content-Type: text/html\n\n'

html_body_header = """<HTML><HEAD><TITLE>Flight-Constant-Browser</TITLE></HEAD>
<BODY TOPMARGIN="50px" LEFTMARGIN="50px" MARGINHEIGHT="50px" MARGINWIDTH="100px">"""

html_body_footer = """</BODY></HTML>"""



def showForm(fltcons, filtered=None):

    if not filtered:
        filtered = False
        filtered_checked_txt = 'checked'
    else:
        filtered_checked_txt = ''

    html = ""
    opt = ""
    if fltcons:
        opt += form_options % (fltcons, fltcons)

    for fltcon in fltcons_list:
        opt += form_options % (fltcon, fltcon)

    if fltcons:
        fcs = Summary(fltcons, filtered=filtered)
        fcs_txt = "<p><pre>" + fcs.__str__() + "</pre></p>"

        fcp = faampy.fltcons.Plot.Plot(fltcons)
        fcp.get_data()
        fcp.create()
        filename = os.path.join(faampy.fltcons.FIGURES_PATH, fltcons + '.png')
        fcp.Figure.savefig(filename)

        img_url = os.path.join(faampy.fltcons.FIGURES_URL, fltcons + '.png')
        fcs_plot = """<p><img src=" %s" border="0" align="left" /></p>""" % ('/img'+img_url)
    else:
        fcs_txt = ""
        fcs_plot = ""

    html += html_header + \
            html_body_header + \
            form_header + \
            opt + \
            form_footer % (filtered_checked_txt) + \
            fcs_plot + \
            6 * spacer + \
            "<hr>" + \
            fcs_txt + \
            html_body_footer
    print html


def process():
    form = cgi.FieldStorage()
    # get flt-constant parameter name
    if form.has_key('cgi_fltcons'):
        fltcons = form['cgi_fltcons'].value
    else:
        fltcons = None
    if form.getvalue('cgi_filtered'):
        filter_value = False
    else:
        filter_value = True
    showForm(fltcons, filtered=filter_value)


if __name__ == '__main__':
    process()

