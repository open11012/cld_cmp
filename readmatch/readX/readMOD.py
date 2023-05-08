# fuhaoyang
# 2023/3/14 20:00
import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
import datetime
from tqdm import tqdm

import os


def stdTime(dt_cal):
    # CALIPSO Profile_UTC_Time转换为'yyyyMMddHHmmss'
    # 因为CALIPSO时间为string，array转换位置不对，因此单独对一个string转换
    date = np.floor(dt_cal)
    time = dt_cal - date
    dt_std = datetime.datetime.strptime('20' + str(date)[0:6], '%Y%m%d') + timedelta(days=time)

    return dt_std


def getMODdoy(dt):
    date = np.floor(dt)
    time = dt - date
    t = datetime.datetime.strptime('20' + str(date)[0:6], '%Y%m%d') + timedelta(days=time)
    doy = (t - datetime.datetime(t.year, 1, 1)).days//8*8 + 1
    return doy


def getMODlat(lat):
    # 根据经纬度找到对应MOD11网格点
    # From top to bottom:    90 : 0.05 : -89.95
    # From left to right:  -180 : 0.05 : 179.95
    idx_lat = round((90-lat)/0.05)
    return idx_lat


def getMODlon(lon):
    # 根据经纬度找到对应MOD11网格点
    # From top to bottom:    90 : 0.05 : -89.95
    # From left to right:  -180 : 0.05 : 179.95
    idx_lon = round((lon+180)/0.05)
    return idx_lon



def readMOD11(lat_cal, lon_cal, dt_cal, pathMOD):

    # 不需要对经度范围转换

    # MOD11数据为.npy格式，
    # 样本时间连续，为避免频繁内存I/O耗时，预先读入第一个样本对应的MOD11数据，
    # 后续时间doy变化再读如新mod npy数据
    # 转换为MOD11对应网格
    idx_lat = getMODlat(lat_cal)
    idx_lon = getMODlon(lon_cal)
    idx_lon[idx_lon == 7200] = 0
    # 转换为对应MOD11 DoY 
    dt_std0 = stdTime(dt_cal[0])
    num_year0 = '%04d' % dt_std0.year
    doy0 = getMODdoy(dt_cal[0]) # Convert time from CALIPSO UTC format to MODIS day of year
    doy0str = '%03d' % doy0
    nameMOD = 'MOD11C2.A'+num_year0+doy0str+'.061.itp.npy'
    pathnameMOD = pathMOD + nameMOD
    MOD11all = np.load(pathnameMOD)
    bands = ['Emis_20', 'Emis_22', 'Emis_23', 'Emis_29', 'Emis_31', 'Emis_32']
    varnames = ['MOD11_' + s for s in bands]
    df_MOD11 = pd.DataFrame(columns=varnames)
    df_nan = pd.DataFrame([np.nan], columns=[varnames[0]])

    for ii in range(len(dt_cal)):
    # for ii in tqdm(range(len(dt_cal)), desc='MOD matching for 20'+str(dt_cal[0])):

        # 转换为对应MOD11 DoY 
        dt_std = stdTime(dt_cal[ii])
        num_year = '%04d' % dt_std.year
        doy = getMODdoy(dt_cal[ii]) # Convert time from CALIPSO UTC format to MODIS day of year
        
        if os.path.isfile(pathnameMOD):
            if doy == doy0:
                df_piece = pd.DataFrame([MOD11all[int(idx_lat[ii]), int(idx_lon[ii]), :]], columns=varnames)
                df_MOD11 = pd.concat([df_MOD11, df_piece], ignore_index=True)
            else:
                doy0 = doy
                doystr = '%03d' % doy
                num_year = '%04d' % dt_std.year
                nameMOD = 'MOD11C2.A'+num_year+doystr+'.061.itp.npy'
                pathnameMOD = pathMOD + nameMOD
                MOD11all = np.load(pathnameMOD)
                df_piece = pd.DataFrame([MOD11all[int(idx_lat[ii]), int(idx_lon[ii]), :]], columns=varnames)
                df_MOD11 = pd.concat([df_MOD11, df_piece], ignore_index=True)
        else:
            df_MOD11 = pd.concat([df_MOD11, df_nan], ignore_index=True)
        # df_H8['DAA'] = abs(df_H8['SOA'].values[idx_H8Lat, idx_H8Lat]-df_H8['SAA'])
    
    return df_MOD11