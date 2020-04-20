#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-20 18:55:38
@Description  : process postvar
'''
import sys
# sys.path.append('/g3/wanghao/Python/Cmodule/gen_info')
sys.path.append('/home/shiyu1997/NMC/Cmodule/')

import numpy as np
import time
from netCDF4 import Dataset
from gen_timelines import gen_timelines
import os
import yaml
from multiprocessing import Pool
from PIL import Image

from plotmap import plot_data


# Main Program
if __name__ == "__main__":
    # read the config file
    curPath       = os.path.dirname(os.path.realpath(__file__))
    cong_yamlPath = os.path.join(curPath+"/config/", "config_xhj.yml")
    if sys.version_info[0] < 3:
        cong = yaml.load(open(cong_yamlPath))
    elif sys.version_info[0] >= 3:
        cong = yaml.load(open(cong_yamlPath), Loader=yaml.FullLoader)

    start_ddate    = cong['start_ddate'] #yyyymnddhh
    end_ddate      = cong['end_ddate']   #yyyymnddhh 
    exdata_dir     = cong['exdata_dir']
    st_vars        = cong['st_vars']
    st_levels      = cong['st_levels']
    make_gif       = cong['make_gif']
    
    # 参数设置
    fcst_step   = 24  # hours
    timelines   = gen_timelines(start_ddate, end_ddate, fcst_step)
    
    time_indices = [0] #[0, 3, 5] # 0d, 3d, 5d
    var = 't'
    var_name = {'t':'Temperature'}

    ncfiles     = ['postvar{}.nc'.format(itime) for itime in timelines]

    # 1.0 读取postvar数据
    print(u'1.0 开始读取postvar数据')
    t0_readpostvar = time.time()
    data_list = []
    for ifile in ncfiles:
        data_list.append(Dataset(exdata_dir+ifile, 'r'))

    t1_readpostvar = time.time()
    print(u'postvar数据读取结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    lat, lon = data_list[0].variables['latitude'][:], data_list[0].variables['longitude'][:]
    # levels   = data_list[0].variables['levels'][:].tolist()
    levels = [1000]

    TLON,TLAT = np.meshgrid(lon,lat)
    
    # 2.0 对指定高度和指定的预报时效做平均
    print(u'2.0 对指定预报面高度列表和指定的预报时效列表做平均')
    t0_readpostvar = time.time()

    tmp_datatable = np.zeros((len(data_list), len(time_indices), len(levels), len(lat), len(lon)), dtype='float32')
    for itime, time_index in enumerate(time_indices):
        for ilevel, level in enumerate(levels):
            level_index = levels.index(level)
            for idata, data in enumerate(data_list):
                tmp_datatable[idata, itime, ilevel, ...] = data.variables[var][time_index, level_index, ...]

    datatable = np.average(tmp_datatable, axis=0)
    
    t1_readpostvar = time.time()
    print(u'对指定预报面高度列表和指定的预报时效列表做平均结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    # begin to plot
    for iarea in ['North_P']: #['Global', 'E_Asia', 'North_P', 'South_P']:
        for itime, time_index in enumerate(time_indices):
            p = Pool(len(levels))
            for ilevel,level in enumerate(levels):
                post_data = datatable[itime, ilevel, ...]

                title    = 'Prediction of {}hr {}hPa {}'.format(itime*24, int(level), var_name[var])
                subtitle = 'Init: {} UTC - {} UTC'.format(start_ddate, end_ddate)
                pic_file = '{}_{}hr_{}hpa.png'.format(iarea, itime*24, int(level))
                p.apply_async(plot_data, args=(post_data, iarea, title, subtitle, pic_file))
                plot_data(post_data, TLON, TLAT, iarea, title, subtitle, pic_file)

            print('Waiting for all subprocesses done...')
            p.close()
            p.join()
            print('All subprocesses done.')
            
    # 合成图片
    if make_gif:
        print('开始合成gif')
        for iarea in ['Global', 'Tropics', 'E_Asia', 'North_P', 'South_P']:
            for itime, time_index in enumerate(time_indices):
                gif_file = './pic/{}_{}hr_pres.gif'.format(iarea, itime*24)
                pic_files = []
                for ilevel,level in enumerate(levels):
                    pic_files.append('./pic/{}_{}hr_{}hpa.png'.format(iarea, itime*24,int(level)))
                    
                imgs = []
                for ipic in pic_files:
                    temp = Image.open(ipic)
                    imgs.append(temp)
                    # os.system('rm {}'.format(ipic))
                imgs[0].save(gif_file,save_all=True,append_images=imgs,duration=2)
