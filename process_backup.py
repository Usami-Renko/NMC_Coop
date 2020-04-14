#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: wanghao
@LastEditTime: 2020-04-14 10:48:23
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

data_dir  = './ex_data/'
ctlfiles  = ['postvar2016010112.nc','postvar2016010212.nc']
fili      = ['fili0','fili1']
data_filenames = ['pdata0','pdata1']

# 1.0 读取postvar数据
print(u'1.0 开始读取postvar数据')
t0_readpostvar = time.time()
for ifile,idata in zip(ctlfiles, data_filenames):
    locals()[idata] = Dataset(data_dir+ifile, 'r')
    print(locals()[idata])

t1_readpostvar = time.time()
print(u'postvar数据读取结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

lat, lon = pdata0.variables['latitude'][:],pdata0.variables['longitude'][:]
# print(len(lat), len(lon))

lons,lats = np.meshgrid(lon,lat)
# print(np.shape(lats))
levels = pdata0.variables['levels'][:].tolist()
print(levels)

for it in [0,1,3]:
    for ilevel in [1000.,850]:
        index = levels.index(ilevel)
        post_data = (pdata0.variables['t'][it,index,:,:] + pdata1.variables['t'][it,index,:,:])/2
        # print(post_data)
        # exit()

        # begin to plot
        for iarea in ['South_P','North_P','E_Asia','Tropics']:
            slat,elat,slon,elon = area_region(iarea)
            
            fig = plt.figure(figsize=(12,6))
            proj =ccrs.NorthPolarStereo(central_longitude=-90.)
            leftlon, rightlon, lowerlat, upperlat = (slon,elon,slat,elat)
            img_extent = [-180., 180., lowerlat, upperlat]


            #######以下为网格线的参数######
            theta = np.linspace(0, 2*np.pi, 100)
            center, radius = [0.5, 0.5], 0.5
            verts = np.vstack([np.sin(theta), np.cos(theta)]).T
            circle = mpath.Path(verts * radius + center)
            
            ax = fig.add_axes([0.1, 0.1, 0.5, 0.5],projection = ccrs.NorthPolarStereo())
            # ax.set_extent(img_extent, ccrs.PlateCarree())

            ax.gridlines()
            # ax.set_extent(img_extent, ccrs.PlateCarree())
            # ax.set_boundary(circle)
            # ax.set_boundary(circle, transform=ax.transAxes)

            shaded = ax.contourf(lons,lats,post_data, zorder=0, extend = 'both',transform=ccrs.PlateCarree(), cmap='jet')
            
            # ax.text(lons, lats, r'0$^\circ$',fontsize=14, horizontalalignment='center',verticalalignment='center')
            position=fig.add_axes([0.38, 0.04, 0.35, 0.025])
            fig.colorbar(shaded,cax=position,orientation='horizontal',format='%.1f')

            # plt.savefig('./pic/{}.png'.format(iarea), bbox_inches='tight')
            plt.show()
            exit()
