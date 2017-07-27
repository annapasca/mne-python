"""Build measurement info
"""

# Author: Vittorio Pizzella <vittorio.pizzella@unich.it>
#
# License: BSD (3-clause)

from time import strptime
from calendar import timegm

import numpy as np

from ...utils import logger
from ..meas_info import _empty_info
from ..constants import FIFF

from .constants import ITAB


def _convert_time(date_str, time_str):
    """Convert date and time strings to float time"""
    for fmt in ("%d/%m/%Y", "%d-%b-%Y", "%a, %b %d, %Y"):
        try:
            date = strptime(date_str, fmt)
        except ValueError:
            pass
        else:
            break
    else:
        raise RuntimeError(
            'Illegal date: %s.\nIf the language of the date does not '
            'correspond to your local machine\'s language try to set the '
            'locale to the language of the date string:\n'
            'locale.setlocale(locale.LC_ALL, "en_US")' % date_str)

    for fmt in ('%H:%M:%S', '%H:%M'):
        try:
            time = strptime(time_str, fmt)
        except ValueError:
            pass
        else:
            break
    else:
        raise RuntimeError('Illegal time: %s' % time_str)
    # MNE-C uses mktime which uses local time, but here we instead decouple
    # conversion location from the process, and instead assume that the
    # acquisiton was in GMT. This will be wrong for most sites, but at least
    # the value we obtain here won't depend on the geographical location
    # that the file was converted.
    res = timegm((date.tm_year, date.tm_mon, date.tm_mday,
                  time.tm_hour, time.tm_min, time.tm_sec,
                  date.tm_wday, date.tm_yday, date.tm_isdst))
    return res


def _mhdch_2_chs(mhd_ch):
    """Build chs list item from mhd ch list item"""
    
    ch = dict()

   # Generic channel
    loc=np.zeros(12)
    ch['ch_name'] = mhd_ch['label']
    ch['coord_frame'] = 0
    ch['coil_type'] = 0
    ch['range']  = 1.0
    ch['unit'] = FIFF.FIFF_UNIT_NONE
    ch['cal'] = 1.0
    ch['loc'] = loc
    ch['scanno'] = None
    ch['kind'] = FIFF.FIFFV_MISC_CH
    ch['logno']  = None

    nmeg = neeg = nref = 0
    
   # Magnetic channel
    if mhd_ch['type'] == ITAB.ITABV_MAG_CH:
        loc[0:12]= (mhd_ch['pos'][0]['posx']/1000,  #r0
                mhd_ch['pos'][0]['posy']/1000,  
                mhd_ch['pos'][0]['posz']/1000,
                mhd_ch['pos'][0]['orix'],  #ex
                0,
                0,
                0,                         #ey
                mhd_ch['pos'][0]['oriy'],
                0,
                0,                         #ez
                0,
                mhd_ch['pos'][0]['oriz'])         
        ch['loc'] = loc
        ch['kind'] = FIFF.FIFFV_MEG_CH
        ch['coil_type'] = FIFF.FIFFV_COIL_POINT_MAGNETOMETER
        if mhd_ch['calib'] == 0:
 #           ch['cal'] = 0
            ch['cal'] = 0.001
        else:
            ch['cal'] = mhd_ch['amvbit'] / mhd_ch['calib']
        ch['unit'] = FIFF.FIFF_UNIT_T
        if mhd_ch['unit'] == "fT":
            ch['unit_mul'] = FIFF.FIFF_UNITM_F
        elif mhd_ch['unit'] == "pT":
            ch['unit_mul'] = FIFF.FIFF_UNITM_P
            
        nmeg += 1
        ch['logno'] = nmeg    
    
   # Electric channel
    if mhd_ch['type'] == ITAB.ITABV_EEG_CH:     
        ch['kind'] = FIFF.FIFFV_BIO_CH
        ch['cal'] = mhd_ch['amvbit'] / mhd_ch['calib']
        ch['unit'] = FIFF.FIFF_UNIT_V
        if mhd_ch['unit'] == "mV":
            ch['unit_mul'] = FIFF.FIFF_UNITM_M
        elif mhd_ch['unit'] == "uT":
            ch['unit_mul'] = FIFF.FIFF_UNITM_MU

        neeg += 1
        ch['logno'] = neeg
        
   # Other channel type
    if (mhd_ch['type'] == ITAB.ITABV_REF_EEG_CH    and     
        mhd_ch['type'] == ITAB.ITABV_REF_MAG_CH    and 
        mhd_ch['type'] == ITAB.ITABV_REF_AUX_CH    and 
        mhd_ch['type'] == ITAB.ITABV_REF_PARAM_CH  and
        mhd_ch['type'] == ITAB.ITABV_REF_DIGIT_CH  and
        mhd_ch['type'] == ITAB.ITABV_REF_FLAG_CH  ):

        ch['kind'] = FIFF.FIFFV_BIO_CH
        ch['cal'] = 1
        ch['unit'] = FIFF.FIFF_UNIT_V
        if mhd_ch['unit'] == "mV":
            ch['unit_mul'] = FIFF.FIFF_UNITM_M
        elif mhd_ch['unit'] == "uT":
            ch['unit_mul'] = FIFF.FIFF_UNITM_MU
    
        nref += 1
        ch['logno'] = nref
        
    return ch
   
   
