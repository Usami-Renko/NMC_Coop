#!/usr/bin/env python
# coding=UTF-8

'''
@Description: plot the countoured map of a given variable
@Author: Hejun Xie
@Date: 2020-04-20 18:46:33
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-27 20:16:28
'''

from mpl_toolkits.basemap import Basemap
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from numpy import ma

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
    if area == 'China':
        rlat, qlat =  10.,  55.
        rlon, qlon =  70., 140.

    return rlat, qlat, rlon, qlon

def float_index(float_ls, myfloat):
    if myfloat < float_ls[0]:
        return 0
    for ifloat, float in enumerate(float_ls):
        if ifloat < len(float_ls) - 1 and float <= myfloat <= float_ls[ifloat+1] :
            return ifloat
    return len(float_ls) - 1

def _tick_lats(map, lat_labels, ax, xoffset=250000, yoffset=0, rl='r'):

    for lat_label in lat_labels:
        lon, lat = lat_label[0], lat_label[1]
        text = '{}'.format(abs(lat)) + r'$^\circ$' + ('N' if lat > 0 else 'S')
        x, y = map(lon, lat)
        
        if rl == 'r':
            x += xoffset
        elif rl == 'l':
            x -= xoffset
            
        ax.text(x, y+yoffset, text, fontsize=11, ha='center', va='center')

def _add_title(ax, title, subtitle):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.set_xticks([])
    ax.set_yticks([])

    ax.text(0.5, 0.50, title, fontsize=22, ha='center', va='center')
    ax.text(0.5, 0.00, subtitle, fontsize=16, ha='center', va='center')

