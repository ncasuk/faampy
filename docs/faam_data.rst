
============
FAAM_Dataset
============

The FAAM_Dataset class handles the core_faam* netCDF and smoothes out the reading process of the data and ensures that older files are read in the same way as newer ones. The class copies the behaviour of netCDF4.Dataset. 

A nifty method of the class is merge, which enables you to merge data from a separate file. The data type that can be merged is a numpy.recarray. The index for the procedure is the timestamp, of the FAAM_Dataset. Care is taken off gaps in the recarray.

A convenient option is exporting the Dataset into a pandas DataFrame, which then gives you all the amazing features of pandas. Due to the fact that pandas can't deal with multidimensional arrays, only the first measurement within a row is used for the DataFrame.



.. automodule:: faampy.core.faam_data
   :members: FAAM_Dataset


