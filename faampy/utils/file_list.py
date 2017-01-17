import os
import sys

import file_info


class File_List(list):
    """
    A list of File_Info objects. The list can be sorted and filtered which can
    be useful for batch processing.
    
    For example it is possible to (i) get all DECADES rawdlu and flight-constant
    files from a path, (ii) filter those for the latest revisions and reprocess
    them.
    
    """
    def __init__(self, path):        
        """
        Get all FAAM data files in the path.
        
        :param path: path which will be walked and checked for FAAM data files        
        """
        self.Path = path
        if os.path.isdir(path):
            for root, subFolders, files in os.walk(self.Path):
                for f in files:
                    if file_info.get_data_type_from_filename(f):
                        self.append(file_info.File_Info(os.path.join(root, f)))
        else:
            sys.stdout.write('%s is not a directory.\n' % path)
        self.sort()

    def filter_by_data_type(self, dtype):
        """
        Filtering by data type.
        """
        if not dtype in file_info.DATA_TYPES:
            sys.stdout.write('Submitted dtype unknown.\nValid data types are: %s\n' % ', '.join(sorted(file_info.DATA_TYPES.keys())))
            
        bad_index = []
        for i in self:
            if not i.data_type == dtype:   
                bad_index.append(i)
        for b in bad_index:
            self.remove(b)

    def filter_latest_revision(self):
        """
        Compresses the list and keeps only the latest revision file for a FID
        """
        bad_index = []        
        self.sort(key=lambda i: '%4s_%s_%0.3i' % (i.fid, i.data_type, i.rev))
        self.reverse()
        for i in range(len(self)-1):
            if ((self[i].fid, self[i].data_type)) == ((self[i+1].fid, self[i+1].data_type)):
                bad_index.append(self[i+1])
        for b in bad_index:
            self.remove(b)                        
        self.sort()
        
    def __str__(self):
        output = ''
        for i in self:
            output += '%s\n' % (i.filename,)
        return output

    def get_filenames(self):
        """
        Returns the filenames
        """
        result = [os.path.join(i.path, i.filename) for i in self]
        return result


