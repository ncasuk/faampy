import os

from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(HERE, 'README.rst')) as f:
    long_description = f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

#http://thomas-cokelaer.info/blog/2012/03/how-to-embedded-data-files-in-python-using-setuptools/
datadir = os.path.join('files')
datafiles = [(d, [os.path.join(d, f) for f in files])
    for d, folders, files in os.walk(datadir)]


def get_faampy_version():
    version = None
    initpath = os.path.join(HERE, 'faampy', '__init__.py')
    with open(initpath) as fd:
        for line in fd:
            if line.startswith('__version__'):
                _, version = line.split('=')
                version = version.strip()[1:-1]  # Remove quotation characters
                break
    return version


setup(name = "faampy",
      version = get_faampy_version(),
      description = "python module for dealing with FAAM data",
      author = "Axel Wellpott",
      author_email = "axel dot wellpott at faam dot ac dot uk",
      url = "http://www.faam.ac.uk",
      package_dir = {'': '.'},
      packages=find_packages('.'), 
      # scripts are defined in the faampy.__init__ file
      entry_points={
          'console_scripts': [
                'faampy = faampy:command_line',]
          },
      license='LGPLv3',
      platforms = ['linux'],
      long_description = long_description,
      install_requires = required,
      include_package_data = True,
      data_files = datafiles,
      zip_safe = False,     # http://stackoverflow.com/questions/27964960/pip-why-sometimes-installed-as-egg-sometimes-installed-as-files
      keywords = ['FAAM',
                  'Facility for Airborne Atmospheric Measurements', 
                  'NCAS',
                  'MetOffice',
                  'data',
                  'science',
                  'meteorology',
                  'python',
                  'plotting'],
      classifiers=['Development Status :: 2 - Pre-Alpha',
                   'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Scientific/Engineering :: Visualization'])
