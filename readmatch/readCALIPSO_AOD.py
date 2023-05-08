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
fnames = ['Column_Feature_Fraction',
          'Column_IAB_Cumulative_Probability',
          'Column_Integrated_Attenuated_Backscatter_532',
          'Column_Optical_Depth_Cloud_532',
          'Column_Optical_Depth_Cloud_Uncertainty_532',]

varnames = fname1+fname2+fname3+fname4+fnames
#%%
def process(month):
# for month in [1]:

    num_mon = '%02d' % month
    # df_T = pd.DataFrame(columns=varnamesT)
    df = pd.DataFrame(columns=varnames)
    CALnames=[filename for filename in
        os.listdir(readpath)
        # if filename.endswith('.hdf')]
        if filename.startswith('CAL_LID_L2_05kmAPro-Standard-V4-20.2017-'+num_mon)]
    #%%
    for ii in tqdm(range(len(CALnames)), desc=num_mon):

        CALIPSO = SD(readpath+CALnames[ii])
        #%%
        Lat = CALIPSO.select('Latitude')[:]
        Lon = CALIPSO.select('Longitude')[:]
        t = CALIPSO.select('Profile_Time')[:]
        UTC_t = CALIPSO.select('Profile_UTC_Time')[:]
        data = np.hstack((Lat, Lon, t, UTC_t))
        for var in fnames:
            data = np.hstack((data, CALIPSO.select(var)[:]))
        df1 =  pd.DataFrame(data, columns=varnames)
        #%%
        df = pd.concat([df, df1], ignore_index=True)
    #%%
    # savepathT = '/home/fuhy/data/CALIPSO/T/'+num_year+'/'
    # savenameT = 'CALIPSO_T_'+num_year+'_'+num_mon+'.feather'
    # pathnameT = savepathT+savenameT
    # df_T[varnamesT].to_feather(pathnameT)

    savepath = '/home/fuhy/data/CALIPSO/AOD/'+num_year+'/'
    savename = 'CALIPSO_AOD_'+num_year+'_'+num_mon+'.feather'
    pathname = savepath+savename
    df[varnames].to_feather(pathname)

#%%
pool = ThreadPool()
pool.map(process, months)
pool.close()
pool.join()
