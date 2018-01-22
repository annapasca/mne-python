"""Conversion tool from ITAB to FIF
"""

# Author: Vittorio Pizzella <vittorio.pizzella@unich.it>
#
# License: BSD (3-clause)

import numpy as np

from ...utils import verbose
from ..base import BaseRaw
from ..utils import _mult_cal_one

from .mhd import _read_mhd
from .info import _mhd2info
from .constants import ITAB

class RawITAB(BaseRaw):
    """Raw object from ITAB directory

    Parameters
    ----------
    fname : str
        The raw file to load. Filename should end with *.raw
    preload : bool or str (default False)
        Preload data into memory for data manipulation and faster indexing.
        If True, the data will be preloaded into memory (fast, requires
        large amount of memory). If preload is a string, preload is the
        file name of a memory-mapped file which is used to store the data
        on the hard drive (slower, requires less memory).
    verbose : bool, str, int, or None
        If not None, override default verbose level (see mne.verbose).

    See Also
    --------
    mne.io.Raw : Documentation of attribute and methods.
    """
    
    @verbose
    def __init__(self, fname, preload=False, verbose=True):


#        if preload:
#            self._preload_data(preload)
#        else:
#            self.preload = False
        
        file_name = list()
        file_name.append(fname)
        
        fname_mhd = fname + ".mhd"
        mhd = _read_mhd(fname_mhd)  # Read the mhd file
        info = _mhd2info(mhd)
        info['buffer_size_sec'] = info['n_samp'] / info['sfreq']
        print(info['buffer_size_sec'])

        pass
        if info.get('buffer_size_sec', None) is None:
            raise RuntimeError('Reader error, notify mne-python developers')
        self.info = info
#        self.n_times = info['n_samp']
#        self.times = info['n_samp']
        info._check_consistency()
        
        first_samps = list()
        first_samps.append(0)
        
        last_samps = list()
        last_samps.append(info['n_samp'] - 1)
        
#        self._update_times()
        super(RawITAB, self).__init__(
            info, preload, last_samps=last_samps, filenames=file_name,
            verbose=verbose)
 

    @verbose
    def _read_segment_file(self, data, idx, fi, start, stop, cals, mult):
        """Read a chunk of raw data"""
        
        #  Initial checks
        start = int(start)
        if stop is None:
            stop = self.info['n_samp']
#        else:
#            min([int(stop), self.n_times])

        if start >= stop:
            raise ValueError('No data in this range')

 #       offset = 0
        with open(self._filenames[fi], 'rb') as fid:

        #position  file pointer
            data_offset = self.info['start_data']
            fid.seek(data_offset + start * self.info['nchan'], 0)            

        # read data                
            n_read = self.info['n_chan']*self.info['n_samp']
            this_data = np.fromfile(fid, '>i4', count=n_read)
            this_data.shape = (self.info['n_samp'], self.info['nchan'])
           
            data_view = data[:, 0:self.info['n_samp']]
          
        # calibrate data                                
            _mult_cal_one(data_view, this_data.transpose(), idx, cals, mult)
            
            pass
  

def read_raw_itab(fname, preload=False, verbose=None):
    """Raw object from ITAB directory

    Parameters
    ----------
    fname : str
        The raw file to load. Filename should end with *.raw
    preload : bool or str (default False)
        Preload data into memory for data manipulation and faster indexing.
        If True, the data will be preloaded into memory (fast, requires
        large amount of memory). If preload is a string, preload is the
        file name of a memory-mapped file which is used to store the data
        on the hard drive (slower, requires less memory).
    verbose : bool, str, int, or None
        If not None, override default verbose level (see mne.verbose).

    Returns
    -------
    raw : instance of RawITAB
        The raw data.

    See Also
    --------
    mne.io.Raw : Documentation of attribute and methods.

    Notes
    -----
    .. versionadded:: 0.01
    """
    
    a = RawITAB(fname, preload=preload, verbose=verbose)
    pass
    return a
