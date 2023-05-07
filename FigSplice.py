# %%

import os
import cv2
import torch
import xarray as xr
from pathlib import Path
from   netCDF4 import Dataset
import numpy as np
import random
from PIL import Image
from torch.utils import data

# %% [markdown]
# # 按时间筛选并拼接

# %%
root = '/ai/open11012/zhou/cld/cld_convlstm_seq/test_images/Unet_convlstm_disk_f6s3_epoch3_905T/test_results/'
hours = ["00", "01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23"]
minus = ['00','30']
img_item = []
for h in hours:
    hour_img_00 = '20160730_' + h + '00'
    hour_img_30 = '20160730_' + h + '30'
    img_list_00  = [root+'/'+ f for f in os.listdir(root) if f.startswith(hour_img_00)] #筛选卫星天顶角60度以内的数据
    img_list_30  = [root+'/'+ f for f in os.listdir(root) if f.startswith(hour_img_30) ] #筛选卫星天顶角60度以内的数据
    img_list_30.sort()
    print(len(img_list_30))
    if len(img_list_30)>1:
        img_item.append(img_list_30)
# img_list.sort()

# %%
path_data = '/ai/open11012/zhou/cld/cld_convlstm_seq/test_images/Unet_convlstm_disk_f6s3_epoch3_905T/test_results/'


# %%
os.listdir(root)