def _mhd2info(mhd):
    """Create meas info from ITAB mhd data"""

    info = _empty_info(mhd['smpfq'])
  
    info['meas_date'] = _convert_time(mhd['date'], mhd['time'])
    
    info['description'] = mhd['notes']
    
    si = dict()
#    si['id'] = mhd['id']
    si['last_name'] = mhd['last_name']
    si['first_name'] = mhd['first_name']
    si['sex'] = mhd['subinfo']['sex']
                
    info['subject_info'] = si

    ch_names = list()
    chs = list()
    bads = list()
    for k in range(mhd['nchan']):   
        ch_names.append(mhd['ch'][k]['label'])
        if (mhd['ch'][k]['flag'] > 0):
            bads.append(mhd['ch'][k]['label'])
        y = _mhdch_2_chs(mhd['ch'][k])
        chs.append(y)
        
    info['bads'] = bads
    info['chs']  = chs
    info['ch_names'] = ch_names

    info['lowpass']  = mhd['hw_low_fr'] 
    info['highpass'] = mhd['hw_hig_fr']
 
# Total number of channels in .raw file
    info['nchan']    = mhd['nchan']
    info['n_chan']   = mhd['nchan']
# Total number of timepoints in .raw file
    info['n_samp']   = mhd['ntpdata']
# Only one trial (continous acquisition)
    info['n_trials'] = 1    
# Data start in .raw file
    info['start_data'] = mhd['start_data']
    
    
# Get Polhemus digitization data (in head coordinates) 
    
    dig = []
   
# Nasion    
    point_info = dict()
    point_info['coord_frame'] = FIFF.FIFFV_COORD_HEAD   
    point_info['kind']  = FIFF.FIFFV_POINT_CARDINAL
    point_info['ident'] = FIFF.FIFFV_POINT_NASION 
    point_info['r'] = ( mhd['marker'][0]['posx']/1000,
                        mhd['marker'][0]['posy']/1000,
                        mhd['marker'][0]['posz']/1000)
    dig += [point_info]
# Right pre-auricolar  
    point_info = dict()
    point_info['coord_frame'] = FIFF.FIFFV_COORD_HEAD   
    point_info['kind']  = FIFF.FIFFV_POINT_CARDINAL
    point_info['ident'] = FIFF.FIFFV_POINT_RPA 
    point_info['r'] = ( mhd['marker'][1]['posx']/1000,
                        mhd['marker'][1]['posy']/1000,
                        mhd['marker'][1]['posz']/1000 )
    dig += [point_info]
# Left pre-auricolar  
    point_info = dict()
    point_info['coord_frame'] = FIFF.FIFFV_COORD_HEAD   
    point_info['kind']  = FIFF.FIFFV_POINT_CARDINAL
    point_info['ident'] = FIFF.FIFFV_POINT_LPA 
    point_info['r'] = ( mhd['marker'][2]['posx']/1000,
                        mhd['marker'][2]['posy']/1000,
                        mhd['marker'][2]['posz']/1000)
    dig += [point_info]
# Vertex  
    point_info = dict()
    point_info['coord_frame'] = FIFF.FIFFV_COORD_HEAD   
    point_info['kind']  = FIFF.FIFFV_POINT_EXTRA
    point_info['ident'] = 4 
    point_info['r'] = ( mhd['marker'][3]['posx']/1000,
                        mhd['marker'][3]['posy']/1000,
                        mhd['marker'][3]['posz']/1000)
    dig += [point_info]
# HPI coils
    for k in range(4, mhd['num_markers']):   
        point_info = dict()
        point_info['coord_frame'] = FIFF.FIFFV_COORD_HEAD   
        point_info['kind']  = FIFF.FIFFV_POINT_HPI
        point_info['ident'] = k+1 
        point_info['r'] = ( mhd['marker'][k]['posx']/1000,
                            mhd['marker'][k]['posy']/1000,
                            mhd['marker'][k]['posz']/1000)
        dig += [point_info]
# TDB other poosible head points, check on dig points.      
      
    info['dig'] = dig

 # TBD trigger handling

    event = list()
    for k in range(mhd['nsmpl']):   
        event.append([ mhd['sample'][k]['start'], 
                       mhd['sample'][k]['type'], 
                       mhd['sample'][k]['quality'] ])
 
    info._check_consistency()

    logger.info('    Measurement info composed.')
            
    return info
