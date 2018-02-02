import os
import sys
import faampy
import file_info


class File_List(list):
    """
    A list of File_Info objects. The list can be sorted and filtered which can
    be useful for batch processing.

    For example it is possible to (i) get all DECADES rawdlu and flight
    constant files from a path, (ii) filter those for the latest revisions and
    reprocess them.
    """

    def __init__(self, *args):
        """
        Get all FAAM data files in the path. The path argument can either be
        *one* existing path or a list of paths.

        If no path is supplied the directories that are defined in the
        .faampy_config file are searched.

        :param str path: path which will be walked and checked for
          FAAM data files

        :Example:

          In [16]: l = File_List('/home/axel/gdrive/ncas/core_processing/')

          In [17]: print(l)
          0: flight-sum_faam_20150806_r0_b919.txt
          1: core_faam_20150806_r0_b919_rawdlu.zip
          2: flight-cst_faam_20150806_r0_b919.txt
          3: flight-cst_faam_20150806_r1_b919.txt
        """
        if args:
            path_list = args[0]
            if not hasattr(path_list, "__iter__"):
                path_list = [path_list, ]
        else:
            path_list = faampy.DATA_SEARCH_PATH_LIST

        self.Path_List = path_list[:]
        for path in self.Path_List:
            if os.path.isdir(path):
                for root, subFolders, files in os.walk(path):
                    for f in files:
                        if file_info.get_data_type_from_filename(f):
                            finfo = file_info.File_Info(os.path.join(root, f))
                            if int(finfo.rev) < 90:
                                self.append(finfo)
            else:
                sys.stdout.write('%s: does not exist.\n' % path)
        self.sort()

    def filter_by_data_type(self, dtype):
        """
        Filtering by data type.
        """
        if dtype not in file_info.DATA_TYPES:
            sys.stdout.write('Submitted dtype unknown.\nValid data types are: %s\n' % ', '.join(sorted(file_info.DATA_TYPES.keys())))

        bad_index = []
        for i in self:
            if not i.data_type == dtype:
                bad_index.append(i)
        for b in bad_index:
            self.remove(b)

    def filter_latest_revision(self):
        """
        Compresses the list and keeps only the latest revision for a FID.
        """
        bad_index = []
        self.sort(key=lambda i: '%4s_%s_%s_%0.3i' % (i.fid, i.date,
                                                     i.data_type, i.rev))
        self.reverse()
        for i in range(len(self)-1):
            if ((self[i].fid, self[i].date, self[i].data_type)) == ((self[i+1].fid, self[i+1].date, self[i+1].data_type)):
                bad_index.append(self[i+1])
        for b in bad_index:
            self.remove(b)
        self.sort()

    def __str__(self):
        output = ''
        for _i, i in enumerate(self):
            output += '%i: %s\n' % (_i+1, i.filename)
        return output

    def get_filenames(self):
        """
        Returns the file names for each entry.
        """
        result = [os.path.join(i.path, i.filename) for i in self]
        return result

    def extract_fid(self, fid):
        ix = [i for i, x in enumerate(self) if x.fid == fid]
        return _File_List([self[i] for i in ix])

    def extract_date(self, date_string):
        ix = [i for i, x in enumerate(self) if x.date.startswith(date_string)]
        return _File_List([self[i] for i in ix])


class _File_List(File_List):
    """
    Copy of the File_List class that takes a list of file_info objects as an
    input instead of paths.
    """
    def __init__(self, file_info_items):
        for i in file_info_items:
            self.append(i)
