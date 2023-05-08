#%% 匹配H8示例
# fuhaoyang
# 2023/3/6 10:
import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
import netCDF4 as nc
import xarray as xr
import datetime
from tqdm import tqdm
import csv
# from netCDF4 import num2date, date2num, date2index
import pyhdf.SD        # must prefix names with "pyhdf.SD."
from pyhdf import SD   # must prefix names with "SD."
from pyhdf.SD import * # type: ignore # names need no prefix
import scipy.io as scio
import os

#%% Functions for reading ERA data.
def round_hour_toERA(dt):
    # Rounds to the nearest hour by adding a timedelta hour if minute >= 30
    date = np.floor(dt)
    time = dt - date
    t = datetime.datetime.strptime('20' + str(date)[0:6], '%Y%m%d') + timedelta(days=time)
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour)
            + timedelta(hours=t.minute // 30))  # 向下取整


def round_lat_toERA(lat):
    lat = np.round(lat / 0.25) * 0.25
    return lat


def round_lon_toERA(lon):
    idx = lon < 0
    lon = lon + idx * 360
    lon = np.round(lon / 0.25) * 0.25
    return lon


def readERApl(field, time, levels, latitude, longitude):
    value = field.loc[time, levels, latitude, longitude].values
    return value


def readERAsl(field, time, latitude, longitude):
    value = field.loc[time, latitude, longitude].values
    return value


#%% Functions for reading Himawari data.
def stdTime(dt_cal):
    # CALIPSO Profile_UTC_Time转换为'yyyyMMddHHmmss'
    date = np.floor(dt_cal)
    time = dt_cal - date
    dt_std = datetime.datetime.strptime('20' + str(date)[0:6], '%Y%m%d') + timedelta(days=time)

    return dt_std


def getH8idx(lat_cal, lon_cal):
    # 根据经纬度获取H8网格行列号 (6001, 6001)

    #  得到H8经纬度序列
    Lat_H8 = 60-np.arange(0, 120.02, 0.02) # H8纬度序列
    Lon_H8 = 80+np.arange(0, 120.02, 0.02) # H8经度序列
    # 经度范围转换
    idx = lon_cal < 0
    lon_cal = lon_cal + idx * 360
    # 确定目标点不超出H8经纬度范围边界
    lon_cal = max(80, lon_cal)
    lon_cal = min(200,lon_cal)
    lat_cal = max(-60,lat_cal)
    lat_cal = min(60, lat_cal)
    # 找到距离CALIPSO最近的H8点经纬度，网格位置
    # H8经纬度为0.02度的网格，保留2位小数
    idx_H8Lat = round((60 - lat_cal)/0.02)
    idx_H8Lon = round((lon_cal - 80)/0.02)


    # loc = [int(3000 - lat_h[i,0]*50), int(lon_h[i,0]*50 - 4000)]
    return idx_H8Lat, idx_H8Lon


def getH8dtstr(dt_std, lat_cal, lon_cal, Timelist):
    # H8name的日期时间，返回string

    # 找到对应H8网格像元的成像时间
    H8Hour = Timelist.sel(latitude=lat_cal, longitude=lon_cal, method="nearest").values # numpy.timedelta64
    # 根据CALIPSO时间、H8像元成像时间，找到对应H8文件的日期、时间，确定H8文件名
    # 读取H8时间，dt_std为datetime，H8Hour为datetime64
    dt_std = pd.to_datetime(dt_std) - H8Hour # 去除像元成像时间，'HHmmss'

    # H8d format: yymmdd
    H8d = dt_std.strftime("%y%m%d")
    # H8t format: hhmm
    dt_ms = timedelta(minutes=dt_std.minute, seconds=dt_std.second) # 得到mmss
    H8t1= "%02d" % dt_std.hour
    # 转换最近H8的mm00，H8为每十分钟一次观测
    if (dt_ms >= timedelta(minutes=54.5)) |( dt_ms < timedelta(minutes=4.5)):
        H8t2 = "%02d" % 0
    elif (dt_ms >= timedelta(minutes=4.5)) & (dt_ms < timedelta(minutes=14.5)):
        H8t2 = "%02d" % 10
    elif (dt_ms >= timedelta(minutes=14.5)) &( dt_ms < timedelta(minutes=24.5)):
        H8t2 = "%02d" % 20
    elif (dt_ms >= timedelta(minutes=24.5)) &( dt_ms < timedelta(minutes=34.5)):
        H8t2 = "%02d" % 30
    elif (dt_ms >= timedelta(minutes=34.5)) &( dt_ms < timedelta(minutes=44.5)):
        H8t2 = "%02d" % 40
    elif (dt_ms >= timedelta(minutes=44.5)) &( dt_ms < timedelta(minutes=54.5)):
        H8t2 = "%02d" % 50   # 格式mm00
    else:
        H8t2 = "%02d" % 99 # 格式mm00

    H8t = H8t1 + H8t2
    # H8d format: yymmdd
    # H8t format: hhmm
    return H8d, H8t



def getH8name(dt_cal, lat_cal, lon_cal, Timelist):
    # 获取目标匹配的H8name
    # CALIPSO Profile_UTC_Time转换为'yyyyMMddHHmmss'
    dt_std = stdTime(dt_cal)
    # # 根据经纬度获取H8网格行列号 (6001, 6001)
    # [idx_H8Lat, idx_H8Lon] = getH8idx(lat_cal,lon_cal)
    # H8name的日期时间，返回string
    [H8d, H8t] = getH8dtstr(dt_std, lat_cal, lon_cal, Timelist)
    # H8name = 'NC_H08_20'+H8d+'_'+H8t+'_R21_FLDK.06001_06001.nc'
    H8name = '20'+H8d[0:4]+'/'+H8d[4:]+'/'+'NC_H08_20'+H8d+'_'+H8t+'_R21_FLDK.06001_06001.nc'

    return H8name



def readH8data(dt_cal, lat_cal, lon_cal, varnames, path_H8, Timelist):
    # 经度范围转换
    idx = lon_cal < 0
    lon_cal = lon_cal + idx * 360
    df_H8 = pd.DataFrame(columns=varnames)

    for ii in range(len(dt_cal)):
        if (lat_cal<60.02) & (lat_cal>-60.02) & (lon_cal>79.98) & (lon_cal<200.02): # 在H8空间范围内
            name_H8 = getH8name(dt_cal[ii], lat_cal[ii],lon_cal[ii], Timelist) # 获取点对应H8数据名称
            if os.path.isfile(path_H8+name_H8):
                H8 = xr.open_dataset(path_H8+name_H8)
                # 获取对应数据
                # Dataset无法同时用idx检索，只能单独拿出DataArray读取位置
                df_piece = H8[varnames].sel(latitude=[lat_cal[ii]], longitude=[lon_cal[ii]], method="nearest")\
                    .to_dataframe().reset_index().drop(['latitude', 'longitude'], axis=1)
                df_H8 = df_H8.append(df_piece, ignore_index=True)
            else:
                df_H8 = df_H8.append({df_H8.columns[0]: np.nan}, ignore_index=True)
        else:
            df_H8 = df_H8.append({df_H8.columns[0]: np.nan}, ignore_index=True)    
        # df_H8['DAA'] = abs(df_H8['SOA'].values[idx_H8Lat, idx_H8Lat]-df_H8['SAA'])

    return df_H8



#%% 选取一个H8Timelist
pathTimelist = '/home/public/data/H8/L1/201612/01/NC_H08_20161201_0000_R21_FLDK.06001_06001.nc'
H8Timelist = xr.open_dataset(pathTimelist)['Hour']
# e.g.
# H8Hour = H8Timelist.sel(latitude=-60, longitude=-80.000111111, method="nearest")
# H8Hour.values
# t1 = pd.to_datetime(datetime.datetime(2005, 7, 14, 12, 30))+H8Hour # datetime和datetime64需统一
# An example for .mat format.
# path = '/home/fuhy/data/AerosolType/readH81004/H8Timelist.mat'
# mat = scio.loadmat(path)
# H8Timelist=mat['TimeList']
# H8Hour = H8Timelist.sel(latitude=0, longitude=-80.000111111, method="nearest").values
# t1 = datetime.datetime(2005, 7, 14, 12, 30)+H8Hour

#%%
path_CALIPSO1 = '/home/public/data/CALIPSO/APro/2016/2020294055515_53389/'
path_CALIPSO2 = '/home/public/data/CALIPSO/APro/2016/2020294060916_53390/'
name_CALIPSO  = 'CAL_LID_L2_05kmAPro-Standard-V4-20.2016-07-01T02-31-02ZD_Subset.hdf'
CALIPSO = SD(path_CALIPSO2+name_CALIPSO)
# %%
df = pd.DataFrame()
df['dt']  = CALIPSO.select('Profile_UTC_Time')[:,1]
df['lat'] = CALIPSO.select('Latitude')[:,1]
df['lon'] = CALIPSO.select('Longitude')[:,1]
#%%
# Himawari-8
path_H8     = '/home/public/data/H8/L1/'
H8bands = ['tbb_07', 'tbb_08', 'tbb_09', 'tbb_10', 'tbb_11', 'tbb_12', 'tbb_13', 'tbb_14',
    'tbb_15', 'tbb_16','SOZ', 'SAZ']
df_H8 = readH8data(df['dt'], df['lat'], df['lon'], H8bands, path_H8, H8Timelist)

# %% An example of NetCDF indexing in xarray
# H8 = xr.open_dataset('/home/public/data/H8/L1/201612/02/NC_H08_20161202_1450_R21_FLDK.06001_06001.nc')
# H8bands = ['tbb_07', 'tbb_08', 'tbb_09', 'tbb_10', 'tbb_11', 'tbb_12', 'tbb_13', 'tbb_14',
#     'tbb_15', 'tbb_16','SOZ', 'SAZ']
# H8_return_data=H8[H8bands].sel(latitude=[60.01], longitude=[79.99], method="nearest")\
#     .to_dataframe().reset_index().drop(['latitude', 'longitude'], axis=1)#.set_index(['lat','lon']).to_xarray()
# %%
