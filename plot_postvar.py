#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-28 20:49:41
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
from multiprocessing import Pool
from scipy.interpolate import griddata
import hashlib

from plotmap import plot_data, find_clevels, plot_case
from utils import DATAdecorator, config, hashlist
from derived_vars import derived_vars, get_derived_var
from asciiio import read_obs

# read the config file
cong = config()

for key, value in cong.items():
    globals()[key] = value

OBS_HASH = hashlist([case_ini_times, case_fcst_hours])
GRAPES_HASH = hashlist([st_vars, st_levels, fcst, start_ddate, end_ddate, fcst_step, OBS_HASH])
OBS_DATA_PKLNAME = './pkl/OBS_{}.pkl'.format(OBS_HASH)
GRAPES_DATA_PKLNAME = './pkl/GRAPES_{}.pkl'.format(GRAPES_HASH)
FNL_DATA_PKLNAME = './pkl/FNL_{}.pkl'.format(GRAPES_HASH)


# pickle the data for ploting
@DATAdecorator('./', True, GRAPES_DATA_PKLNAME)
def get_GRAPES_data():

    # 1.0 读取postvar数据
    print(u'1.0 开始读取postvar数据')
    import netCDF4 as nc
    t0_readpostvar = time.time()
    data_list = []
    for ifile in ncfiles:
        if not os.path.exists(exdata_dir+ifile):
            print('Error: {} file not found under dir {}'.format(ifile, exdata_dir))
            sys.exit()
        data_list.append(nc.Dataset(exdata_dir+ifile, 'r'))

    t1_readpostvar = time.time()
    print(u'postvar数据读取结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    lat, lon  = data_list[0].variables['latitude'][:], data_list[0].variables['longitude'][:]
    TLAT, TLON  = np.meshgrid(lat, lon)
    levels    = data_list[0].variables['levels'][:].tolist()
    time_incr = int(float(data_list[0].variables['times'].incr))
    
    time_indices = np.array([int(i/time_incr) for i in fcst], dtype='int')

    # get time_indices_rain, make alignment with 00UTC
    if dt.datetime.strptime(timelines[0], '%Y%m%d%H').hour == 0: 
        time_indices_rain = time_indices
    else:
        offset_index = (24 - dt.datetime.strptime(timelines[0], '%Y%m%d%H').hour) // time_incr
        time_indices_rain = time_indices + offset_index

    # 2.0 对指定高度和指定的预报时效做平均
    print(u'2.0 对指定预报面高度列表和指定的预报时效列表做平均')
    t0_readpostvar = time.time()

    tmp_datatable = np.zeros((len(timelines), len(st_vars), len(time_indices), len(st_levels), len(lat), len(lon)), dtype='float32')
    var_ndims = dict()
    var_time_indices = dict()

    for ivar, var in enumerate(st_vars):
        
        time_indices_var = list(time_indices_rain if var in align_vars else time_indices)
        # moist vars skip for initial filed
        if var in moist_vars:
            time_indices_var.remove(0)
        
        var_time_indices[var] = time_indices_var
             
        for itime, time_index in enumerate(time_indices_var):
            for idata, data in enumerate(data_list):
                # get the variable table
                if var in ex_vars:
                    var_table = data.variables[var]
                else:
                    var_table = get_derived_var(data, var)
                if var not in var_ndims.keys():
                    var_ndims[var] = len(var_table.shape)

                if var_ndims[var] == 4:
                    for ilevel, level in enumerate(st_levels):
                        level_index = levels.index(level)
                        tmp_datatable[idata, ivar, itime, ilevel, ...] = var_table[time_index, level_index, ...]
                elif var_ndims[var] == 3:
                    tmp_datatable[idata, ivar, itime, 0, ...] = var_table[time_index, ...]
                    
    datatable = np.average(tmp_datatable, axis=0)

    datatable_case = np.zeros((len(case_ini_times), len(case_fcst_hours), len(lat), len(lon)), dtype='float32')

    for iinit, case_ini_time in enumerate(case_ini_times):
        for ifcst, case_fcst_hour in enumerate(case_fcst_hours):
            init_index = timelines.index(case_ini_time)
            fcst_index = case_fcst_hour // time_incr
            data = data_list[init_index]
            var_table = get_derived_var(data, '24hrain')            
            datatable_case[iinit, ifcst, ...] = var_table[fcst_index, ...]

    # close the netCDF file handles and nc package for nasty issues with Nio
    for data in data_list:
        data.close()
    del tmp_datatable
    del nc

    t1_readpostvar = time.time()
    print(u'对指定预报面高度列表和指定的预报时效列表做平均结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    global_package = dict()
    global_names = ['time_indices', 'time_incr', 'time_indices_rain', 
                    'levels', 'TLON', 'TLAT', 'lon', 'lat', 
                    'var_ndims', 'var_time_indices']
    for global_name in global_names:
        global_package[global_name] = locals()[global_name]

    return global_package, datatable, datatable_case

# pickle the data for ploting
@DATAdecorator('./', True, FNL_DATA_PKLNAME)
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

        if not os.path.exists(fnl_dir+fnl_filename):
            print('Error: {} file not found under dir {}'.format(fnl_filename, fnl_dir))
            sys.exit()
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

    tmp_datatable = np.zeros((len(timelines), len(st_vars), len(time_indices), len(st_levels), len(lat), len(lon)), dtype='float32')
    
    # we use a data cache to avoid repeated interpolation for the same dataset
    data_cache = dict()
     
    for iinittime, inittime_str in enumerate(timelines): 
        for ifcsttime, time_index in enumerate(time_indices):
            
            fnl_datetime = (dt.datetime.strptime(inittime_str, '%Y%m%d%H') + dt.timedelta(hours=fcst[ifcsttime])).strftime('%Y%m%d%H')
            
            if fnl_datetime in data_cache:
                tmp_datatable[iinittime, :, ifcsttime, :, ...] = \
                    tmp_datatable[data_cache[fnl_datetime][0], :, data_cache[fnl_datetime][1], :, ...] 
            else:
                for ivar, var in enumerate(st_vars):
                    if var in noFNL_vars:
                        continue
                    for ilevel, level in enumerate(st_levels):
                        level_index = fnl_levels.index(level)
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


@DATAdecorator('./', True, OBS_DATA_PKLNAME)
def get_OBS_data():

    # 3.0 读取FNL数据
    print(u'5.0 开始读取OBS数据')
    t0_readpostvar = time.time()
    
    datatable = dict()
    for case_ini_time in case_ini_times:
        datatable[case_ini_time] = dict()
        for case_fcst_hour in case_fcst_hours:
            obs_utc_dt = dt.datetime.strptime(case_ini_time, '%Y%m%d%H') + dt.timedelta(hours=case_fcst_hour)
            obs_bjt_dt = obs_utc_dt + dt.timedelta(hours=8)
            obs_timestamp = obs_bjt_dt.strftime('%Y%m%d%H')
            obs_filename = obs_dir + 'rr24{}/{}/{}.000'.format(obs_utc_dt.strftime('%H'), obs_utc_dt.strftime('%Y'), \
            obs_bjt_dt.strftime('%y%m%d%H'))

            datatable[case_ini_time][case_fcst_hour] = read_obs(obs_filename)

    t1_readpostvar = time.time()
    print(u'读取OBS数据结束, 用时{} seconds.'.format(str(t1_readpostvar-t0_readpostvar)[:7]))

    return datatable

# Main Program
if __name__ == "__main__":
    
    # 参数设置
    timelines   = gen_timelines(start_ddate, end_ddate, fcst_step)
    ncfiles     = ['postvar{}.nc'.format(itime) for itime in timelines]

    # datatable dimension: (nvars, nfcsrtimes, nlevels, nlat, nlon)
    global_package, datatable_grapes, datatable_case_grapes = get_GRAPES_data()
    for global_name in global_package.keys():
        globals()[global_name] = global_package[global_name]
    datatable_fnl = get_FNL_data()
    datatable_obs = get_OBS_data()

    # print(datatable_grapes.shape)
    # data = datatable_grapes[0, 1, 0, ...] 
    # print(data.max())
    # print(data.min())

    # exit()

    if clean_plot:
        os.system('rm -rf ./pic/*')
    
    if plot_cases:
        for iinit, case_ini_time in enumerate(case_ini_times):
            for ifcst, case_fcst_hour in enumerate(case_fcst_hours):
                dataframe_obs = datatable_obs[case_ini_time][case_fcst_hour]
                dataframe_grapes = datatable_case_grapes[iinit, ifcst, ...]
                title    = 'Prediction and Observation of {}hr 24hours precipitation [mm]'.format(case_fcst_hour)
                subtitle = 'Init: {} UTC'.format(case_ini_time)
                pic_file = 'case_{}_{}hr_24hrain.png'.format(case_ini_time, case_fcst_hour)

                plot_case(dataframe_grapes, dataframe_obs, lon, lat, title, subtitle, pic_file, newcolorscheme)

    # exit()

    # begin to plot
    for plot_type in plot_types:
        print('开始作图: {}'.format(plot_types_name[plot_type]))
        for ivar, var in enumerate(st_vars):
            print('\t变量: {}'.format(var))
            # No FNL data for '24hrain'
            if var in noFNL_vars and plot_type in ['F', 'PMF']:
                continue
            varname = variable_name[var]

            time_indices_var = var_time_indices[var] 

            for iarea in plot_areas:
                print('\t\t区域: {}'.format(iarea))
                for itime,time_index in enumerate(time_indices_var):
                    
                    if var not in clevel_custom.keys():
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
                        
                        if var in clevel_custom.keys(): 
                            clevels = np.array(clevel_custom[var])
                        else:
                            if plot_type in ['P', 'F']:
                                clevel_data = datatable_grapes[ivar, itime, ilevel, ...]
                            elif plot_type in ['PMF']:
                                # the biggest forecast range have large clevels
                                clevel_data = datatable_grapes[ivar, -1, ilevel, ...] - \
                                    datatable_fnl[ivar, -1, ilevel, ...]
                            clevels = find_clevels(iarea, clevel_data, lon, lat, dlevel, plot_type)

                        # 3D or surface vars
                        if var_ndims[var] == 4:
                            title    = '{} of {}hr {}hPa {}'.format(plot_types_name[plot_type], time_index*time_incr, int(level), varname)
                            subtitle = 'Init: {} UTC - {} UTC'.format(start_ddate, end_ddate)
                            pic_file = '{}_{}_{}hr_{}hpa_{}.png'.format(plot_type, iarea, time_index*time_incr, int(level), var)

                            print('\t\t\t'+pic_file)

                            p.apply_async(plot_data, args=(data, plot_type, var, varname, lon, lat, iarea, title, subtitle, pic_file, clevels))
                            plot_data(data, plot_type, var, varname, lon, lat, iarea, title, subtitle, pic_file, clevels)
                        elif var_ndims[var] == 3:
                            title    = '{} of {}hr {}'.format(plot_types_name[plot_type], time_index*time_incr, varname)
                            subtitle = 'Init: {} UTC - {} UTC'.format(start_ddate, end_ddate)
                            pic_file = '{}_{}_{}hr_{}.png'.format(plot_type, iarea, time_index*time_incr, var)

                            print('\t\t\t'+pic_file)

                            plot_data(data, plot_type, var, varname, lon, lat, iarea, title, subtitle, pic_file, clevels)
                            break

                    p.close()
                    p.join()

