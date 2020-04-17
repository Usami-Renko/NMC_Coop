#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-17 17:11:17
@Description  : process postvar
'''
import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import time
from netCDF4 import Dataset
import os
import re

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

def plot_data(post_data, iarea, time_index, level):
    
    slat,elat,slon,elon = area_region(iarea)

    fcst_range_str = '{}hr'.format(time_index*24)
    level_str = '{}hPa'.format(int(level))
    
    if iarea in ['North_P', 'South_P']:
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
        
    title = 'Prediction of {} {} Temperature'.format(fcst_range_str, level_str)
    subtitle = 'Init: {} UTC - {} UTC'.format(start_datatime, end_datetime)
    add_title(ax_title, title, subtitle)
    
    if iarea == 'Tropics':
        ax_cf = fig.add_axes([0.1, 0.08, 0.85, 0.60])
    else:
        ax_cf = fig.add_axes([0.1, 0.08, 0.85, 0.80])

    if iarea in ['North_P', 'South_P']:
        ax_cb = fig.add_axes([0.1, 0.05, 0.85, 0.03])
    if iarea == 'Tropics':
        ax_cb = fig.add_axes([0.4, 0.05, 0.2, 0.03])
    if iarea == 'E_Asia':
        ax_cb = fig.add_axes([0.1, 0.05, 0.85, 0.03])

    if iarea == 'North_P':
        map = Basemap(projection='npstere', boundinglat=slat, lon_0=0, resolution='i', ax=ax_cf)
        map.drawparallels(np.arange(slat, 90, 10), linewidth=1, dashes=[4, 3])
        map.drawmeridians(np.arange(-180, 181, 20), linewidth=1, dashes=[4, 3], labels=[1, 1, 1, 1])
    elif iarea == 'South_P':
        map = Basemap(projection='spstere', boundinglat=elat, lon_0=0, resolution='i', ax=ax_cf)
        map.drawparallels(np.arange(-90, elat+1, 10), linewidth=1, dashes=[4, 3])
        map.drawmeridians(np.arange(-180, 181, 20), linewidth=1, dashes=[4, 3], labels=[1, 1, 1, 1])
    elif iarea == 'Tropics':
        map = Basemap(projection='cyl',llcrnrlat=slat,urcrnrlat=elat, llcrnrlon=slon, urcrnrlon=elon, resolution='i', ax=ax_cf)
        map.drawparallels(np.arange(slat, elat+1, 20), linewidth=1, dashes=[4, 3], labels=[1, 1, 1, 1])
        map.drawmeridians(np.arange(slon, elon+1, 20), linewidth=1, dashes=[4, 3], labels=[0, 0, 1, 0])
    elif iarea == 'E_Asia':
        map = Basemap(projection='cyl',llcrnrlat=slat,urcrnrlat=elat, llcrnrlon=slon, urcrnrlon=elon, resolution='i', ax=ax_cf)
        map.drawparallels(np.arange(slat, elat+1, 10), linewidth=1, dashes=[4, 3], labels=[1, 0, 0, 0])
        map.drawmeridians(np.arange(slon, elon+1, 10), linewidth=1, dashes=[4, 3], labels=[0, 0, 0, 1])

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
    
    if iarea == 'North_P':
        clevels = np.arange(240, 290, 5)
    if iarea == 'South_P':
        clevels = np.arange(260, 285, 3)
    if iarea == 'Tropics':
        clevels = np.arange(270, 310, 3)
    if iarea == 'E_Asia':
        clevels = np.arange(240, 300, 5)

    CF = map.contourf(x, y, post_data.T, levels=clevels, cmap='jet', origin=origin, extend="both")

    CB = fig.colorbar(CF, cax=ax_cb, orientation='horizontal')
    CB.set_label("Temperature [K]", fontsize=14)

    # ax_cf.set_title()

    plt.savefig('./pic/{}_{}_{}.png'.format(iarea, fcst_range_str, level_str), bbox_inches='tight', dpi=500)
    plt.close()

def glob_dir(datadir, datasuffix):

    regex = '\w*\.{}$'.format(datasuffix)
    
    allfiles = os.listdir(datadir)
    
    datafiles = list()
    timestamps = list()
    for allfile in allfiles:
        if re.search(regex, allfile) is not None:
            datafile = os.path.join(datadir, allfile)
            datafiles.append(datafile)
            timestamps.append(allfile.split('.')[0].strip('postvar'))
    
    print(u'{} *.{} datafiles found under directory {}'.format(len(datafiles), datasuffix, datadir))
    
    timestamps = np.asarray(timestamps, dtype='int')
    global start_datatime, end_datetime
    start_datatime, end_datetime = min(timestamps), max(timestamps)

    return datafiles

if __name__ == "__main__":

    data_dir  = './ex_data/'
    data_suffix = 'nc'
    var = 't'
    
    time_indices = [0, 3, 5] # 0d, 3d, 5d
    levels = [1000, 850]
    
    datafiles = glob_dir(data_dir, data_suffix)

    plt.rcParams['font.family'] = 'serif'

    # 1.0 读取postvar数据
    data_list = list() 
    print(u'1.0 开始读取postvar数据')
    t0_readpostvar = time.time()
    for datafile in datafiles:
        data = Dataset(datafile, 'r')
        data_list.append(data)

    t1_readpostvar = time.time()
    print(u'postvar数据读取结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    lat, lon = data_list[0].variables['latitude'][:], data_list[0].variables['longitude'][:]
    levels = data_list[0].variables['levels'][:].tolist()    
    # print(levels)

    # 2.0 对指定高度和指定的预报时效做平均

    print(u'2.0 对指定预报面高度列表和指定的预报时效列表做平均')
    t0_readpostvar = time.time()
    
    tmp_datatable = np.zeros((len(data_list), len(time_indices), len(levels), len(lat), len(lon)), dtype='float32')

    for itime, time_index in enumerate(time_indices):
        for ilevel, level in enumerate(levels):
            level_index = levels.index(level)
            for idata, data in enumerate(data_list):
                tmp_datatable[idata, itime, ilevel, ...] = data.variables[var][time_index, level_index, ...]
    
    # (times, levels, lats, lons)
    datatable = np.average(tmp_datatable, axis=0)
    
    t1_readpostvar = time.time()
    print(u'对指定预报面高度列表和指定的预报时效列表做平均结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    TLON,TLAT = np.meshgrid(lon,lat)
    
    # begin to plot
    for itime, time_index in enumerate(time_indices):
        for ilevel, level in enumerate(levels):
            
            post_data = datatable[itime, ilevel, ...]

            for iarea in ['North_P','South_P', 'Tropics', 'E_Asia']:
                
                plot_data(post_data, iarea, time_index, level)
        
            exit()
