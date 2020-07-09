#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: Hejun Xie
@LastEditTime: 2020-07-09 17:28:57
@Description: Process and plot postvar
Version: 1.9.2-alpha
Release Date: 2020/6/23
'''

import sys
sys.path.append('./Cmodule')
sys.path.append('/g3/wanghao/Python/Cmodule/GRAPES_VS_FNL')
import numpy as np
import numpy.ma as ma
import time
import datetime as dt
from gen_timelines import gen_timelines
import os
import glob
from multiprocessing import Pool

from utils import DATADumpManager, config_list, hashlist, makenewdir, DumpDataSet
from derived_vars import FNLWorkStation, GRAPESWorkStation
from asciiio import read_obs
from plotmap import plot_data, find_clevels, find_statistics, plot_case, clip_china_data, \
                    plot_data_zonal, find_clevels_zonal
from make_comp import make_comp_pic, make_gif_pic

# read the config file

CONFIGPATH = './config/' # default config path
cong = config_list(CONFIGPATH, ['config.yml', 'devconfig.yml'])

# config script
for key, value in cong.items():
    globals()[key] = value

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

def get_GRAPES_data(exdata_dir):

    # 1.0 读取postvar数据
    print('1.0 开始读取postvar数据')
    import netCDF4 as nc
    t0 = time.time()
    data_list = []

    ncfiles = ['postvar{}.nc'.format(itime) for itime in timelines]

    if run_mode == 'interp':
        if not os.path.exists(nc_sample):
            raise IOError('{} file not found under dir {}'.format(ifile, exdata_dir))
        sample = nc.Dataset(nc_sample, 'r')
    else:
        for ifile in ncfiles:
            if not os.path.exists(os.path.join(exdata_dir, ifile)):
                raise IOError('{} file not found under dir {}'.format(ifile, exdata_dir))
            data_list.append(nc.Dataset(os.path.join(exdata_dir, ifile), 'r'))
        sample = data_list[0]

    t1 = time.time()
    print('postvar数据读取结束, 用时{} seconds.'.format(str(t1-t0)[:7]))

    lat, lon  = sample.variables['lat'][:], sample.variables['lon'][:]
    interp2fnl_lat, interp2fnl_lon = sample.variables['lat_2'][:], sample.variables['lon_2'][:]
    TLAT, TLON  = np.meshgrid(lat, lon)
    levels    = sample.variables['lev'][:].tolist()
    times     = sample.variables['time'][:]
    times = [(dt.datetime(1,1,1) + dt.timedelta(hours=time) - dt.timedelta(days=2)).strftime('%Y%m%d%H') for time in times]
    time_incr = int(sample.variables['time'][1] - sample.variables['time'][0]) # hour
    
    time_indices = np.array([int(i/time_incr) for i in fcst], dtype='int')
    level_indices = np.array([levels.index(st_level) for st_level in st_levels], dtype='int')

    var_time_indices = dict()
    for ivar, var in enumerate(st_vars):
        var_time_indices[var] = get_time_indices(var, time_indices, time_incr, times)

    # 2.0 对指定高度和指定的预报时效做平均
    print('2.0 对指定预报面高度列表和指定的预报时效列表做平均')
    t0 = time.time()

    # [A]. initialize the datatable
    datatable = {}
    for var in st_vars:
        if var not in noFNL_vars:
            datatable[var] = np.zeros((len(time_indices), len(st_levels), len(interp2fnl_lat), len(interp2fnl_lon)), dtype='float32')
        else:
            datatable[var] = np.zeros((len(time_indices), len(st_levels), len(lat), len(lon)), dtype='float32')

    # [B]. fill in the datatable
    for idata, data in enumerate(data_list):
        ws = GRAPESWorkStation(data, grapes_varname)
        for var in st_vars:
            time_indices_var = var_time_indices[var]
            var_instance = ws.get_var(var, (time_indices_var, level_indices)).data
            if var_ndims[var] == 4:
                datatable[var][:len(time_indices_var), ...] += var_instance
            elif var_ndims[var] == 3:
                datatable[var][:len(time_indices_var), 0, ...] += var_instance
        ws.close()
    
    # [C]. get mean datatable
    for var in st_vars:
        datatable[var] /= len(timelines)

    # get case data
    if plot_cases:
        datatable_case = np.zeros((len(case_ini_times), len(case_fcst_hours), len(lat), len(lon)), dtype='float32')
        for iinit, case_ini_time in enumerate(case_ini_times):
            init_index = timelines.index(case_ini_time)
            data = data_list[init_index]

            ws = GRAPESWorkStation(data, grapes_varname)
            fcst_indices = np.array(case_fcst_hours, dtype='int') // time_incr
            var_instance = ws.get_var('24hrain', (fcst_indices, level_indices))          
            datatable_case[iinit, ...] = var_instance.data
            ws.close()
    else:
        datatable_case = None

    # close the netCDF file handles and nc package for nasty issues with Nio
    for data in data_list:
        data.close()
    del nc

    t1 = time.time()
    print('对指定预报面高度列表和指定的预报时效列表做平均结束, 用时{} seconds.'.format(str(t1-t0)[:7]))

    global_package = dict()
    global_names = ['time_indices', 'time_incr', 
                    'levels', 'TLON', 'TLAT', 'lon', 'lat', 'interp2fnl_lat', 'interp2fnl_lon', 
                    'var_time_indices']
    for global_name in global_names:
        global_package[global_name] = locals()[global_name]

    return global_package, datatable, datatable_case


def deletelevel(oldfile):
    year = oldfile.split('/')[-2]
    filename = oldfile.split('/')[-1]
    makenewdir(os.path.join(temp_fnl_dir, year))
    newfile = os.path.join(temp_fnl_dir, year, filename)
    command = 'cdo delete,name=gh,t,level=1500,4000 {} {}'.format(oldfile, newfile)
    os.system(command)
    return newfile

def get_FNL_data():

    # 3.0 读取FNL数据
    print('3.0 开始读取FNL数据')
    t0 = time.time()

    from nwpc_data.grib.eccodes import load_field_from_file
    
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
        fnl_data_dic[fnl_timestr] = fnl_dir+os.sep+fnl_datetime.strftime("%Y")+os.sep+fnl_filename

    t1 = time.time()
    print('读取FNL数据结束, 用时{} seconds.'.format(str(t1-t0)[:7]))

    # 4.0 对FNL数据进行计算平均
    print('4.0 对FNL数据计算平均')
    t0 = time.time()
    
    sample_file = list(fnl_data_dic.values())[0]
    sample_field = load_field_from_file(
        file_path = sample_file,
        parameter = "u",
        level_type = "isobaricInhPa",
        level = None,
    )
    
    fnl_levels = sample_field.coords['isobaricInhPa'].values.tolist()

    # if run in interp-mode, then we interp all the levels in ex_levels 
    level_indices_fnl = np.array([fnl_levels.index(st_level) for st_level in st_levels], dtype='int')

    # [A]. initialize the datatable
    datatable = {}
    for var in st_vars:
        if var not in noFNL_vars:
            datatable[var] = np.zeros((len(time_indices), len(st_levels), len(interp2fnl_lat), len(interp2fnl_lon)), dtype='float32')
    
    # [B]. fill in the datatable
    # time_indices always have the largest dimension among var_time_indices
    def get_FNL_worker(var, fnl_datetime):
        if temp_fnl_dir not in fnl_data_dic[fnl_datetime]:
            fnl_data_dic[fnl_datetime] = deletelevel(fnl_data_dic[fnl_datetime])
        ws = FNLWorkStation(fnl_data_dic[fnl_datetime], fnl_varname, TLAT.T, TLON.T, sample_field)
        FNL_data = ws.get_var(var, level_indices_fnl, interp=False, strip=True).data
        ws.close()
        return FNL_data

    dds = DumpDataSet(dump_dir, get_FNL_worker)
    for var in st_vars:
        if run_mode == 'debug':
            print('\t变量:{}'.format(var)) 
        if var in noFNL_vars:
            continue

        time_indices_var = var_time_indices[var]
        ndim = var_ndims[var]

        for iinittime, inittime_str in enumerate(timelines):
            if run_mode == 'debug':
                print('\t\t起报时间:{}'.format(inittime_str)) 
            for ifcsttime, time_index in enumerate(time_indices_var):
                fnl_datetime = (dt.datetime.strptime(inittime_str, '%Y%m%d%H') + \
                    dt.timedelta(hours=int(time_indices_var[ifcsttime]*time_incr))).strftime('%Y%m%d%H')

                FNL_data = dds.get_data(var, fnl_datetime)

                if ndim == 4:
                    datatable[var][ifcsttime, ...] += FNL_data               
                elif ndim == 3:
                    datatable[var][ifcsttime, 0, ...] += FNL_data

    if remove_dump:
        dds.close()
        os.system('rm {}/*/*.grib2'.format(temp_fnl_dir))
    
    # [C]. get mean datatable
    for var in st_vars:
        if var not in noFNL_vars:
            datatable[var] /= len(timelines)

    # close the file handle    
    del fnl_data_dic
    del load_field_from_file

    t1 = time.time()
    print('对FNL数据计算平均, 用时{} seconds.'.format(str(t1-t0)[:7]))

    return datatable


def get_OBS_data():

    # 5.0 读取OBS数据
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

def get_gridrain_data(datafile, datatype, sample=False):
    '''
    Input:
        datafile: filename of gridrain data, contain the time stamp as: YYMMDDHH
        datatype: 'type1' or 'type2', see config.yaml
        sample: True or False
    
    Output:
        if sample == False then return rain data
        if sample == True then return latitude and longitude
    '''


    if datatype == 'type1':
        rootgrp = nc.Dataset(datafile, 'r')
    elif datatype == 'type2':
        ddate = os.path.basename(datafile).split('.')[-2].split('-')[-1]
        ctlfile = './temp/cmp_pre_ctls/cmp_pre_{}.ctl'.format(ddate)
        gen_cmp_pre_ctl(ctlfile,ddate,gridrain[datatype]['gridrain_dir'])

        rootgrp = CTLReader(ctlfile, ['crain'])
    
    if sample:
        return rootgrp.variables['latitude'][:], rootgrp.variables['longitude'][:]
    else:
        if datatype == 'type1':
            grdata = rootgrp.variables['rain'][0, ...]
        elif datatype == 'type2':
            grdata = rootgrp.variables['crain'][0][0, ...]
        grdata[grdata < 0.] = 0.
        return grdata

def get_GRIDRAIN_data():
    
    # 6.0 读取GRIDRAIN数据
    print('6.0 开始读取GRIDRAIN数据')
    t0 = time.time()

    if use_gridrain_type == 'type1':
        global nc
        import netCDF4 as nc
    elif use_gridrain_type == 'type2':
        global CTLReader, gen_cmp_pre_ctl
        from CTLReader import CTLReader
        from utils import gen_cmp_pre_ctl

    time_indices_var = var_time_indices['24hrain']

    if not os.path.exists(gridrain[use_gridrain_type]['gridrain_sample']):
        raise IOError('{} gridrain sample not found'.format(gridrain_sample))
    
    gridrain_lat, gridrain_lon = get_gridrain_data(gridrain[use_gridrain_type]['gridrain_sample'], use_gridrain_type, sample=True)

    rain = get_gridrain_data(gridrain[use_gridrain_type]['gridrain_sample'], use_gridrain_type, False)
    # exit()

    datacache = dict()
    datatable = np.zeros((len(time_indices), len(gridrain_lat), len(gridrain_lon)), dtype='float32')

    for iinittime, inittime_str in enumerate(timelines):
        if run_mode != 'plot':
            print('\t\t起报时间:{}'.format(inittime_str)) 
        for ifcsttime, time_index in enumerate(time_indices_var):
            gridrain_datetime = (dt.datetime.strptime(inittime_str, '%Y%m%d%H') + \
                dt.timedelta(hours=int(time_indices_var[ifcsttime]*time_incr))).strftime('%Y%m%d')
            
            if gridrain_datetime in datacache.keys():
                datatable[ifcsttime, ...] += datacache[gridrain_datetime]
                continue
            
            if use_gridrain_type == 'type1':
                match = '{}/{}/*-{}*.nc'.format(gridrain[use_gridrain_type]['gridrain_dir'], gridrain_datetime, gridrain_datetime)
            elif use_gridrain_type == 'type2':
                match = '{}/*-{}*.grd'.format(gridrain[use_gridrain_type]['gridrain_dir'], gridrain_datetime)
            
            gridrain_files = glob.glob(match)
            if len( gridrain_files) != 24:
                print(gridrain_files)
                print(len( gridrain_files))
                raise IOError('integrity of 24h gridrain for {} failed'.format(gridrain_datetime))

            grdata_ls = list()
            for gridrain_file in gridrain_files:
                grdata = get_gridrain_data(gridrain_file, use_gridrain_type, sample=False)
                grdata_ls.append(grdata)
            dayrain = np.sum(grdata_ls, axis=0)
            
            datacache[gridrain_datetime] = dayrain
            datatable[ifcsttime, ...] += dayrain

    datatable = datatable / len(timelines)

    # clean
    for data in datacache.values():
        del data
    del datacache
    if use_gridrain_type == 'type1':
        del nc
    elif use_gridrain_type == 'type2':
        del CTLReader, gen_cmp_pre_ctl
    t1 = time.time()
    print('读取GRIDRAIN数据结束, 用时{} seconds.'.format(str(t1-t0)[:7]))

    return datatable, gridrain_lat, gridrain_lon

def plot(pic_dir, datatable_grapes, datatable_case_grapes, datatable_grapes_zero, expr_name, iexpr):

    global fnl_pics

    origin_dir = os.path.join(pic_dir, origin)
    comp_dir = os.path.join(pic_dir, comp)
    gif_dir = os.path.join(pic_dir, gif)
    case_dir = os.path.join(pic_dir, case)
    zonalmean_dir = os.path.join(pic_dir, zonalmean)

    # config submodules
    import plotmap, make_comp
    plotmap.config_submodule(cong, pic_dir, expr_name)
    make_comp.config_submodule(cong, pic_dir)


    makenewdir(pic_dir)
    if clean_plot:
        os.system('rm -rf {}/*'.format(pic_dir))
    makenewdir(origin_dir)
    if plot_zonalmean:
        makenewdir(zonalmean_dir)
    
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
        
        if iexpr != 0 and plot_type == 'F':
            print("Copy fnl files from first experiment")
            for fnl_pic in fnl_pics:
                fnl_pic_segments = fnl_pic.split('/')
                fnl_pic_segments[-4] = expr_name
                new_fnl_pic = '/'.join(fnl_pic_segments)

                command = "cp {} {}".format(fnl_pic, new_fnl_pic)
                print(command)
                os.system(command)
            continue
        
        # skip CTRL for GMG
        if iexpr == 0 and plot_type == 'GMG':
            continue


        print('开始作图: {}'.format(plot_types_name[plot_type]))
        for ivar, var in enumerate(st_vars):
            # special case for GRIDRAIN data
            if var in noFNL_vars and plot_type in ['F', 'GMF'] and \
                not (var == '24hrain' and plot_type == 'F'):
                continue
            print('\t变量: {}'.format(var))
            varname = variable_name[var]

            time_indices_var = var_time_indices[var]

            # get plot_areas_var
            for key in plot_areas.keys():
                if var in key.split():
                    plot_areas_var = plot_areas[key]
            if 'plot_areas_var' not in locals().keys():
                raise KeyError('plot_area not defined for var:{}'.format(var))
            var_plot_areas[var] = plot_areas_var

            var_dir_origin = os.path.join(origin_dir, var)
            makenewdir(var_dir_origin)

            if plot_zonalmean:
                var_dir_zonalmean = os.path.join(zonalmean_dir, var)
                makenewdir(var_dir_zonalmean)

            for iarea in plot_areas_var:
                # special case for GRIDRAIN data
                if var == '24hrain' and plot_type == 'F' and iarea!='E_Asia':
                    continue
                print('\t\t区域: {}'.format(iarea))
                for itime,time_index in enumerate(time_indices_var):
                    # [I]. plot data on isobaric surfaces
                    if var not in clevel_custom.keys():
                        if plot_type in ['G', 'F']:    
                            dlevel = clevel_step[var]
                        elif plot_type in ['GMF', 'GMG']:
                            dlevel = clevel_step_PMF[var]
                    
                    for level in plot_levels:
                        # continue
                        if var_ndims[var] == 4:
                            ilevel = st_levels.index(level)
                        else:
                            ilevel = 0
                        
                        # [A]. find plot_lat, plot_lon, plot_typelabel
                        if var == '24hrain' and plot_type == 'F':
                            plot_lat, plot_lon = gridrain_lat, gridrain_lon
                            plot_typelabel = 'OBS:CMP'
                        elif var in noFNL_vars:
                            plot_lat, plot_lon = lat, lon
                            plot_typelabel = plot_types_name[plot_type]
                        else:
                            plot_lat, plot_lon = interp2fnl_lat, interp2fnl_lon
                            plot_typelabel = plot_types_name[plot_type]
                        
                        # [B]. find data
                        if plot_type == 'G':
                            data = datatable_grapes[var][itime, ilevel, ...]
                        elif plot_type == 'F':
                            if var != '24hrain':
                                data = datatable_fnl[var][itime, ilevel, ...]
                            else:
                                data = datatable_gridrain[itime, ...]
                        elif plot_type == 'GMF':
                            data = datatable_grapes[var][itime, ilevel, ...] - \
                                datatable_fnl[var][itime, ilevel, ...]
                        elif plot_type == 'GMG':
                            data = datatable_grapes[var][itime, ilevel, ...] - \
                                datatable_grapes_zero[var][itime, ilevel, ...]

                        # [C]. find clevels
                        if plot_type in ['G', 'F'] and var in clevel_custom.keys(): 
                            clevels = np.array(clevel_custom[var])
                        elif plot_type in ['GMF', 'GMG'] and var in clevel_custom_PMF.keys():
                            clevels = np.array(clevel_custom_PMF[var])
                            # print(clevels)
                        else:
                            if var in noFNL_vars:
                                clevel_data = datatable_grapes_zero[var][itime, ilevel, ...]
                            elif plot_type in ['G', 'F']:
                                clevel_data = datatable_fnl[var][itime, ilevel, ...]
                            elif plot_type in ['GMF', 'GMG']:
                                # the biggest forecast range have large clevels
                                clevel_data = datatable_grapes[var][len(time_indices_var)-1, ilevel, ...] - \
                                    datatable_fnl[var][len(time_indices_var)-1, ilevel, ...]
                            
                            clevels = find_clevels(iarea, clevel_data, plot_lon, plot_lat, dlevel, plot_type)
                        # print(clevels)
                        
                        # [D]. find timestr
                        if var in daymean_vars:
                            timestr = '({:0>3}-{:0>3})'.format(time_index*time_incr-24, time_index*time_incr)
                        elif var in dayacc_vars:
                            timestr = '({:0>3}-{:0>3})'.format(time_index*time_incr, time_index*time_incr+24)
                        else:
                            timestr = '{:0>3}'.format(time_index*time_incr)
                        
                        # [E]. find statistics
                        if var == '24hrain' and iarea == 'E_Asia' and platform != 'Pi':
                            if plot_type == 'F':
                                if 'clip_china_index_gridrain' not in globals().keys():
                                    global clip_china_index_gridrain
                                    st_data, clip_china_index_gridrain = clip_china_data(data, plot_lat, plot_lon)
                                else:
                                    st_data = data.flatten()[clip_china_index_gridrain]
                            elif plot_type == 'G':
                                if 'clip_china_index_grapes' not in globals().keys():
                                    global clip_china_index_grapes
                                    st_data, clip_china_index_grapes = clip_china_data(data, plot_lat, plot_lon)
                                else:
                                    st_data = data.flatten()[clip_china_index_grapes]
                        else:
                            st_data = data

                        if platform == 'Pi' and var == '24hrain' and iarea == 'E_Asia':
                            statistics = None
                        else: 
                            statistics = find_statistics(iarea, st_data, plot_lon, plot_lat)
                        
                        # [F]. get FNL datetime
                        if plot_type == 'F':
                            fnl_start_dt = dt.datetime.strptime(start_ddate, '%Y%m%d%H') + dt.timedelta(hours=int(time_index*time_incr))
                            fnl_end_dt = dt.datetime.strptime(end_ddate, '%Y%m%d%H') + dt.timedelta(hours=int(time_index*time_incr))
                            if var == '24hrain':
                                fnl_start_ddate = fnl_start_dt.strftime("%Y%m%d")
                                fnl_end_ddate = fnl_end_dt.strftime("%Y%m%d")
                            else:
                                fnl_start_ddate = fnl_start_dt.strftime("%Y%m%d%H")
                                fnl_end_ddate = fnl_end_dt.strftime("%Y%m%d%H")

                        # 3D or surface vars
                        if var_ndims[var] == 4:
                            if len(varname) < 20:
                                title = '{} {}hPa {}'.format(plot_typelabel, int(level), varname)  # timestr
                            else:
                                title = ['{} {}hPa'.format(plot_typelabel, int(level)),
                                         r'{}'.format(varname)]
                            if plot_type == 'F':
                                subtitle = 'Init(UTC): {} - {}'.format(fnl_start_ddate, fnl_end_ddate)
                            else:
                                subtitle = 'Init(UTC): {}+{}H - {}+{}H'.format(start_ddate,timestr,end_ddate,timestr)
                            pic_file = '{}_{}_{}hr_{}hpa_{}.png'.format(plot_type, iarea, time_index*time_incr, int(level), var)

                            print('\t\t\t'+pic_file)

                            plot_data(data, plot_type, var, varname, plot_lon, plot_lat, iarea, title, subtitle, pic_file, clevels, statistics)
                        elif var_ndims[var] == 3:
                            if len(varname) < 20:
                                title    = '{} {}'.format(plot_typelabel, varname)
                            else:
                                title    = ['{}'.format(plot_typelabel),
                                            r'{}'.format(varname)]
                            if plot_type == 'F':
                                subtitle = 'Init(UTC): {} - {}'.format(fnl_start_ddate, fnl_end_ddate)
                            else:
                                subtitle = 'Init(UTC): {}+{}H - {}+{}H'.format(start_ddate, timestr, end_ddate, timestr)
                            pic_file = '{}_{}_{}hr_{}.png'.format(plot_type, iarea, time_index*time_incr, var)

                            print('\t\t\t'+pic_file)

                            plot_data(data, plot_type, var, varname, plot_lon, plot_lat, iarea, title, subtitle, pic_file, clevels, statistics)
                            break

                    # [II]. plot zonal averaged data
                    if plot_zonalmean:
                        if var in noFNL_vars or iarea != 'Global':
                            continue

                        if plot_type in ['G', 'F']:    
                            dlevel = clevel_step_zonalmean[var]

                        # [A]. find plot_lat, plot_lon, plot_typelabel
                        plot_lat, plot_lon = interp2fnl_lat, interp2fnl_lon
                        plot_typelabel = plot_types_name[plot_type]
                    
                        # [B]. find data
                        if plot_type == 'G':
                            data = datatable_grapes[var][itime, ...]
                        elif plot_type == 'F':
                            data = datatable_fnl[var][itime, ...]
                        elif plot_type == 'GMF':
                            data = datatable_grapes[var][itime, ...] - \
                                datatable_fnl[var][itime, ...]
                        elif plot_type == 'GMG':
                            data = datatable_grapes[var][itime, ...] - \
                                datatable_grapes_zero[var][itime, ...]
                        # perform zonal average
                        data = np.mean(data, axis=2)

                        # [C]. find clevels
                        if plot_type in ['G', 'F']:
                            clevel_data = datatable_fnl[var][itime, ...]
                            # perform zonal average
                            clevel_data = np.mean(clevel_data, axis=2)
                            clevels = find_clevels_zonal(iarea, clevel_data, plot_lat, dlevel, plot_type)
                        elif plot_type in ['GMF', 'GMG']:
                            clevels = clevel_zonalmean_PMF[var]
                        
                        # [D]. find timestr
                        timestr = '{:0>3}'.format(time_index*time_incr)

                        # [F]. get FNL datetime
                        if plot_type == 'F':
                            fnl_start_dt = dt.datetime.strptime(start_ddate, '%Y%m%d%H') + dt.timedelta(hours=int(time_index*time_incr))
                            fnl_end_dt = dt.datetime.strptime(end_ddate, '%Y%m%d%H') + dt.timedelta(hours=int(time_index*time_incr))
                            fnl_start_ddate = fnl_start_dt.strftime("%Y%m%d%H")
                            fnl_end_ddate = fnl_end_dt.strftime("%Y%m%d%H")
                        
                        if len(varname) < 20:
                            title = '{} Zonal Mean {}'.format(plot_typelabel, varname)  # timestr
                        else:
                            title = ['{} Zonal Mean'.format(plot_typelabel), r'{}'.format(varname)]
                        if plot_type == 'F':
                            subtitle = 'Init(UTC): {} - {}'.format(fnl_start_ddate, fnl_end_ddate)
                        else:
                            subtitle = 'Init(UTC): {}+{}H - {}+{}H'.format(start_ddate,timestr,end_ddate,timestr)
                        pic_file = '{}_{}_{}hr_zonalmean_{}.png'.format(plot_type, iarea, time_index*time_incr, var)

                        plot_data_zonal(data, plot_type, var, varname, plot_lat, iarea, title, subtitle, pic_file, clevels)

                        print('\t\t\t'+pic_file)
                        
                        # exit()

    
    if iexpr == 0:
        fnl_pics = glob.glob("{}/*/F_*.png".format(origin_dir)) + glob.glob("{}/*/F_*.png".format(zonalmean_dir))

    if make_comp:
        makenewdir(comp_dir)
        make_comp_pic(var_time_indices, var_ndims, var_plot_areas, time_incr)
    
    if make_gif:
        makenewdir(gif_dir)
        make_gif_pic(var_time_indices, var_ndims, var_plot_areas, time_incr)


# Main Program
if __name__ == "__main__":

    # mode settings
    GRAPES_PKL = True
    FNL_PKL = True
    OBS_PKL = True
    GRIDRAIN_PKL = True

    if run_mode == 'interp':
        st_vars = plotable_vars
        fcst_step = 6
        FNL_PKL = False
        GRAPES_PKL = False

    if run_mode == 'debug':
        FNL_PKL = False
        GRAPES_PKL = False
        OBS_PKL = False
        GRIDRAIN_PKL = False
    
    if plot_zonalmean:
        st_levels = ex_levels
    else:
        st_levels = plot_levels

    OBS_HASH = hashlist([case_ini_times, case_fcst_hours])
    FNL_HASH = hashlist([st_vars, st_levels, fcst, start_ddate, end_ddate, fcst_step])
    GRIDRAIN_HASH = hashlist([start_ddate, end_ddate])
    OBS_DATA_PKLNAME = './temp/pkl/OBS_{}.pkl'.format(OBS_HASH)
    FNL_DATA_PKLNAME = './temp/pkl/FNL_{}.pkl'.format(FNL_HASH)
    GRIDRAIN_DATA_PKLNAME = './temp/pkl/GRIDRAIN_{}.pkl'.format(GRIDRAIN_HASH)

    ddm_fnl = DATADumpManager('./', FNL_PKL, FNL_DATA_PKLNAME, get_FNL_data)
    ddm_obs = DATADumpManager('./', OBS_PKL, OBS_DATA_PKLNAME, get_OBS_data)
    ddm_gridrain = DATADumpManager('./', GRIDRAIN_PKL, GRIDRAIN_DATA_PKLNAME, get_GRIDRAIN_data) 
    
    # 参数设置
    timelines   = gen_timelines(start_ddate, end_ddate, fcst_step)

    # datatable dimension: (nvars, nfcsrtimes, nlevels, nlat, nlon)
    # [A]. get grapes experiment data
    # dump the data
    for iexpr, expr_name in enumerate(exprs.keys()):
        print("计算试验{}".format(expr_name))
        exdata_dir = os.path.join(exdata_root_dir, expr_name)
        GRAPES_HASH = hashlist([exdata_dir, st_vars, st_levels, fcst, start_ddate, end_ddate, fcst_step, OBS_HASH])
        GRAPES_DATA_PKLNAME = './temp/pkl/GRAPES_{}.pkl'.format(GRAPES_HASH)
        ddm_grapes = DATADumpManager('./', GRAPES_PKL, GRAPES_DATA_PKLNAME, get_GRAPES_data)
        global_package, datatable_grapes, datatable_case_grapes = ddm_grapes.get_data(exdata_dir)
        if iexpr == 0:
            datatable_grapes_zero = datatable_grapes
    # clean the memory
    del datatable_grapes, datatable_case_grapes
    for global_name in global_package.keys():
        globals()[global_name] = global_package[global_name]
    

    # [B]. get FNL data
    datatable_fnl = ddm_fnl.get_data()
    
    # exit()
    # [C]. get OBS data
    if plot_cases:
        datatable_obs = ddm_obs.get_data()
    

    # [D]. get GRIDRAIN data
    if '24hrain' in st_vars:
        if 'E_Asia' in cong['plot_areas']['24hrain']:
            datatable_gridrain, gridrain_lat, gridrain_lon = ddm_gridrain.get_data()
    
    print("Sucessfully loading all the data, start ploting")

    # exit()

    # start ploting
    for iexpr, expr_name in enumerate(exprs.keys()):
        # Load data
        print("从硬盘加载试验{}缓存".format(expr_name))
        exdata_dir = os.path.join(exdata_root_dir, expr_name)
        GRAPES_HASH = hashlist([exdata_dir, st_vars, st_levels, fcst, start_ddate, end_ddate, fcst_step, OBS_HASH])
        GRAPES_DATA_PKLNAME = './temp/pkl/GRAPES_{}.pkl'.format(GRAPES_HASH)
        ddm_grapes = DATADumpManager('./', GRAPES_PKL, GRAPES_DATA_PKLNAME, get_GRAPES_data)
        global_package, datatable_grapes, datatable_case_grapes = ddm_grapes.get_data(exdata_dir)
        
        # plot
        pic_dir = os.path.join(pic_root_dir, expr_name)
        makenewdir(pic_dir)
        plot(pic_dir, datatable_grapes, datatable_case_grapes, datatable_grapes_zero, expr_name, iexpr)

        # clean the memory
        del global_package, datatable_grapes, datatable_case_grapes
