#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-20 18:07:16
@Description  : process postvar
'''
import sys
# sys.path.append('/g3/wanghao/Python/Cmodule/gen_info')
sys.path.append('/home/shiyu1997/NMC/Cmodule/')

import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import time
from netCDF4 import Dataset
import matplotlib.path as mpath
from gen_timelines import gen_timelines
import os
import yaml
from multiprocessing import Pool
from PIL import Image

def area_region(area):
    if area == 'South_P':
        rlat, qlat = -90., -60.
        rlon, qlon =   0., 360.
    if area  == 'North_P':
        rlat, qlat =  60.,  90.
        rlon, qlon =   0., 360.
    if area == 'E_Asia':
        rlat, qlat =  10.,  70.
        rlon, qlon =  60., 150.
    if area == 'Tropics':
        rlat, qlat = -20.,  20.
        rlon, qlon =   0., 360.
    if area == 'Global':
        rlat, qlat = -90., 90.
        rlon, qlon =   0., 360.

    return rlat, qlat, rlon, qlon

def tick_lats(map, lat_labels, ax, xoffset=250000, yoffset=0, rl='r'):

    for lat_label in lat_labels:
        lon, lat = lat_label[0], lat_label[1]
        text = '{}'.format(abs(lat)) + r'$^\circ$' + ('N' if lat > 0 else 'S')
        x, y = map(lon, lat)
        
        if rl == 'r':
            x += xoffset
        elif rl == 'l':
            x -= xoffset
            
        ax.text(x, y+yoffset, text, fontsize=11, ha='center', va='center')

def add_title(ax, title, subtitle):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.set_xticks([])
    ax.set_yticks([])

    ax.text(0.5, 0.50, title, fontsize=25, ha='center', va='center')
    ax.text(0.5, 0.00, subtitle, fontsize=16, ha='center', va='center')

def plot_data(post_data, iarea, title, subtitle, pic_file):
    
    slat,elat,slon,elon = area_region(iarea)
    
    if iarea == 'Global':
        figsize = (12,8.0)
    elif iarea in ['North_P', 'South_P']:
        figsize = (10,12)
    elif iarea == 'Tropics':
        figsize = (20,4.0)
    elif iarea == 'E_Asia':
        figsize = (10,7.7)

    fig = plt.figure(figsize=figsize)
    
    if iarea == 'Tropics':
        ax_title = fig.add_axes([0.1, 0.80, 0.82, 0.18])
    else:
        ax_title = fig.add_axes([0.1, 0.90, 0.82, 0.08])
    
    add_title(ax_title, title, subtitle)

    if iarea == 'Tropics':
        ax_cf = fig.add_axes([0.1, 0.10, 0.85, 0.60])
    elif iarea == 'Global':
        ax_cf = fig.add_axes([0.1, 0.12, 0.85, 0.80])
    else:
        ax_cf = fig.add_axes([0.1, 0.10, 0.85, 0.80])
    
    if iarea == 'Global':
        ax_cb = fig.add_axes([0.1, 0.12, 0.85, 0.03])
    if iarea in ['North_P', 'South_P']:
        ax_cb = fig.add_axes([0.1, 0.05, 0.85, 0.03])
    if iarea == 'Tropics':
        ax_cb = fig.add_axes([0.4, 0.05, 0.2, 0.03])
    if iarea == 'E_Asia':
        ax_cb = fig.add_axes([0.1, 0.05, 0.85, 0.03])

    if iarea == 'Global':
        map = Basemap(projection='cyl', llcrnrlat=slat, urcrnrlat=elat, llcrnrlon=slon, urcrnrlon=elon, resolution='l', ax=ax_cf)
        map.drawparallels(np.arange(slat, elat+1, 30), linewidth=1, dashes=[4, 3], labels=[1, 0, 0, 0])
        map.drawmeridians(np.arange(slon, elon+1, 60), linewidth=1, dashes=[4, 3], labels=[0, 0, 0, 1])
    elif iarea == 'E_Asia':
        map = Basemap(projection='cyl',llcrnrlat=slat,urcrnrlat=elat, llcrnrlon=slon, urcrnrlon=elon, resolution='l', ax=ax_cf)
        map.drawparallels(np.arange(slat, elat+1, 20), linewidth=1, dashes=[4, 3], labels=[1, 0, 0, 0])
        map.drawmeridians(np.arange(slon, elon+1, 20), linewidth=1, dashes=[4, 3], labels=[0, 0, 0, 1])
    elif iarea == 'North_P':
        map = Basemap(projection='npstere', boundinglat=slat, lon_0=0, resolution='l', ax=ax_cf)
        map.drawparallels(np.arange(slat, 90, 10), linewidth=1, dashes=[4, 3])
        map.drawmeridians(np.arange(-180, 181, 20), linewidth=1, dashes=[4, 3], labels=[1, 1, 1, 1])
    elif iarea == 'South_P':
        map = Basemap(projection='spstere', boundinglat=elat, lon_0=0, resolution='l', ax=ax_cf)
        map.drawparallels(np.arange(-90,  elat+1, 10), linewidth=1, dashes=[4, 3])
        map.drawmeridians(np.arange(-180, 181, 20), linewidth=1, dashes=[4, 3], labels=[1, 1, 1, 1])
    elif iarea == 'Tropics':
        map = Basemap(projection='cyl',llcrnrlat=slat,urcrnrlat=elat, llcrnrlon=slon, urcrnrlon=elon, resolution='l', ax=ax_cf)
        map.drawparallels(np.arange(slat, elat+1, 20), linewidth=1, dashes=[4, 3], labels=[1, 1, 1, 1])
        map.drawmeridians(np.arange(slon, elon+1, 20), linewidth=1, dashes=[4, 3], labels=[0, 0, 1, 0])

    map.drawcoastlines()
    
    # tick latitude labels manually
    if iarea == 'North_P': 
        lat_labels= [(120, 60), (120, 70), (120, 80), (300, 60), (300, 70), (300, 80)]
    elif iarea == 'South_P':
        lat_labels= [(120, -60), (120, -70), (120, -80), (300, -60), (300, -70), (300, -80)]

    if iarea in ['North_P', 'South_P']:
        tick_lats(map, lat_labels, ax_cf)

    if iarea == 'North_P':
        tick_lats(map, [(90, 60)], ax_cf, rl='r')
        tick_lats(map, [(270, 60)], ax_cf, rl='l')
    elif iarea == 'South_P':
        tick_lats(map, [(90, -60)], ax_cf, rl='r')
        tick_lats(map, [(270, -60)], ax_cf, rl='l')
    
    x, y = map(TLON.T, TLAT.T)

    origin = 'lower'
   
    if iarea == 'Global':
        clevels = np.arange(240, 300, 5)
    if iarea == 'E_Asia':
        clevels = np.arange(240, 300, 5)
    if iarea == 'North_P':
        clevels = np.arange(240, 290, 5)
    if iarea == 'South_P':
        clevels = np.arange(260, 285, 3)
    if iarea == 'Tropics':
        clevels = np.arange(270, 310, 3)

    CF = map.contourf(x, y, post_data.T, levels=clevels, cmap='jet', origin=origin, extend="both")
    # CF = map.contourf(x, y, post_data.T, cmap='jet', origin=origin, extend="both")
    
    CB = fig.colorbar(CF, cax=ax_cb, orientation='horizontal')
    CB.set_label("Temperature [K]", fontsize=14)

    plt.savefig('./pic/{}'.format(pic_file), bbox_inches='tight', dpi=500)
    plt.close()

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

    plt.rcParams['font.family'] = 'serif'
    
    # 参数设置
    fcst_step   = 24  # hours
    timelines   = gen_timelines(start_ddate, end_ddate, fcst_step)
    
    time_indices = [0, 3, 5] #[0, 3, 5] # 0d, 3d, 5d
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
    levels   = data_list[0].variables['levels'][:].tolist()
    # levels = [1000]

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
    for iarea in ['Global', 'E_Asia', 'North_P', 'South_P', 'Tropics']: #['Global', 'E_Asia', 'North_P', 'South_P']:
        for itime, time_index in enumerate(time_indices):
            p = Pool(len(levels))
            for ilevel,level in enumerate(levels):
                post_data = datatable[itime, ilevel, ...]

                title    = 'Prediction of {}hr {}hPa {}'.format(itime*24, int(level), var_name[var])
                subtitle = 'Init: {} UTC - {} UTC'.format(start_ddate, end_ddate)
                pic_file = '{}_{}hr_{}hpa.png'.format(iarea, itime*24, int(level))
                p.apply_async(plot_data, args=(post_data, iarea, title, subtitle, pic_file))
                plot_data(post_data, iarea, title, subtitle, pic_file)

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
