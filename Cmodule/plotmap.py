#!/usr/bin/env python
# coding=UTF-8

'''
@Description: plot the countoured map of a given variable
@Author: Hejun Xie
@Date: 2020-04-20 18:46:33
@LastEditors: Hejun Xie
@LastEditTime: 2020-06-25 16:10:47
'''

from mpl_toolkits.basemap import Basemap
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Point
import pandas as pd
from pandas.core.frame import DataFrame
import numpy as np
import copy as cp
import maskout
from matplotlib import colors
from numpy import ma
import os
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def config_submodule(cong, pic_dir, expr_name):

    global origin_dir, case_dir, zonalmean_dir, plot_expr

    for key, value in cong.items():
        globals()[key] = value

    origin_dir = os.path.join(pic_dir, origin)
    case_dir = os.path.join(pic_dir, case)
    zonalmean_dir = os.path.join(pic_dir, zonalmean)
    plot_expr = expr_name

def area_region(area):
    if area == 'South_P':
        rlat, qlat = -90., -60.
        rlon, qlon =   0., 360.
    if area  == 'North_P':
        rlat, qlat =  60.,  90.
        rlon, qlon =   0., 360.
    if area == 'E_Asia':
        rlat, qlat =  10.,  60.
        rlon, qlon =  70., 140.
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

def _add_title(ax, title, subtitle, statistics, figsize, plot_type):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.set_xticks([])
    ax.set_yticks([])
    
    if isinstance(title, list):
        if figsize[0] < figsize[1] * 1.4:
            ax.text(0.5, 0.80, title[0], fontsize=20, ha='center', va='center')
            ax.text(0.5, 0.40, title[1], fontsize=16, ha='center', va='center')
        else:
            ax.text(0.5, 0.60, title[0] + ' ' + title[1], fontsize=18, ha='center', va='center')
    else:
        ax.text(0.5, 0.50, title, fontsize=22, ha='center', va='center')
    ax.text(0.5, 0.00, subtitle, fontsize=14, ha='center', va='center')

    if statistics is None:
        if plot_type in ['GMF', 'G']:
            ax.text(0.14, 0.30, "{}".format(plot_expr), fontsize=14, weight='bold', ha='right', va='center')
    else:
        if plot_type in ['GMF', 'G']:
            ax.text(0.08, 0.90, "MIN: {:>.2f}".format(statistics[0]), fontsize=8, ha='right', va='center')
            ax.text(0.08, 0.60, "MAX: {:>.2f}".format(statistics[1]), fontsize=8, ha='right', va='center')
            ax.text(0.08, 0.30, "MEAN: {:>.2f}".format(statistics[2]), fontsize=8, ha='right', va='center')
            ax.text(0.08, 0.00, "{}".format(plot_expr), fontsize=10, weight='bold', ha='right', va='center')
        elif plot_type == 'F':
            ax.text(0.08, 0.60, "MIN: {:>.2f}".format(statistics[0]), fontsize=8, ha='right', va='center')
            ax.text(0.08, 0.30, "MAX: {:>.2f}".format(statistics[1]), fontsize=8, ha='right', va='center')
            ax.text(0.08, 0.00, "MEAN: {:>.2f}".format(statistics[2]), fontsize=8, ha='right', va='center')

def _clip_data(iarea, data, lon, lat):

    slat,elat,slon,elon = area_region(iarea)

    if elon == 360.0:
        elon = 359.75

    lon_index = [float_index(lon, slon), float_index(lon, elon)]
    lat_index = [float_index(lat, slat), float_index(lat, elat)]

    data_visible = data[lat_index[0]:lat_index[1]+1, lon_index[0]:lon_index[1]+1]

    return data_visible

def _clip_data_zonal(iarea, data, lat):
    slat,elat,slon,elon = area_region(iarea)
    lat_index = [float_index(lat, slat), float_index(lat, elat)]
    data_visible = data[:, lat_index[0]:lat_index[1]+1]
    return data_visible

