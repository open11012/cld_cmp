# %%
import os
import cv2
import torch
import xarray as xr
from pathlib import Path
from   netCDF4 import Dataset
# %%
import numpy as np
import random
from PIL import Image
from torch.utils import data
# %%
'''
筛选卫星天顶角小于60度的数据
'''
root = "/ai/open11012/zhou/datasets/H8/H8label2016_npy"
img_list  = [root+'/'+ f for f in os.listdir(root) if (f.endswith('npz') and (int(f[14:16])>6 and int(f[14:16])<24 ) and (int(f[17:19])>6 and int(f[17:19])<24))] #筛选卫星天顶角60度以内的数据
img_list.sort()

# y = int(f.split('/')[-1][14:16])
# x = int(f.split('/')[-1][17:19])

# %%
'''
将不同位置数据放入不同txt
'''
path_txt = "/ai/open11012/zhou/cld/cld_convlstm_seq/dataset/H8/"
for file in img_list:
    idy = file.split('/')[-1][14:16] # 行号
    idx = file.split('/')[-1][17:19] # 列号
    ful_path = path_txt + idy + '_' + idx+ '.txt'
    file_now = open(ful_path, 'a')
    file_now.write(file  + '\n')
    file_now.close()
 