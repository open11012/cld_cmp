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


def readERApl(field, time, levels, latitude, longitude):
    value = field.loc[time, levels, latitude, longitude].values
    return value


def readERAsl(field, time, latitude, longitude):
    value = field.loc[time, latitude, longitude].values
    return value


filepath = '/home/public/data/ERA5/reanalysis-era5-single-levels/'

for month in range(9, 11):
    num_mon = '%02d' % month
    print('2016' + num_mon + ' in progress...')
    AVDname = '/home/fuhy/data/CALIPSO/CALIPSO_AVD_2016_' + num_mon + '.csv'
    # AVDname = '/Users/fu/数据/CALIPSO/AVD_2016/CALIPSO_AVD_2016_' + num_mon + '.csv'
    data = pd.read_csv(AVDname, usecols=['Latitude_2', 'Longitude_2', 'Profile_UTC_Time_2'])
    print('In preprocess...')
    print('Part 1/3 preprocess:')
    data['dt_ERA'] = data.Profile_UTC_Time_2.apply(round_hour)  # 转换为ERA-5对应时间
    print('Part 2/3 preprocess:')
    data['lat_ERA'] = data.Latitude_2.apply(round_lat)  # 转换为ERA-5对应纬度
    print('Part 3/3 preprocess:')
    data['lon_ERA'] = data.Longitude_2.apply(round_lon)  # 转换为ERA-5对应纬度

    # single levels
    # surface_pressure
    dataset = xr.open_dataset(filepath + '2016_surface_pressure.nc')
    var1 = dataset['sp']
    print('Part 1/3 progress:')
    # tqdm.pandas(desc='Part 1/3 progress')
    data['sp'] = data.apply(lambda x: readERAsl(var1, x['dt_ERA'], x['lat_ERA'], x['lon_ERA']),
                            axis=1)
    # tcwv and skt
    dataset = xr.open_dataset(filepath + '2016_tcwv_skt.nc')
    var2 = dataset['skt']
    print('Part 2/3 progress:')
    # tqdm.pandas(desc='Part 2/3 progress')
    data['skt'] = data.apply(lambda x: readERAsl(var2, x['dt_ERA'], x['lat_ERA'], x['lon_ERA']),
                             axis=1)
    var3 = dataset['tcwv']
    print('Part 3/3 progress:')
    # tqdm.pandas(desc='Part 3/3 progress')
    data['tcwv'] = data.apply(lambda x: readERAsl(var3, x['dt_ERA'], x['lat_ERA'], x['lon_ERA']),
                              axis=1)
    filename = 'ERAsl_' + num_mon + '.csv'
    data.to_csv(filename)
