#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: Hejun Xie
@LastEditTime: 2020-05-18 18:00:51
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

from utils import DATAdecorator, config_list, hashlist, makenewdir, DumpDataSet
from derived_vars import FNLWorkStation, GRAPESWorkStation
from asciiio import read_obs
from plotmap import plot_data, find_clevels, plot_case
from make_comp import make_comp_pic, make_gif_pic

# read the config file

CONFIGPATH = './config/' # default config path
cong = config_list(CONFIGPATH, ['config.yml', 'devconfig.yml'])

# config submodules
import plotmap, make_comp
plotmap.config_submodule(cong)
make_comp.config_submodule(cong)

# config script
for key, value in cong.items():
    globals()[key] = value

origin_dir = os.path.join(pic_dir, origin_dir)
comp_dir = os.path.join(pic_dir, comp_dir)
gif_dir = os.path.join(pic_dir, gif_dir)
case_dir = os.path.join(pic_dir, case_dir)

OBS_HASH = hashlist([case_ini_times, case_fcst_hours])
GRAPES_HASH = hashlist([st_vars, st_levels, fcst, start_ddate, end_ddate, fcst_step, OBS_HASH])
OBS_DATA_PKLNAME = './pkl/OBS_{}.pkl'.format(OBS_HASH)
GRAPES_DATA_PKLNAME = './pkl/GRAPES_{}.pkl'.format(GRAPES_HASH)
FNL_DATA_PKLNAME = './pkl/FNL_{}.pkl'.format(GRAPES_HASH)


