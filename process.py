#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-14 20:14:42
@Description  : process postvar
'''
import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import time
from netCDF4 import Dataset
import matplotlib.path as mpath
import cartopy.crs as ccrs

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

def plot_data(post_data, iarea):
    
    slat,elat,slon,elon = area_region(iarea)
    
    if iarea in ['North_P', 'South_P']:
        figsize = (10,10)
    elif iarea == 'Tropics':
        figsize = (20,2.5)
    elif iarea == 'E_Asia':
        figsize = (10,7)

    fig = plt.figure(figsize=figsize)

    ax_cf = fig.add_axes([0.1, 0.12, 0.85, 0.85])
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
        map.drawparallels(np.arange(-90, elat, 10), linewidth=1, dashes=[4, 3])
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

    plt.savefig('./pic/{}.png'.format(iarea), bbox_inches='tight', dpi=500)
    plt.close()


if __name__ == "__main__":

    data_dir  = './ex_data/'
    ctlfiles  = ['postvar2016010112.nc','postvar2016010212.nc']
    fili      = ['fili0','fili1']
    data_filenames = ['pdata0','pdata1']

    # 1.0 读取postvar数据
    print(u'1.0 开始读取postvar数据')
    t0_readpostvar = time.time()
    for ifile,idata in zip(ctlfiles, data_filenames):
        locals()[idata] = Dataset(data_dir+ifile, 'r')
        # print(locals()[idata])

    t1_readpostvar = time.time()
    print(u'postvar数据读取结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    lat, lon = pdata0.variables['latitude'][:],pdata0.variables['longitude'][:]
    # print(len(lat), len(lon))

    TLON,TLAT = np.meshgrid(lon,lat)
    # print(np.shape(lats))
    levels = pdata0.variables['levels'][:].tolist()
    print(levels)

    # assign time and level
    it = 0
    ilevel = 1000

    index = levels.index(ilevel)
    post_data = (pdata0.variables['t'][it,index,:,:] + pdata1.variables['t'][it,index,:,:])/2

    # begin to plot
    for iarea in ['North_P','South_P', 'Tropics', 'E_Asia']:
        plot_data(post_data, iarea)
