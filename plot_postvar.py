#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-22 12:05:42
@Description  : process postvar
'''
import sys
# sys.path.append('/g3/wanghao/Python/Cmodule/gen_info')
# sys.path.append('/home/shiyu1997/NMC/Cmodule/')
sys.path.append('./Cmodule')
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
    cong_yamlPath = os.path.join(curPath+"/config/", "config.yml")
    if sys.version_info[0] < 3:
        cong = yaml.load(open(cong_yamlPath))
    elif sys.version_info[0] >= 3:
        cong = yaml.load(open(cong_yamlPath), Loader=yaml.FullLoader)

    start_ddate    = cong['start_ddate'] #yyyymnddhh
    end_ddate      = cong['end_ddate']   #yyyymnddhh 
    exdata_dir     = cong['exdata_dir']
    st_vars        = cong['st_vars']
    st_levels      = cong['st_levels']
    fcst           = cong['fcst']
    make_gif       = cong['make_gif']
    clevel_step    = cong['clevel_step']
    variable_name  = cong['variable_name']
    plot_areas     = cong['plot_areas']
    
    # 参数设置
    fcst_step   = 24  # hours
    timelines   = gen_timelines(start_ddate, end_ddate, fcst_step)
    
    ncfiles     = ['postvar{}.nc'.format(itime) for itime in timelines]

    # 1.0 读取postvar数据
    print(u'1.0 开始读取postvar数据')
    t0_readpostvar = time.time()
    data_list = []
    for ifile in ncfiles:
        data_list.append(Dataset(exdata_dir+ifile, 'r'))

    t1_readpostvar = time.time()
    print(u'postvar数据读取结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    lat, lon  = data_list[0].variables['latitude'][:], data_list[0].variables['longitude'][:]
    levels    = data_list[0].variables['levels'][:].tolist()
    time_incr = int(float(data_list[0].variables['times'].incr))
    
    time_indices = [int(i/time_incr) for i in fcst]

    # 2.0 对指定高度和指定的预报时效做平均
    print(u'2.0 对指定预报面高度列表和指定的预报时效列表做平均')
    t0_readpostvar = time.time()

    tmp_datatable = np.zeros((len(data_list), len(st_vars), len(time_indices), len(st_levels), len(lat), len(lon)), dtype='float32')
    
    for ivar, var in enumerate(st_vars):
        for itime, time_index in enumerate(time_indices):
            for ilevel, level in enumerate(st_levels):
                level_index = levels.index(level)
                for idata, data in enumerate(data_list):
                    tmp_datatable[idata, ivar, itime, ilevel, ...] = data.variables[var][time_index, level_index, ...]

    datatable = np.average(tmp_datatable, axis=0)
    
    t1_readpostvar = time.time()
    print(u'对指定预报面高度列表和指定的预报时效列表做平均结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    # begin to plot
    for iarea in plot_areas:
        for itime,time_index in enumerate(time_indices):
            for ivar, var in enumerate(st_vars):
                varname = variable_name[var]
                dlevel = clevel_step[var]

                p = Pool(len(st_levels))
                for ilevel,level in enumerate(st_levels):
                    post_data = datatable[ivar, itime, ilevel, ...]
                        
                    title    = 'Prediction of {}hr {}hPa {}'.format(time_index*time_incr, int(level), varname)
                    subtitle = 'Init: {} UTC - {} UTC'.format(start_ddate, end_ddate)
                    pic_file = '{}_{}hr_{}hpa_{}.png'.format(iarea, time_index*time_incr, int(level), var)
                    p.apply_async(plot_data, args=(post_data, varname, lon, lat, iarea, title, subtitle, pic_file, dlevel))
                    # plot_data(post_data, varname, lon, lat, iarea, title, subtitle, pic_file, dlevel)
                print('Waiting for all subprocesses done...')
                p.close()
                p.join()
                print('All subprocesses done.')

    # 合成图片
    if make_gif:
        print('开始合成gif')
        for iarea in plot_areas:
            for itime, time_index in enumerate(time_indices):
                for ivar, var in enumerate(st_vars):
                    gif_file = './pic/{}_{}hr_{}_pres.gif'.format(iarea, time_index*time_incr, var)
                    pic_files = []
                    for ilevel,level in enumerate(st_levels):
                        pic_files.append('./pic/{}_{}hr_{}hpa_{}.png'.format(iarea, time_index*time_incr,int(level), var))
                    
                    imgs = []
                    for ipic in pic_files:
                        temp = Image.open(ipic)
                        imgs.append(temp)
                        # os.system('rm {}'.format(ipic))
                    imgs[0].save(gif_file,save_all=True,append_images=imgs,duration=2)