def _find_clevels_rec(data, dlevel, plot_type):
    
    if dlevel < 1.0:
        data *= 10
        dlevel *= 10
        clevels = _find_clevels_rec(data, dlevel, plot_type) / 10.
        return clevels
    
    # remove float here
    dlevel = int(dlevel)
    
    data_max, data_min = int(data.max()), int(data.min())

    if plot_type in ['G', 'F']:
        data_max = data_max // dlevel * dlevel
        data_min = data_min // dlevel * dlevel
    
    if plot_type in ['GMF']:
        data_max = data_max // dlevel * dlevel + dlevel / 2
        data_min = data_min // dlevel * dlevel - dlevel / 2

    if plot_type == 'GMF':
        if abs(data_max) > abs(data_min):
            data_min = - data_max
        else:
            data_max = - data_min
    
    if (data_max - data_min) % dlevel != 0:
        data_max = ((data_max - data_min) // dlevel + 1) * dlevel + data_min

    clevels = np.arange(data_min, data_max + dlevel, dlevel)
    return clevels

def find_clevels(iarea, data, lon, lat, dlevel, plot_type):
    data_visible = _clip_data(iarea, data, lon, lat)
    data_visible_copy = cp.copy(data_visible)
    clevels = _find_clevels_rec(data_visible_copy, dlevel, plot_type)
    if len(clevels) > 20:
        step = len(clevels) // 20
        clevels = clevels[::step]
    
    return clevels

def find_clevels_zonal(iarea, data, lat, dlevel, plot_type):
    data_visible = _clip_data_zonal(iarea, data, lat)
    data_visible_copy = cp.copy(data_visible)
    clevels = _find_clevels_rec(data_visible_copy, dlevel, plot_type)
    if len(clevels) > 20:
        step = len(clevels) // 20
        clevels = clevels[::step]
    
    return clevels

def find_statistics(iarea, data, lon, lat):
    if len(data.shape) == 2:
        data_visible = _clip_data(iarea, data, lon, lat)
    else:
        data_visible = data
    Min, Max, Mean = data_visible.min(), data_visible.max(), data_visible.mean()
    return Min, Max, Mean

def clip_china_data(data, lat, lon):
    import geopandas as gpd

    fdata = data.flatten()
    TLAT, TLON = np.meshgrid(lat, lon)
    LAT, LON = TLAT.T, TLON.T
    fLAT, fLON = LAT.flatten(), LON.flatten()

    c={"lat":fLAT, "lon":fLON, "data":fdata}
    df=DataFrame(c)

    WORLD = gpd.read_file(mask_dir+'.shp')

    geometry = [Point(xy) for xy in zip(df.lon,df.lat)]

    crs = {'init':'epsg:4326'}
    data = gpd.GeoDataFrame(df,crs=crs,geometry=geometry)

    WORLD.crs = data.crs

    data_world = gpd.sjoin(data,WORLD,how="inner")
    data_china = data_world[data_world["SOVEREIGN"] == "China"]

    return data_china['data'], data_china.index

def plot_data_zonal(post_data, plot_type, var, varname, lat, iarea, title, subtitle, pic_file, clevels):
    plt.rcParams['font.family'] = 'serif'

    TLAT, TLEVEL = np.meshgrid(lat, ex_levels)
    slat,elat,slon,elon = area_region(iarea)

    figsize=(14, 10)
    
    fig = plt.figure(figsize=figsize)

    ax_title = fig.add_axes([0.1, 0.90, 0.82, 0.08])
    ax_cf = fig.add_axes([0.16, 0.14, 0.76, 0.72])
    ax_cb = fig.add_axes([0.1, 0.05, 0.85, 0.03])

    _add_title(ax_title, title, subtitle, None, figsize, plot_type)

    origin = 'lower'
    extend = 'both'

    if plot_type == 'GMF':
        cmap = 'RdBu_r'
    else:
        cmap = 'jet'

    if var in ['q'] and plot_type in ['G', 'F']:
        post_data = ma.masked_where(post_data <= 0.00, post_data)
        extend = 'max'

    if len(clevels) < 3:
        print("[warning]: clevels too short for this var at this level, abort...".format())
        return
    
    if var in symlognorm_params_zonalmean_PMF.keys() and plot_type == 'GMF':
        norm=colors.SymLogNorm(**symlognorm_params_zonalmean_PMF[var] if symlognorm_params_zonalmean_PMF[var] is not None else {})
    else:
        norm = None

    ticks = clevels
    ticklabels = [str(clevel) for clevel in clevels]

    latticks = [-60, -30, 0, 30, 60]
    latticklabels = ['60S', '30S', 'EQ', '30N', '60N']
    leveltickelabels = [str(leveltick) for leveltick in levelticks]

    CF = ax_cf.contourf(TLAT.T, TLEVEL.T, post_data.T, levels=clevels, cmap=cmap, origin=origin, extend=extend, norm=norm)
    
    ax_cf.invert_yaxis()

    ax_cf.set_xticks(latticks)
    ax_cf.set_xticklabels(latticklabels, fontsize=14)
    ax_cf.set_yticks(levelticks)
    ax_cf.set_yticklabels(leveltickelabels, fontsize=14)
    
    CB = fig.colorbar(CF, cax=ax_cb, orientation='horizontal', ticks=ticks)
    CB.ax.set_xticklabels(ticklabels)
    for tick in CB.ax.xaxis.get_major_ticks():
        tick.label.set_fontsize(10)
        tick.label.set_rotation(45)

    CB.set_label(varname, fontsize=14)
    
    plt.savefig('{}/{}/{}'.format(zonalmean_dir, var, pic_file), bbox_inches='tight', dpi=plot_dpi)
    plt.close(fig)


def plot_data(post_data, plot_type, var, varname, lon, lat, iarea, title, subtitle, pic_file, clevels, statistics):
    
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
        figsize = (10,8.2)

    fig = plt.figure(figsize=figsize)
    
    if iarea == 'Tropics':
        ax_title = fig.add_axes([0.1, 0.80, 0.82, 0.18])
    else:
        ax_title = fig.add_axes([0.1, 0.90, 0.82, 0.08])
    
    _add_title(ax_title, title, subtitle, statistics, figsize, plot_type)

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
        map.drawcountries()
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
    extend = 'both'

    # some settings 
    
    if plot_type == 'GMF':
        cmap = 'RdBu_r'
    else:
        cmap = 'jet'
    
    if var in ['24hrain']:
        post_data = ma.masked_where(post_data <= 0.01, post_data)
    
    if var in ['q'] and plot_type in ['G', 'F']:
        post_data = ma.masked_where(post_data <= 0.00, post_data)
        extend = 'max'

    if len(clevels) < 3:
        print("[warning]: clevels too short for this var at this level, abort...".format())
        return

    if var in lognorm_params.keys():
        norm = colors.LogNorm(**lognorm_params[var] if lognorm_params[var] is not None else {})
    elif var in symlognorm_params.keys():
        norm=colors.SymLogNorm(**symlognorm_params[var] if symlognorm_params[var] is not None else {})
    else:
        norm = None

    ticks = clevels
    ticklabels = [str(clevel) for clevel in clevels]

    CF = map.contourf(x, y, post_data.T, levels=clevels, cmap=cmap, origin=origin, extend=extend, norm=norm)
    CB = fig.colorbar(CF, cax=ax_cb, orientation='horizontal', ticks=ticks)
    CB.ax.set_xticklabels(ticklabels)
    for tick in CB.ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(10)
            tick.label.set_rotation(45)

    CB.set_label(varname, fontsize=14)

    # add mask here
    if iarea == 'E_Asia' and var == '24hrain':
        map.readshapefile(mask_dir,'whatevername',color='gray')
        clip=maskout.shp2clip(CF,ax_cf,mask_dir,'China')

    plt.savefig('{}/{}/{}'.format(origin_dir, var, pic_file), bbox_inches='tight', dpi=plot_dpi)
    plt.close(fig)


def plot_case(data_field, data_obs, lon, lat, title, subtitle, pic_file, newcolorscheme):
    
    plt.rcParams['font.family'] = 'serif'

    # mask zero precipitation 
    data_field = ma.masked_where(data_field <= 0.0, data_field)

    TLON,TLAT = np.meshgrid(lon,lat)
    slat,elat,slon,elon = area_region('China')

    figsize = (10.5,8.7)

    fig = plt.figure(figsize=figsize)

    ax_title = fig.add_axes([0.1, 0.90, 0.82, 0.08])

    _add_title(ax_title, title, subtitle, figsize)

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

    plt.savefig('{}/{}'.format(case_dir, pic_file), bbox_inches='tight', dpi=plot_dpi)
    plt.close(fig)

# unit test
if __name__ == "__main__":
    a = np.linspace(-0.05, 0.05, 100)
    dlevel = 0.01
    clevels = _find_clevels_rec(a, dlevel, 'P')
    print(clevels)
    