def get_time_indices(var, time_indices, time_incr, times):

    time_indices_var = time_indices.copy()
    times_dt = [dt.datetime.strptime(str(time), '%Y%m%d%H') for time in times]
    fcst_hours = [int((time_dt - times_dt[0]).total_seconds() // 3600) for time_dt in times_dt]

    if var in align_vars:
        if dt.datetime.strptime(timelines[0], '%Y%m%d%H').hour != 0:
            offset_index = (24 - dt.datetime.strptime(timelines[0], '%Y%m%d%H').hour) // time_incr
            time_indices_var = time_indices + offset_index
    if var in moist_vars:
        time_indices_var = time_indices[time_indices != 0]
    if var in daymean_vars:
        time_indices_var = time_indices[time_indices*time_incr >= 24]
    
    # remove overflow indices
    if var in align_vars:
        time_indices_var = time_indices_var[(time_indices_var*time_incr + 24) <= fcst_hours[-1]]
    else:
        time_indices_var = time_indices_var[(time_indices_var*time_incr) <= fcst_hours[-1]]
    
    return time_indices_var

# pickle the data for ploting
@DATAdecorator('./', True, GRAPES_DATA_PKLNAME)
def get_GRAPES_data():

    # 1.0 读取postvar数据
    print('1.0 开始读取postvar数据')
    import netCDF4 as nc
    t0 = time.time()
    data_list = []
    for ifile in ncfiles:
        if not os.path.exists(exdata_dir+ifile):
            raise IOError('{} file not found under dir {}'.format(ifile, exdata_dir))
        data_list.append(nc.Dataset(exdata_dir+ifile, 'r'))

    t1 = time.time()
    print('postvar数据读取结束, 用时{} seconds.'.format(str(t1-t0)[:7]))

    lat, lon  = data_list[0].variables['latitude'][:], data_list[0].variables['longitude'][:]
    TLAT, TLON  = np.meshgrid(lat, lon)
    levels    = data_list[0].variables['levels'][:].tolist()
    times     = data_list[0].variables['times'][:]
    time_incr = int(float(data_list[0].variables['times'].incr))
    
    time_indices = np.array([int(i/time_incr) for i in fcst], dtype='int')
    level_indices = np.array([levels.index(st_level) for st_level in st_levels], dtype='int')

    var_time_indices = dict()
    for ivar, var in enumerate(st_vars):
        var_time_indices[var] = get_time_indices(var, time_indices, time_incr, times)
    
    if run_mode == 'interp':
        global_package = dict()
        global_names = ['time_indices', 'time_incr', 
                    'levels', 'TLON', 'TLAT', 'lon', 'lat', 
                    'var_time_indices']
        for global_name in global_names:
            global_package[global_name] = locals()[global_name]
        
        return global_package, None, None        


    # 2.0 对指定高度和指定的预报时效做平均
    print('2.0 对指定预报面高度列表和指定的预报时效列表做平均')
    t0 = time.time()

    tmp_datatable = np.zeros((len(st_vars), len(time_indices), len(st_levels), len(lat), len(lon)), dtype='float32')
    for idata, data in enumerate(data_list):
        ws = GRAPESWorkStation(data, grapes_varname)
        for ivar, var in enumerate(st_vars):
            time_indices_var = var_time_indices[var]
            var_instance = ws.get_var(var, (time_indices_var, level_indices)).data
            if var_ndims[var] == 4:
                tmp_datatable[ivar, :len(time_indices_var), ...] += var_instance
            elif var_ndims[var] == 3:
                tmp_datatable[ivar, :len(time_indices_var), 0, ...] += var_instance
        ws.close()
    datatable = tmp_datatable / len(timelines)

    # get case data
    datatable_case = np.zeros((len(case_ini_times), len(case_fcst_hours), len(lat), len(lon)), dtype='float32')
    for iinit, case_ini_time in enumerate(case_ini_times):
        init_index = timelines.index(case_ini_time)
        data = data_list[init_index]

        ws = GRAPESWorkStation(data, grapes_varname)
        fcst_indices = np.array(case_fcst_hours, dtype='int') // time_incr
        var_instance = ws.get_var('24hrain', (fcst_indices, level_indices))          
        datatable_case[iinit, ...] = var_instance.data
        ws.close()

    # close the netCDF file handles and nc package for nasty issues with Nio
    for data in data_list:
        data.close()
    del tmp_datatable
    del nc

    t1 = time.time()
    print('对指定预报面高度列表和指定的预报时效列表做平均结束, 用时{} seconds.'.format(str(t1-t0)[:7]))

    global_package = dict()
    global_names = ['time_indices', 'time_incr', 
                    'levels', 'TLON', 'TLAT', 'lon', 'lat', 
                    'var_time_indices']
    for global_name in global_names:
        global_package[global_name] = locals()[global_name]

    return global_package, datatable, datatable_case

# pickle the data for ploting
@DATAdecorator('./', False, FNL_DATA_PKLNAME)
def get_FNL_data():

    # 3.0 读取FNL数据
    print('3.0 开始读取FNL数据')
    t0 = time.time()

    import Nio
    
    init_datetimes = np.array([dt.datetime.strptime(itime, "%Y%m%d%H") for itime in timelines])

    fnl_datetime_set = set()

    for var in st_vars:
        if var in noFNL_vars:
            continue

        time_indices_var = var_time_indices[var]
        for time_index in time_indices_var:
            new = set(init_datetimes + dt.timedelta(hours=int(time_index*time_incr)))
            fnl_datetime_set = fnl_datetime_set.union(new)
    
    if len(fnl_datetime_set) == 0:
        return None

    fnl_data_dic = dict()
    for fnl_datetime in fnl_datetime_set:
        fnl_filename = fnl_datetime.strftime("fnl_%Y%m%d_%H_00.grib2")
        fnl_timestr = fnl_datetime.strftime("%Y%m%d%H")

        if not os.path.exists(fnl_dir+os.sep+fnl_datetime.strftime("%Y")+os.sep+fnl_filename):
            raise IOError('{} file not found under dir {}'.format(fnl_filename, fnl_dir+os.sep+fnl_datetime.strftime("%Y"))+os.sep)
        fnl_data_dic[fnl_timestr] = Nio.open_file(fnl_dir+os.sep+fnl_datetime.strftime("%Y")+os.sep+fnl_filename, 'r')

    t1 = time.time()
    print('读取FNL数据结束, 用时{} seconds.'.format(str(t1-t0)[:7]))

    # 4.0 对FNL数据进行插值
    print('4.0 对FNL数据进行插值')
    t0 = time.time()
    
    sample = list(fnl_data_dic.values())[0]
    
    fnl_levels = (sample.variables['lv_ISBL0'][:] / 100.).tolist()  # [Pa] --> [hPa]

    # if run in interp-mode, then we interp all the levels in ex_levels 
    level_indices_fnl_interp = np.array([fnl_levels.index(ex_level) for ex_level in ex_levels], dtype='int')
    level_indices_fnl_plot = np.array([fnl_levels.index(st_level) for st_level in st_levels], dtype='int')

    select_table = np.zeros((len(ex_levels)), dtype='bool')
    for iindex, level_index_fnl_interp in enumerate(level_indices_fnl_interp):
        if level_index_fnl_interp in level_indices_fnl_plot:
            select_table[iindex] = True

    tmp_datatable = np.zeros((len(st_vars), len(time_indices), len(st_levels), len(lat), len(lon)), dtype='float32')
    
    # we use a data cache to avoid repeated interpolation for the same dataset

    # time_indices always have the largest dimension among var_time_indices

    def get_FNL_worker(var, fnl_datetime):
        if run_mode == 'plot':
            msg = "FNL interpolated data {}_{}.pkl not found, please report this to developers of this script, ploting abort...".format(
                var, fnl_datetime)
            raise IOError(msg)

        ws = FNLWorkStation(fnl_data_dic[fnl_datetime], fnl_varname, TLAT.T, TLON.T)
        FNL_data = ws.get_var(var, level_indices_fnl_interp, interp=True).data
        ws.close()
        return FNL_data

    dds = DumpDataSet(dump_dir, get_FNL_worker)
    for ivar, var in enumerate(st_vars):
        print('\t变量:{}'.format(var))
        if var in noFNL_vars:
            continue
                
        time_indices_var = var_time_indices[var]
        ndim = var_ndims[var]

        for iinittime, inittime_str in enumerate(timelines):
            print('\t\t起报时间:{}'.format(inittime_str))
            for ifcsttime, time_index in enumerate(time_indices_var):
                fnl_datetime = (dt.datetime.strptime(inittime_str, '%Y%m%d%H') + \
                    dt.timedelta(hours=int(time_indices_var[ifcsttime]*time_incr))).strftime('%Y%m%d%H')

                FNL_data = dds.get_data(var, fnl_datetime)

                if ndim == 4:
                    tmp_datatable[ivar, ifcsttime, ...] += FNL_data[select_table]               
                elif ndim == 3:
                    tmp_datatable[ivar, ifcsttime, 0, ...] += FNL_data

    if remove_dump:
        dds.close()
    
    datatable = tmp_datatable / len(timelines)

    # close the file handle    
    for fnl_data in fnl_data_dic.values():
        fnl_data.close()
    del tmp_datatable
    del Nio

    t1 = time.time()
    print('对FNL数据进行插值, 用时{} seconds.'.format(str(t1-t0)[:7]))

    return datatable


@DATAdecorator('./', True, OBS_DATA_PKLNAME)
def get_OBS_data():

    # 3.0 读取FNL数据
    print('5.0 开始读取OBS数据')
    t0 = time.time()
    
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

    t1 = time.time()
    print('读取OBS数据结束, 用时{} seconds.'.format(str(t1-t0)[:7]))

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
    if run_mode == 'interp':
        print('Successfully interpolated FNL data from {} to {}'.format(start_ddate, end_ddate))
        exit()
    datatable_obs = get_OBS_data()

    # exit()

    makenewdir(pic_dir)
    if clean_plot:
        os.system('rm -rf {}/*'.format(pic_dir))
    makenewdir(origin_dir)
    
    if plot_cases:
        makenewdir(case_dir)
        print('开始作图: 案例')
        for iinit, case_ini_time in enumerate(case_ini_times):
            for ifcst, case_fcst_hour in enumerate(case_fcst_hours):
                dataframe_obs = datatable_obs[case_ini_time][case_fcst_hour]
                dataframe_grapes = datatable_case_grapes[iinit, ifcst, ...]
                title    = 'Prediction and Observation of {}hr 24hours precipitation [mm]'.format(case_fcst_hour)
                subtitle = 'Init: {} UTC'.format(case_ini_time)
                pic_file = 'case_{}_{}hr_24hrain.png'.format(case_ini_time, case_fcst_hour)

                print('\t{}'.format(pic_file))
                plot_case(dataframe_grapes, dataframe_obs, lon, lat, title, subtitle, pic_file, newcolorscheme)

    # exit()

    var_plot_areas = dict()

    # begin to plot
    for plot_type in plot_types:
        print('开始作图: {}'.format(plot_types_name[plot_type]))
        for ivar, var in enumerate(st_vars):
            print('\t变量: {}'.format(var))
            # No FNL data for '24hrain'
            if var in noFNL_vars and plot_type in ['F', 'GMF']:
                continue
            varname = variable_name[var]

            time_indices_var = var_time_indices[var]

            # get plot_areas_var
            for key in plot_areas.keys():
                if var in key.split():
                    plot_areas_var = plot_areas[key]
            if 'plot_areas_var' not in locals().keys():
                raise KeyError('plot_area not defined for var:{}'.format(var))
            var_plot_areas[var] = plot_areas_var

            var_dir = os.path.join(origin_dir, var)
            makenewdir(var_dir)

            for iarea in plot_areas_var:
                print('\t\t区域: {}'.format(iarea))
                for itime,time_index in enumerate(time_indices_var):
                    
                    if var not in clevel_custom.keys():
                        if plot_type in ['G', 'F']:    
                            dlevel = clevel_step[var]
                        elif plot_type == 'GMF':
                            dlevel = clevel_step_PMF[var]

                    p = Pool(len(st_levels))
                    for ilevel,level in enumerate(st_levels):

                        if plot_type == 'G':
                            data = datatable_grapes[ivar, itime, ilevel, ...]
                        elif plot_type == 'F':
                            data = datatable_fnl[ivar, itime, ilevel, ...]
                        elif plot_type == 'GMF':
                            data = datatable_grapes[ivar, itime, ilevel, ...] - \
                                datatable_fnl[ivar, itime, ilevel, ...]

                        # print(data.min())
                        # print(data.max())

                        if var in clevel_custom.keys(): 
                            clevels = np.array(clevel_custom[var])
                        else:
                            if var in noFNL_vars:
                                clevel_data = datatable_grapes[ivar, itime, ilevel, ...]
                            elif plot_type in ['G', 'F']:
                                clevel_data = datatable_fnl[ivar, itime, ilevel, ...]
                            elif plot_type in ['GMF']:
                                # the biggest forecast range have large clevels
                                clevel_data = datatable_grapes[ivar, len(time_indices_var)-1, ilevel, ...] - \
                                    datatable_fnl[ivar, len(time_indices_var)-1, ilevel, ...]
                            
                            clevels = find_clevels(iarea, clevel_data, lon, lat, dlevel, plot_type)
                        
                        # print(clevels)
                        
                        if var in daymean_vars:
                            timestr = '{}-{}'.format(time_index*time_incr-24, time_index*time_incr)
                        else:
                            timestr = '{}'.format(time_index*time_incr)

                        # 3D or surface vars
                        if var_ndims[var] == 4:
                            if len(varname) < 20:
                                title = '{} of {}hr {}hPa {}'.format(plot_types_name[plot_type], timestr, int(level), varname)
                            else:
                                title = ['{} of {}hr {}hPa'.format(plot_types_name[plot_type], timestr, int(level)),
                                         r'{}'.format(varname)]
                            subtitle = 'Init: {} UTC - {} UTC'.format(start_ddate, end_ddate)
                            pic_file = '{}_{}_{}hr_{}hpa_{}.png'.format(plot_type, iarea, time_index*time_incr, int(level), var)

                            print('\t\t\t'+pic_file)

                            # p.apply_async(plot_data, args=(data, plot_type, var, varname, lon, lat, iarea, title, subtitle, pic_file, clevels))
                            plot_data(data, plot_type, var, varname, lon, lat, iarea, title, subtitle, pic_file, clevels)
                        elif var_ndims[var] == 3:
                            if len(varname) < 20:
                                title    = '{} of {}hr {}'.format(plot_types_name[plot_type], timestr, varname)
                            else:
                                title    = ['{} of {}hr'.format(plot_types_name[plot_type], timestr),
                                            r'{}'.format(varname)]
                            subtitle = 'Init: {} UTC - {} UTC'.format(start_ddate, end_ddate)
                            pic_file = '{}_{}_{}hr_{}.png'.format(plot_type, iarea, time_index*time_incr, var)

                            print('\t\t\t'+pic_file)

                            plot_data(data, plot_type, var, varname, lon, lat, iarea, title, subtitle, pic_file, clevels)
                            break

                    p.close()
                    p.join()

    if make_comp:
        makenewdir(comp_dir)
        make_comp_pic(var_time_indices, var_ndims, var_plot_areas, time_incr)
    
    if make_gif:
        makenewdir(gif_dir)
        make_gif_pic(var_time_indices, var_ndims, var_plot_areas, time_incr)
