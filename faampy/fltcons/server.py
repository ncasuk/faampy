'''
Created on 8 May 2013

@author: axel
'''


import sys
sys.path.insert(0, '/home/axel/git-repos/faampy')


import BaseHTTPServer
import CGIHTTPServer
import cgitb; cgitb.enable()  ## This line enables CGI error reporting

import shutil
import os
import sys
import tempfile

HOST_NAME = 'localhost' 
PORT_NUMBER = 8080

# create temporary directory from where we will run the http server
TMP_DIR = tempfile.mkdtemp()
os.mkdir(os.path.join(TMP_DIR, 'cgi-bin'))
os.mkdir(os.path.join(TMP_DIR, 'img'))

sys.stdout.write('HTTP-Server running from: %s ...\n' % TMP_DIR)
                   
src = os.path.join('/home/axel/git-repos/faampy/faampy', 'fltcons', 'cgi-fltcons-summary.py')
dst = os.path.join(TMP_DIR, 'cgi-bin', 'cgi-fltcons-summary.py')

shutil.copy(src, dst)

os.chmod(dst, 0777)

os.chdir(TMP_DIR)

sys.stdout.write('Now go to: http://localhost:8080/cgi-bin/cgi-fltcons-summary.py\n')
server=BaseHTTPServer.HTTPServer
handler=CGIHTTPServer.CGIHTTPRequestHandler
server_address = ("", PORT_NUMBER)
#handler.cgi_directories = ["/cgi-bin"]
httpd = server((HOST_NAME, PORT_NUMBER), handler)
httpd.serve_forever()
