# read CALIPSO:
#           1. Temperature profiles
#           2. AVD
# fuhaoyang
# 2023/3/21
#%%
import pandas as pd
import numpy as np
from tqdm import tqdm
from pyhdf import SD   # must prefix names with "SD."
from pyhdf.SD import * # type: ignore # names need no prefix
import os
from multiprocessing.dummy import Pool as ThreadPool


#%%
months =  list(np.arange(1,13))
num_year = '%04d' % 2017
#%%
readpath = '/home/fuhy/public/data/CALIPSO/APro/2017/'


fname1 = ['Latitude_' + str(s) for s in np.arange(1,4)]
fname2 = ['Longitude_' + str(s) for s in np.arange(1,4)]
fname3 = ['Profile_Time_' + str(s) for s in np.arange(1,4)]
fname4 = ['Profile_UTC_Time_' + str(s) for s in np.arange(1,4)]
fnameT = ['Temperature_' + str(s) for s in np.arange(1,400)]
fnameAVD = ['Atmospheric_Volume_Description_' + str(s) for s in np.arange(1,799)]
fnameST =  ['IGBP_Surface_Type'] # IGBP_Surface_Type

varnamesT = fname1+fname2+fname3+fname4+fnameT
varnamesAVD = fname1+fname2+fname3+fname4+fnameAVD+fnameST

#%%
def process(month):

    num_mon = '%02d' % month
    df_T = pd.DataFrame(columns=varnamesT)
    df_AVD = pd.DataFrame(columns=varnamesAVD)
    CALnames=[filename for filename in
        os.listdir(readpath)
        # if filename.endswith('.hdf')]
        if filename.startswith('CAL_LID_L2_05kmAPro-Standard-V4-20.2017-'+num_mon)]
    #%%
    for ii in tqdm(range(len(CALnames)), desc=num_mon):

        CALIPSO = SD(readpath+CALnames[ii])
        #%%
        # df = pd.DataFrame()
        # df
        Lat = CALIPSO.select('Latitude')[:]
        Lon = CALIPSO.select('Longitude')[:]
        t = CALIPSO.select('Profile_Time')[:]
        UTC_t = CALIPSO.select('Profile_UTC_Time')[:]
        T = CALIPSO.select('Temperature')[:]
        # AVD0 = CALIPSO.select('Atmospheric_Volume_Description')[:,:,0]
        # AVD1 = CALIPSO.select('Atmospheric_Volume_Description')[:,:,1]
        # ST = CALIPSO.select('IGBP_Surface_Type')[:] # IGBP_Surface_Type
        df_T1 =  pd.DataFrame(np.hstack((Lat, Lon, t, UTC_t, T)), columns=varnamesT)
        # df_AVD1 =  pd.DataFrame(np.hstack((Lat, Lon, t, UTC_t, AVD0, AVD1, ST)), columns=varnamesAVD)
        #%%
        df_T = pd.concat([df_T, df_T1], ignore_index=True)
        # df_AVD = pd.concat([df_AVD, df_AVD1], ignore_index=True)
    #%%
    savepathT = '/home/fuhy/data/CALIPSO/T/'+num_year+'/'
    savenameT = 'CALIPSO_T_'+num_year+'_'+num_mon+'.feather'
    pathnameT = savepathT+savenameT
    df_T[varnamesT].to_feather(pathnameT)

    # savepathAVD = '/home/fuhy/data/CALIPSO/AVD/'+num_year+'/'
    # savenameAVD = 'CALIPSO_AVD_'+num_year+'_'+num_mon+'.feather'
    # pathnameAVD = savepathAVD+savenameAVD
    # df_AVD[varnamesAVD].to_feather(pathnameAVD)

#%%
pool = ThreadPool()
pool.map(process, months)
pool.close()
pool.join()
