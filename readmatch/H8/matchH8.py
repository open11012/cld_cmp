#%% 匹配H8示例
# fuhaoyang
# 2023/3/19
import pandas as pd
import numpy as np
import xarray as xr
from tqdm import tqdm
import os
from multiprocessing.dummy import Pool as ThreadPool
import sys
sys.path
sys.path.append('/home/fuhy/data/SWC/code/preprocessing/readmatch')
import readX # type: ignore
# import importlib
# importlib.reload(readX.readERA)
from readX.readH8 import readH8data # type: ignore
#%% 选取一个H8Timelist
pathTimelist = '/home/public/data/jma/netcdf/201701/01/NC_H08_20170101_0000_R21_FLDK.06001_06001.nc'
H8Timelist = xr.open_dataset(pathTimelist)['Hour']


path_H8     = '/home/public/data/jma/netcdf/'
H8bands = ['albedo_01', 'albedo_02', 'albedo_03', 'albedo_04', 'albedo_05',
           'albedo_06', 'tbb_07', 'tbb_08', 'tbb_09', 'tbb_10', 'tbb_11', 'tbb_12',
           'tbb_13', 'tbb_14', 'tbb_15', 'tbb_16', 'SOZ', 'SAZ', 'SOA', 'SAA', 'Hour']
H8bands1 = ['albedo_01', 'albedo_02', 'albedo_03', 'albedo_04', 'albedo_05',
           'albedo_06', 'tbb_07', 'tbb_08', 'tbb_09', 'tbb_10', 'tbb_11', 'tbb_12',
           'tbb_13', 'tbb_14', 'tbb_15', 'tbb_16', 'SOZ', 'SAZ', 'SOA', 'SAA', 'Hour']
#%%
# 各月
months = [1, 4, 8, 11]

def process(month):
    num_mon = '%02d' % month
    AVDname = '/home/fuhy/data/CALIPSO/AVD/2017/CALIPSO_AVD_2017_' + num_mon + '.csv'
    # AVDname = '/Users/fu/数据/CALIPSO/AVD_2016/CALIPSO_AVD_2016_' + num_mon + '.csv'
    df = pd.read_csv(AVDname, usecols=['Latitude_2', 'Longitude_2', 'Profile_UTC_Time_2'])
    # Himawari-8
    df_H8 = readH8data(df['Profile_UTC_Time_2'], df['Latitude_2'], df['Longitude_2'], H8bands, path_H8, H8Timelist)
    savepath = '/home/fuhy/data/SWC/data/H8/'
    filename = 'H8_SWC_2017_' + num_mon + '.csv' # 这里保存名称中的月份可能因为最后一个数据而变为下一个月
    pathname = savepath+filename
    df_H8.columns = H8bands1
    df_H8.to_csv(pathname)


pool = ThreadPool()
pool.map(process, months)
pool.close()
pool.join()