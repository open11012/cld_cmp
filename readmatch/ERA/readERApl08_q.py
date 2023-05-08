# fuhaoyang
# 2022/8/8 15:16
import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
import netCDF4 as nc
import xarray as xr
import datetime
from tqdm import tqdm
import csv
from netCDF4 import num2date, date2num, date2index


def round_hour(dt):
    # Rounds to the nearest hour by adding a timedelta hour if minute >= 30
    date = np.floor(dt)
    time = dt - date
    t = datetime.datetime.strptime('20' + str(date)[0:6], '%Y%m%d') + timedelta(days=time)
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour)
            + timedelta(hours=t.minute // 30))  # 向下取整


def round_lat(ll):
    ll = np.round(ll / 0.25) * 0.25
    return ll


def round_lon(ll):
    idx = ll < 0
    ll = ll + idx * 360
    ll = np.round(ll / 0.25) * 0.25
    return ll


# pressure-levels:
#   format:
#       variable(time, level, latitude, longitude)
#   variables:
#       o3:     ozone_mass_mixing_ratio
#       q:      specific_humidity
#       t:      temperature
#   'pressure_level': [
#                     '1', '2', '3',
#                     '5', '7', '10',
#                     '20', '30', '50',
#                     '70', '100', '125',
#                     '150', '175', '200',
#                     '225', '250', '300',
#                     '350', '400', '450',
#                     '500', '550', '600',
#                     '650', '700', '750',
#                     '775', '800', '825',
#                     '850', '875', '900',
#                     '925', '950', '975',
#                     '1000',
#                     ]
# single-levels:
#   format:
#       variable(time, latitude, longitude)
#   variables:
#       sp:     surface_pressure
#       skt:    skin_temperature
#       tcwv:
# def readERApl(fieldname, field, df, time, latitude, longitude):
#     """
#     desc: read ERA column in loop, 效率低，弃用
#     param
#     return
#     """
#     pls = [
#         '1', '2', '3',
#         '5', '7', '10',
#         '20', '30', '50',
#         '70', '100', '125',
#         '150', '175', '200',
#         '225', '250', '300',
#         '350', '400', '450',
#         '500', '550', '600',
#         '650', '700', '750',
#         '775', '800', '825',
#         '850', '875', '900',
#         '925', '950', '975',
#         '1000',
#     ]
#     # 循环效率低
#     for pl in pls:
#         df[fieldname + '_' + pl] = field.loc[time, pl, latitude, longitude].values
#     return df


# def readERAsl(field, time, latitude, longitude):
#     value = field.loc[time, latitude, longitude].values
#     return value


filepath = '/home/public/data/ERA5/reanalysis-era5-pressure-levels/'

# pressure levels
files = ['specific_humidity_2016']
varnames = ['q']
pressure_level = [
    '1', '2', '3',
    '5', '7', '10',
    '20', '30', '50',
    '70', '100', '125',
    '150', '175', '200',
    '225', '250', '300',
    '350', '400', '450',
    '500', '550', '600',
    '650', '700', '750',
    '775', '800', '825',
    '850', '875', '900',
    '925', '950', '975',
    '1000',
]

# 各月
for month in range(8, 9):
    num_mon = '%02d' % month
    AVDname = '/home/fuhy/data/CALIPSO/CALIPSO_AVD_2016_' + num_mon + '.csv'
    # AVDname = '/Users/fu/数据/CALIPSO/AVD_2016/CALIPSO_AVD_2016_' + num_mon + '.csv'
    data = pd.read_csv(AVDname, usecols=['Latitude_2', 'Longitude_2', 'Profile_UTC_Time_2'])
    print('Processing ' + num_mon + '...')
    print('Preprocessing...')
    print('Part 1/3...')
    data['dt_ERA'] = data.Profile_UTC_Time_2.apply(round_hour)  # 转换为ERA-5对应时间
    print('Part 2/3...')
    data['lat_ERA'] = data.Latitude_2.apply(round_lat)  # 转换为ERA-5对应纬度
    print('Part 3/3...')
    data['lon_ERA'] = data.Longitude_2.apply(round_lon)  # 转换为ERA-5对应纬度
    # 各变量
    for i in range(len(files)):
        filename = files[i] + num_mon + '.nc'
        dataset = xr.open_dataset(filepath + filename)
        varname = varnames[i]
        var = dataset[varname]
        df = pd.DataFrame(columns=[varname + '_' + s for s in pressure_level])
        print('Processing ' + varname + '...')
        n = 0
        for ii in tqdm(range(len(data)), desc=num_mon + ' ' + varname):
            dt = data['dt_ERA'].iloc[n]
            lat = data['lat_ERA'].iloc[n]
            lon = data['lon_ERA'].iloc[n]
            if pd.to_datetime(dt).month == month:
                df.loc[n] = var.loc[dt, :, lat, lon].values
            else:
                num_mon1 = '%02d' % pd.to_datetime(dt).month
                filename1 = files[i] + num_mon1 + '.nc'
                dataset1 = xr.open_dataset(filepath + filename1)
                var1 = dataset1[varname]
                df.loc[n] = var1.loc[dt, :, lat, lon].values
            n = n+1
        data_out = pd.concat([data, df], axis=1)
        filename = 'ERApl_' + varname + num_mon + '.csv'
        data_out.to_csv(filename)