def find_clevels(iarea, data, lon, lat, dlevel, plot_type):
    
    slat,elat,slon,elon = area_region(iarea)

    if elon == 360.0:
        elon = 359.75

    lon_index = [float_index(lon, slon), float_index(lon, elon)]
    lat_index = [float_index(lat, slat), float_index(lat, elat)]

    data_visible = data[lat_index[0]:lat_index[1]+1, lon_index[0]:lon_index[1]+1]

    data_max, data_min = int(data_visible.max()), int(data_visible.min())

    if dlevel >= 10:
        data_max = data_max // 10 * 10
        data_min = data_min // 10 * 10

    if plot_type == 'PMF':
        if abs(data_max) > abs(data_min):
            data_min = - data_max
        else:
            data_max = - data_min
    
    if (data_max - data_min) % dlevel != 0:
        data_max = ((data_max - data_min) // dlevel + 1) * dlevel + data_min

    clevels = np.arange(data_min, data_max + dlevel, dlevel)

    return clevels

def plot_data(post_data, plot_type, var, varname, lon, lat, iarea, title, subtitle, pic_file, clevels):
    
    plt.rcParams['font.family'] = 'serif'

    TLON,TLAT = np.meshgrid(lon,lat)
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
    
    _add_title(ax_title, title, subtitle)

    if iarea == 'Tropics':
        ax_cf = fig.add_axes([0.1, 0.16, 0.85, 0.65])
    elif iarea == 'Global':
        ax_cf = fig.add_axes([0.1, 0.12, 0.85, 0.80])
    else:
        ax_cf = fig.add_axes([0.1, 0.10, 0.85, 0.80])
    
    if iarea == 'Global':
        ax_cb = fig.add_axes([0.1, 0.12, 0.85, 0.03])
    if iarea in ['North_P', 'South_P']:
        ax_cb = fig.add_axes([0.1, 0.05, 0.85, 0.03])
    if iarea == 'Tropics':
        ax_cb = fig.add_axes([0.3, 0.05, 0.4, 0.03])
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
        map.drawparallels(np.arange(slat, elat+1, 20), linewidth=1, dashes=[4, 3], labels=[1, 0, 1, 1])
        map.drawmeridians(np.arange(slon, elon+1, 20), linewidth=1, dashes=[4, 3], labels=[1, 1, 0, 1])

    map.drawcoastlines()
    
    # tick latitude labels manually
    if iarea == 'North_P': 
        lat_labels= [(120, 60), (120, 70), (120, 80), (300, 60), (300, 70), (300, 80)]
    elif iarea == 'South_P':
        lat_labels= [(120, -60), (120, -70), (120, -80), (300, -60), (300, -70), (300, -80)]

    if iarea in ['North_P', 'South_P']:
        _tick_lats(map, lat_labels, ax_cf)

    if iarea == 'North_P':
        _tick_lats(map, [(90, 60)], ax_cf, rl='r')
        _tick_lats(map, [(270, 60)], ax_cf, rl='l')
    elif iarea == 'South_P':
        _tick_lats(map, [(90, -60)], ax_cf, rl='r')
        _tick_lats(map, [(270, -60)], ax_cf, rl='l')
    
    x, y = map(TLON.T, TLAT.T)

    origin = 'lower'

    # some settings 
    
    if plot_type == 'PMF':
        cmap = 'RdBu_r'
    else:
        cmap = 'jet'
    
    if var in ['24hrain']:
        norm = colors.LogNorm()
    else:
        norm = None
    
    if var in ['24hrain']:
        post_data = ma.masked_where(post_data <= 0.01, post_data)
    
    if clevels[-1] - clevels[-2] != clevels[1] - clevels[0]:
        ticks = clevels
        ticklabels = [str(clevel) for clevel in clevels]
    else:
        ticks = None

    CF = map.contourf(x, y, post_data.T, levels=clevels, cmap=cmap, origin=origin, extend="both", norm=norm)
    CB = fig.colorbar(CF, cax=ax_cb, orientation='horizontal', ticks=ticks)
    if 'ticklabels' in locals().keys():
        CB.ax.set_xticklabels(ticklabels)
    CB.set_label(varname, fontsize=14)

    plt.savefig('./pic/{}'.format(pic_file), bbox_inches='tight', dpi=500)
    plt.close()


def plot_case(data_field, data_obs, lon, lat, title, subtitle, pic_file, newcolorscheme):
    
    plt.rcParams['font.family'] = 'serif'

    # mask zero precipitation 
    data_field = ma.masked_where(data_field <= 0.0, data_field)

    TLON,TLAT = np.meshgrid(lon,lat)
    slat,elat,slon,elon = area_region('China')

    figsize = (10.5,8.7)

    fig = plt.figure(figsize=figsize)

    ax_title = fig.add_axes([0.1, 0.90, 0.82, 0.08])

    _add_title(ax_title, title, subtitle)

    ax_cf = fig.add_axes([0.1, 0.10, 0.85, 0.80])

    ax_cb = fig.add_axes([0.3, 0.05, 0.4, 0.03])

    map = Basemap(projection='cyl',llcrnrlat=slat,urcrnrlat=elat, llcrnrlon=slon, urcrnrlon=elon, resolution='l', ax=ax_cf)
    map.drawparallels(np.arange(slat, elat+1, 10), linewidth=0.6, dashes=[4, 3], labels=[1, 0, 0, 0])
    map.drawmeridians(np.arange(slon, elon+1, 10), linewidth=0.6, dashes=[4, 3], labels=[0, 0, 0, 1])

    map.drawcoastlines()
    map.drawcountries()

    x, y = map(TLON.T, TLAT.T)

    origin = 'lower'

    ZERO = 1E-5
    INF = 1E6
    clevels = [0.1, 10, 25, 50, 100]

    if newcolorscheme:
        colortable_obs = ['lightblue', 'royalblue', 'cyan', 'yellow', 'orange', 'red']
        colortable_pre = colortable_obs
        alpha_pre = 0.5
        alpha_obs = 0.8
        clabel = False
    else:
        colortable_obs = ['white', 'blue', 'green', 'yellow', 'red', 'purple']
        colortable_pre = ['white', 'lavender', 'lightblue', 'cornflowerblue', 'royalblue', 'darkblue']
        alpha_pre = 1.0
        alpha_obs = 1.0
        clabel = True

    colorlabel = ['<0.1mm', '0.1~10mm', '10~25mm', '25~50mm', '50~100mm', '>100mm']
    
    color_ranges = list()
    for icolor, color in enumerate(colortable_obs):
        if icolor == 0:
            color_ranges.append((ZERO, clevels[0]))
        elif icolor == len(colortable_obs) - 1:
            color_ranges.append((clevels[-1], INF))
        else:
            color_ranges.append((clevels[icolor-1], clevels[icolor]))

    cmap = mpl.colors.ListedColormap(colortable_pre[1:-1])
    cmap.set_over(colortable_pre[-1])
    cmap.set_under(colortable_pre[0])
    norm = mpl.colors.BoundaryNorm(clevels, cmap.N)
    
    ticks = clevels
    ticklabels = [str(clevel) for clevel in clevels]    

    CF = map.contourf(x, y, data_field.T, levels=clevels, cmap=cmap, origin=origin, extend="both", norm=norm, alpha=alpha_pre)
    CB = fig.colorbar(CF, cax=ax_cb, orientation='horizontal', ticks=clevels)
    CB.ax.set_xticklabels(ticklabels)
    CB.set_label('24h precipitation [mm]', fontsize=14)

    if clabel:
        CL = map.contour(x, y, data_field.T, levels=clevels, colors='k', origin=origin, linewidths=0.8)
        ax_cf.clabel(CL, CL.levels, inline=True, fontsize=8, fmt="%3.1f", colors='k')

    # add observation dots
    lons = np.array(data_obs['longitude'])
    lats = np.array(data_obs['latitude'])
    data = np.array(data_obs['precipitation'])
    
    for icolor, color_range in enumerate(color_ranges):

        # old scheme scatter no <0.1mm observation
        if not newcolorscheme and icolor == 0:
            continue
        
        data_filter = (data>color_range[0]) & (data<color_range[1])
        lons_color = lons[data_filter]
        lats_color = lats[data_filter]
        data_color = data[data_filter]
    
        x, y = map(lons_color, lats_color)
        map.scatter(x, y, marker='o',color=colortable_obs[icolor], alpha=alpha_obs, s=10, label=colorlabel[icolor])

    ax_cf.legend(frameon=True, loc='lower left', title='Observation')

    plt.savefig('./pic/{}'.format(pic_file), bbox_inches='tight', dpi=500)
    plt.close()

