# fuhaoyang
# 2023/3/6 10:
import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
import xarray as xr
import datetime
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


def stdTime(dt_cal):
    # CALIPSO Profile_UTC_Time转换为'yyyyMMddHHmmss'
    # 因为CALIPSO时间为string，array转换位置不对，因此单独对一个string转换
    date = np.floor(dt_cal)
    time = dt_cal - date
    dt_std = datetime.datetime.strptime('20' + str(date)[0:6], '%Y%m%d') + timedelta(days=time)

    return dt_std



def readERAsl(lat_cal, lon_cal, dt_cal, varnames, pathnameERA):
    # 输入lat_cal, lon_cal, dt_cal可为序列

    # 经度范围转换
    idx = lon_cal < 0
    lon_cal = lon_cal + idx * 360
    df_ERA = pd.DataFrame(columns=varnames)
    df_nan = pd.DataFrame([np.nan], columns=[varnames[0]])

    for ii in range(len(dt_cal)):
    ####################################################################################################################
     # 在H8空间范围内:
        if (lat_cal[ii]<60.02) & (lat_cal[ii]>-60.02) & (lon_cal[ii]>79.98) & (lon_cal[ii]<200.02):
    ####################################################################################################################
            # nameERA = getERAslname(dt_cal[ii], lat_cal[ii], lon_cal[ii]) # 获取点对应H8数据名称
            if os.path.isfile(pathnameERA):
                ERA = xr.open_dataset(pathnameERA)
                # 获取对应数据
                # Dataset无法同时用idx检索，只能单独拿出DataArray读取位置
                dt_std = stdTime(dt_cal[ii]) # CALIPSO时间转换为标准时间
                df_piece = ERA[varnames].sel(latitude=[lat_cal[ii]], longitude=[lon_cal[ii]], time=[dt_std],\
                                             method="nearest")\
                    .to_dataframe().reset_index().drop(['latitude', 'longitude', 'time'], axis=1)
                df_ERA = pd.concat([df_ERA, df_piece], ignore_index=True)
            else:
                df_ERA = pd.concat([df_ERA, df_nan], ignore_index=True)
        else:
            df_ERA = pd.concat([df_ERA, df_nan], ignore_index=True)
        # df_H8['DAA'] = abs(df_H8['SOA'].values[idx_H8Lat, idx_H8Lat]-df_H8['SAA'])

    return df_ERA


def readERApl(lat_cal, lon_cal, dt_cal, varname, plevels, pathERA, dictERA):
    # 输入的varnames与pathnameERA配套
    # 经度范围转换
    idx = lon_cal < 0
    lon_cal = lon_cal + idx * 360
    # df_ERA = pd.DataFrame(columns=[varname+'_' + int(pl) for pl in plevels])
    varnames = np.char.add([varname+'_'], np.array(plevels, dtype = np.str_)) # column names (varname + plevels)
    df_ERA = pd.DataFrame(columns=varnames) # empty DataFrame with columns
    df_nan = pd.DataFrame([np.nan], columns=[varnames[0]])

    for ii in range(len(dt_cal)):
        if (lat_cal[ii]<60.02) & (lat_cal[ii]>-60.02) & (lon_cal[ii]>79.98) & (lon_cal[ii]<200.02): # 在H8空间范围内
            # nameERA = getERAslname(dt_cal[ii], lat_cal[ii], lon_cal[ii]) # 获取点对应H8数据名称
            dt_std = stdTime(dt_cal[ii]) # CALIPSO时间转换为标准时间，通过时间确定ERApl文件名
            nameERA = getERAplname(dt_std, varname, dictERA)
            pathnameERA = pathERA+nameERA
            if os.path.isfile(pathnameERA):
                ERA = xr.open_dataset(pathnameERA)
                # 获取对应数据
                # Dataset无法同时用idx检索，只能单独拿出DataArray读取位置
                df_piece = ERA[varname].sel(latitude=[lat_cal[ii]], longitude=[lon_cal[ii]], level=plevels, time=[dt_std],\
                                             method="nearest")\
                    .to_dataframe().reset_index().drop(['latitude', 'longitude', 'time'], axis=1)
                df_piece = df_piece[varname].to_frame().T
                df_piece.columns = varnames
                df_ERA = pd.concat([df_ERA, df_piece], ignore_index=True)
            else:
                df_ERA = pd.concat([df_ERA, df_nan], ignore_index=True)
        else:
            df_ERA = pd.concat([df_ERA, df_nan], ignore_index=True)
        # df_H8['DAA'] = abs(df_H8['SOA'].values[idx_H8Lat, idx_H8Lat]-df_H8['SAA'])
    
    return df_ERA


def getERAplname(dt_std, varname, dictERA):

    num_year = '%04d' % dt_std.year
    num_mon  = '%02d' % dt_std.month
    filename = dictERA[varname] + num_year + num_mon + '.nc'

    return filename