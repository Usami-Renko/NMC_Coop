#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-22 20:54:10
@Description  : process postvar
'''
import sys
# sys.path.append('/g3/wanghao/Python/Cmodule/gen_info')
# sys.path.append('/home/shiyu1997/NMC/Cmodule/')
sys.path.append('./Cmodule')
import numpy as np
import time
import datetime as dt
from gen_timelines import gen_timelines
import os
import yaml
from multiprocessing import Pool
from PIL import Image
from scipy.interpolate import griddata

from plotmap import plot_data
from utils import DATAdecorator


# pickle the data for ploting
@DATAdecorator('./', False, './pkl/GRAPES.pkl')
def get_GRAPES_data():

    global time_indices, time_incr
    global levels, TLON, TLAT, lon, lat

    # 1.0 读取postvar数据
    print(u'1.0 开始读取postvar数据')
    import netCDF4 as nc
    t0_readpostvar = time.time()
    data_list = []
    for ifile in ncfiles:
        data_list.append(nc.Dataset(exdata_dir+ifile, 'r'))

    t1_readpostvar = time.time()
    print(u'postvar数据读取结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    lat, lon  = data_list[0].variables['latitude'][:], data_list[0].variables['longitude'][:]
    TLAT, TLON  = np.meshgrid(lat, lon)
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

    # close the netCDF file handles and nc package for nasty issues with Nio
    for data in data_list:
        data.close()
    del tmp_datatable
    del nc

    t1_readpostvar = time.time()
    print(u'对指定预报面高度列表和指定的预报时效列表做平均结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    return datatable

# pickle the data for ploting
@DATAdecorator('./', True, './pkl/FNL.pkl')
def get_FNL_data():

    # 3.0 读取FNL数据
    print(u'3.0 开始读取FNL数据')
    t0_readpostvar = time.time()

    import Nio
    
    init_datetimes = np.array([dt.datetime.strptime(itime, "%Y%m%d%H") for itime in timelines])

    fnl_datetime_set = set()
    for ifcst in fcst:
        new = set(init_datetimes + dt.timedelta(hours=ifcst))
        fnl_datetime_set = fnl_datetime_set.union(new)

    fnl_data_dic = dict()
    for fnl_datetime in fnl_datetime_set:
        fnl_filename = fnl_datetime.strftime("fnl_%Y%m%d_%H_00.grib2")
        fnl_timestr = fnl_datetime.strftime("%Y%m%d%H")
        
        fnl_data_dic[fnl_timestr] = Nio.open_file(fnl_dir+fnl_filename, 'r')

    t1_readpostvar = time.time()
    print(u'读取FNL数据结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    # 4.0 对FNL数据进行插值
    print(u'4.0 对FNL数据进行插值')
    t0_readpostvar = time.time()
    
    sample = list(fnl_data_dic.values())[0]
    fnl_lat, fnl_lon = sample.variables['lat_0'][:], sample.variables['lon_0'][:]
    TLAT_fnl, TLON_fnl = np.meshgrid(fnl_lat, fnl_lon)
    
    # pad the data to make it cyclic
    TLON_fnl = np.pad(TLON_fnl, ((0, 1), (0, 0)), 'constant', constant_values=360.0)
    TLAT_fnl = np.pad(TLAT_fnl, ((0, 1), (0, 0)), 'constant')
    TLAT_fnl[-1, :] = TLAT_fnl[0, :] 
    
    # make flattend points
    LAT_fnl, LON_fnl   = TLAT_fnl.T.flatten(), TLON_fnl.T.flatten()
    points = np.zeros((len(LAT_fnl), 2))
    points[:, 0], points[:, 1] = LAT_fnl, LON_fnl
    
    fnl_levels = (sample.variables['lv_ISBL0'][:] / 100.).tolist()  # [Pa] --> [hPa]

    # print(fnl_levels)
    # print(levels)
    '''
    We perform FNL to GRAPES interpolation
    All the grapes levels can be found in FNL dataset levels
    No vertical interpolation needed

    FNL levels: 
    [  10.   20.   30.   50.   70.  100.  150.  200.  250.  300.  350.  400.
      450.  500.  550.  600.  650.  700.  750.  800.  850.  900.  925.  950.
      975. 1000.]
    
    GRAPES levels:
    [1000.0, 925.0, 850.0, 700.0, 600.0, 500.0, 400.0, 300.0, 200.0, 100.0, 50.0, 10.0]
    '''

    tmp_datatable = np.zeros((len(data_list), len(st_vars), len(time_indices), len(st_levels), len(lat), len(lon)), dtype='float32')
    
    # we use a data cache to avoid repeated interpolation for the same dataset
    data_cache = dict()
     
    for iinittime, inittime_str in enumerate(timelines): 
        for ifcsttime, time_index in enumerate(time_indices):
            
            fnl_datetime = (dt.datetime.strptime(inittime_str, '%Y%m%d%H') + dt.timedelta(hours=fcst[ifcsttime])).strftime('%Y%m%d%H')
            
            if fnl_datetime in data_cache:
                tmp_datatable[iinittime, :, ifcsttime, :, ...] = \
                    tmp_datatable[data_cache[fnl_datetime][0], :, data_cache[fnl_datetime][1], :, ...] 
            else:
                for ilevel, level in enumerate(st_levels):
                    level_index = fnl_levels.index(level)
                    for ivar, var in enumerate(st_vars):
                        
                        # (lat, lon)
                        fnl_level_data = fnl_data_dic[fnl_datetime].variables[fnl_varname[var]][level_index, ...]

                        # pad the data to make it cyclic
                        fnl_level_data = np.pad(fnl_level_data, ((0, 0), (0, 1)), 'constant')
                        fnl_level_data[:, -1] = fnl_level_data[:, 0]

                        values = fnl_level_data.flatten()
                        interp = griddata(points, values, (TLAT.T, TLON.T), method='linear')

                        tmp_datatable[iinittime, ivar, ifcsttime, ilevel, ...] = interp
                
                data_cache[fnl_datetime] = (iinittime, ifcsttime)
    
    datatable = np.average(tmp_datatable, axis=0)

    # close the file handle    
    for fnl_data in fnl_data_dic.values():
        fnl_data.close()
    del tmp_datatable
    del Nio

    t1_readpostvar = time.time()
    print(u'对FNL数据进行插值, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    return datatable

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
    fnl_dir        = cong['fnl_dir']
    fnl_varname    = cong['fnl_varname']
    st_vars        = cong['st_vars']
    st_levels      = cong['st_levels']
    fcst           = cong['fcst']
    make_gif       = cong['make_gif']
    clevel_step    = cong['clevel_step']
    clevel_step_PMF= cong['clevel_step_PMF']
    variable_name  = cong['variable_name']
    plot_areas     = cong['plot_areas']
    plot_types     = cong['plot_types']
    plot_types_name= cong['plot_types_name']
    
    # 参数设置
    fcst_step   = 24  # hours
    timelines   = gen_timelines(start_ddate, end_ddate, fcst_step)
    
    ncfiles     = ['postvar{}.nc'.format(itime) for itime in timelines]

    # datatable dimension: (ninittimes, nvars, nfcsrtimes, nlevels, nlat, nlon)
    datatable_grapes = get_GRAPES_data()
    datatable_fnl = get_FNL_data()

    # begin to plot
    for plot_type in plot_types:
        for iarea in plot_areas:
            for itime,time_index in enumerate(time_indices):
                for ivar, var in enumerate(st_vars):
                    varname = variable_name[var]
                    
                    if plot_type in ['P', 'F']:    
                        dlevel = clevel_step[var]
                    elif plot_type == 'PMF':
                        dlevel = clevel_step_PMF[var]

                    p = Pool(len(st_levels))
                    for ilevel,level in enumerate(st_levels):

                        if plot_type == 'P':
                            data = datatable_grapes[ivar, itime, ilevel, ...]
                        elif plot_type == 'F':
                            data = datatable_fnl[ivar, itime, ilevel, ...]
                        elif plot_type == 'PMF':
                            data = datatable_grapes[ivar, itime, ilevel, ...] - \
                                datatable_fnl[ivar, itime, ilevel, ...]

                        title    = '{} of {}hr {}hPa {}'.format(plot_types_name[plot_type], time_index*time_incr, int(level), varname)
                        subtitle = 'Init: {} UTC - {} UTC'.format(start_ddate, end_ddate)
                        pic_file = '{}_{}_{}hr_{}hpa_{}.png'.format(plot_type, iarea, time_index*time_incr, int(level), var)
                        p.apply_async(plot_data, args=(data, plot_type, varname, lon, lat, iarea, title, subtitle, pic_file, dlevel))
                        plot_data(data, plot_type, varname, lon, lat, iarea, title, subtitle, pic_file, dlevel)
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
