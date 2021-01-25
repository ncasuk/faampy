========
Synopsis
========

This module helps with the processing and analysis of data from the `FAAM <http://www.faam.ac.uk/>`_ aircraft. The documentation including recipes is available online at `readthedocs.org <http://faampy.readthedocs.io/en/latest/>`_.


==========
Motivation
==========

The faampy repository provides python modules for working with data from the FAAM aircraft. Its main goals are to minimize code duplication and to increase the efficiency of the data analysis. Spend less time data wrangling; spend more time on analysis.


============
Installation
============

The installation of the module is done in the usual way::

    git clone https://github.com/ncasuk/faampy.git
    cd faampy
    python setup.py build
    sudo python setup.py install

In case you do not have superuser rights on the computer you can use the "--user" option with the install command::
    
    git clone https://github.com/ncasuk/faampy.git
    cd faampy
    python setup.py build
    python setup.py install --user
    
============
Examples
============

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ncasuk/faampy/HEAD)

    
============
Contributors
============

* Axel Wellpott (FAAM)
* Dave Tiddeman (MetOffice)

 
======= 
License
=======

faampy is licenced under GNU Lesser General Public License (LGPLv3).
