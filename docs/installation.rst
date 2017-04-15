
Installing faampy
=================

Installation of faampy is done in the usual way using the setup script::

    git clone https://github.com/ncasuk/faampy.git
    python setup.py build
    sudo python setup.py install

So far the module has only been tested on linux machines and most of the code development has been done with python 2.7. However the idea is to make faampy python3 compatible and platform independent.


Example flight data, databases, ...
-----------------------------------

Example data and databases of flight tracks are available for download. After installing the faampy module you can run::

   faampy data_download ZIP_PASSWORD

from the command line. This will download a zip file and copies its content to a 'faampy_data' directory in your $HOME directory. However, for the moment the zip file that you download is password protected. Please contact me if you think you need the data and I will give you the password.


Disclaimer
----------

faampy is in its early stages and has not been thoroughly tested. There will more modules been added in the near future. A backlog of moduls exists that have been written, but will need to be tidied up, before being added to the repository.
