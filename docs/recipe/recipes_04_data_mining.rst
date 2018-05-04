
Recipe - Data Mining
--------------------

The code snipped below loops over all FAAM core data files and extracts the CO
and O3 data plus coordinates. All data are concatenated and written out into
**one** large csv file.

Data extraction
^^^^^^^^^^^^^^^

First we start with extracting the data from all the FAAM core data files.

.. literalinclude:: /../examples/faampy_data_mining_example.py
   :language: python
   :start-after: Step:Start:Data Mining Extraction
   :end-before: Step:End:Data Mining Extraction

Example analysis
^^^^^^^^^^^^^^^^

Now we use the extracted data to plot a profile, where the data are aggregated in 100m
height altitude bin sizes.
   
.. literalinclude:: /../examples/faampy_data_mining_example.py
   :language: python
   :start-after: Step:Start:Analysis Violin Plot
   :end-before: Step:Stop:Analysis Violin Plot

.. figure:: /recipe/img/data_mining_o3_profiles_gt_62n.png
   :align: center
