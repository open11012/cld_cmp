# fuhaoyang
# 2022/8/17 14:31
import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
import datetime
from tqdm import tqdm
from multiprocessing.dummy import Pool as ThreadPool


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


bands = ['Emis_20', 'Emis_22', 'Emis_23', 'Emis_29', 'Emis_31', 'Emis_32']
months = [1, 4, 8, 11]
num_year = '%04d' % 2017


# 各月
# for month in months:
def process(month):
    num_mon = '%02d' % month
    AVDname = '/home/fuhy/data/CALIPSO/AVD/2017/CALIPSO_AVD_'+num_year+'_' + num_mon + '.csv'
    data = pd.read_csv(AVDname, usecols=['Latitude_2', 'Longitude_2', 'Profile_UTC_Time_2'])
    print('Processing ' + num_mon + '...')
    # print('Preprocessing...')
    # print('Part 1/3...')
    data['MODDoY'] = data.Profile_UTC_Time_2.apply(getMODdoy)  # 转换为对应MOD11 DoY
    # print('Part 2/3...')
    data['idx_lat'] = data.Latitude_2.apply(getMODlat)  # 转换为MOD11对应网格
    # print('Part 3/3...')
    idx_lon = data.Longitude_2.apply(getMODlon)  # 转换为MOD11对应网格
    idx_lon[idx_lon == 7200] = 0
    data['idx_lon'] = idx_lon
    doy = data['MODDoY'][0]
    doystr = '%03d' % doy
    MOD11all = np.load('/home/fuhy/data/SWC/data/MOD11_origin_itp/MOD11C2.A'+num_year+doystr+'.061.itp.npy')
    df = pd.DataFrame(columns=['MOD11_'+s for s in bands])
    n = 0
    for ii in tqdm(range(len(data)), desc=num_mon):
        idx1 = data['idx_lat'].iloc[n]
        idx2 = data['idx_lon'].iloc[n]
        if data['MODDoY'][n] == doy:
            df.loc[n] = MOD11all[idx1, idx2, :]
        else:
            doy = data['MODDoY'][n]
            doystr = '%03d' % data['MODDoY'][n]
            MOD11all = np.load('/home/fuhy/data/SWC/data/MOD11_origin_itp/MOD11C2.A'+num_year+doystr+'.061.itp.npy')
            df.loc[n] = MOD11all[idx1, idx2, :]
        n = n+1
    data_out = pd.concat([data, df], axis=1)
    savepath = '/home/fuhy/data/SWC/data/MOD11_Emis/'
    filename = 'MOD11_Emis_'+num_year + num_mon + '.csv'

    data_out.to_csv(savepath+filename)


pool = ThreadPool()
pool.map(process, months)
pool.close()
pool.join()