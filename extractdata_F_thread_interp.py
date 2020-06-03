# -*- coding: utf-8 -*- 
"""
Extract data from Grads data
2018.03.23
@author:wanghao
"""
import sys
sys.path.append('./Cmodule')
sys.path.append('/g3/wanghao/Python/Cmodule/GRAPES_VS_FNL')
from CTLExtract import CTLExtract
from CTLReader import CTLReader
from gen_timelines import gen_timelines
from transf2nc_F_interp import transf2nc_F_interp
import os
import datetime
import time
from utils import config_list
from queue import Queue
from threading import Thread
from asciiio import generate_generalctl
import xarray as xr
import numpy as np
import collections
import re

def ETexe(ddate):
    ts = time.time() 
    ctlfilename =   '{}/post.ctl_{}'.format(ctlfile_dir,ddate)

    ex_ctl  = '{}/postvar{}.ctl'.format(exdata_dir,ddate)
    ex_data = '{}/postvar{}.dat'.format(exdata_dir,ddate)
    
    interp2fnl_ctl  = '{}/postvar{}_interp2fnl.ctl'.format(exdata_dir,ddate)
    interp2fnl_data = '{}/postvar{}_interp2fnl.dat'.format(exdata_dir,ddate)

    ex_nc   = '{}/postvar{}.nc'.format(exdata_dir,ddate)

    # 1.0 Extract need variables 
    print('--- 1.0 begin extract data ---')
    CTLExtract(ctlfilename,ex_vars,ex_levels,ex_ctl,ex_data,ddate)
    os.system('rm extract_{}.gs'.format(ddate))
    print('finish extract data!')
    
    # 2.0 interpolation, grapes2fnl resolution
    print('--- 2.0 begin to interp postvar data ---')
    data = CTLReader(ex_ctl, ex_vars)
    lat, lon = data.variables["latitude"][:],  data.variables["longitude"][:]
    levels = data.variables["levels"][:]

    # 需要插值的网格
    interp_slat, interp_elat, interp_dlat = -89., 89.1, 1.0
    interp_slon, interp_elon, interp_dlon =   0., 359.1, 1.0
    
    interp_lat = np.arange(interp_slat, interp_elat, interp_dlat)
    interp_lon = np.arange(interp_slon, interp_elon, interp_dlon)
    interp_nlat, interp_nlon = len(interp_lat), len(interp_lon)
    interp_info_ml = {"slat":interp_slat, "elat":interp_elat, "dlat":interp_dlat, "nlat":interp_nlat,
                      "slon":interp_slon, "elon":interp_elon, "dlon":interp_dlon, "nlon":interp_nlon,
                      "levels":levels,"ddate":ddate}
    interp_info_sl = {"slat":interp_slat, "elat":interp_elat, "dlat":interp_dlat, "nlat":interp_nlat,
                      "slon":interp_slon, "elon":interp_elon, "dlon":interp_dlon, "nlon":interp_nlon,
                      "ddate":ddate}
    parsed_time_list = data.variables["time"][:]

    ##数据coords赋值, ml:multilevels,sl:singlelevel
    var_info_ml = collections.OrderedDict()
    var_info_sl = collections.OrderedDict()
    for ivar in interp2fnl_vars:
        if data.variables[ivar].dimensions['levels'] > 1:
            info_ml = {ivar : (["time", "level", "lat", "lon"],  data.variables[ivar][:])}
            var_info_ml.update(info_ml)
        elif data.variables[ivar].dimensions['levels'] == 1:
            info_sl = {ivar : (["time","level", "lat", "lon"],  data.variables[ivar][:])}
            var_info_sl.update(info_sl)
        
    coords_ds_ml = xr.Dataset(var_info_ml,
                       coords={"lon": lon,"lat": lat,
                               "level": levels,"time": parsed_time_list})
    
    coords_ds_sl = xr.Dataset(var_info_sl,
                       coords={"lon": lon,"lat": lat, 
                               "level": [1000], "time": parsed_time_list})

    interp_ds_ml = coords_ds_ml.interp(lat=interp_lat, lon=interp_lon, method="linear") #插值
    interp_ds_sl = coords_ds_sl.interp(lat=interp_lat, lon=interp_lon, method="linear") #插值
    
    # output grads format file
    output_grads_file = open('{}'.format(interp2fnl_data),'wb')
    for itime in np.arange(0,data.dimensions['time']):
        for ivar in interp2fnl_vars:
            if data.variables[ivar].dimensions['levels'] > 1:
                np.float32(interp_ds_ml[ivar][itime,...]).tofile(output_grads_file)
            if data.variables[ivar].dimensions['levels'] == 1:
                np.float32(interp_ds_sl[ivar][itime,...].values).tofile(output_grads_file)
    output_grads_file.close()
    
    interp_fili = open(interp2fnl_ctl,'w')
    ex_fili = open(ex_ctl,'r')
    for iline in ex_fili.read().split('\n'):  
         if 'xdef' in iline:
            iline = 'xdef {} linear {} {}'.format(interp_nlon,interp_slon,interp_dlon)
         if 'ydef' in iline:
            iline = 'ydef {} linear {} {}'.format(interp_nlat,interp_slat,interp_dlat)
         if 'vars' in iline:
            iline = 'vars {}'.format(len(interp2fnl_vars))
         interp_fili.write(iline+'\n')
         if iline.startswith('vars'):
            break
    ex_fili.close()
            
    ex_fili = open(ex_ctl,'r')
    read = False
    for iline in ex_fili.read().split('\n'):
        if iline.startswith('endvars'):
            interp_fili.write(iline)
            read = False
        if read:
            p = re.compile('(\w+)\s+(\d+)\s+(\d+)\s+(.*)')    #目标变量行的正则范式
            m = p.match(iline)
            if m.group(1) in interp2fnl_vars:
                interp_fili.write(iline+'\n')
        if iline.startswith('vars'):
            read = True
    ex_fili.close()
    
    interp_fili.close()

    # 3.0 Transfer to NetCDF Format 
    print('--- 3.0 begin transfer data ---')
    transf2nc_F_interp(ex_ctl,interp2fnl_ctl,ex_data,interp2fnl_data,ex_nc,ddate)
    # os.system('NETCDF=/g1/app/mathlib/netcdf/4.4.0/intel')
    os.system('ifort grapes2nc_'+ddate+'.f90'+' -I${NETCDF}/include/ -L${NETCDF}/lib -lnetcdff -lnetcdf -o grapes2nc_'+ddate+'.exe')
    os.system('./grapes2nc_{}.exe'.format(ddate)) 
    print('finish transfer data')
    
    os.system('rm {} {}'.format(ex_ctl, ex_data))
    os.system('rm {} {}'.format(interp2fnl_ctl, interp2fnl_data))  

class ETWorker(Thread):
     def __init__(self, queue):
         Thread.__init__(self)
         self.queue = queue
                     
     def run(self):
         while True:
             # 从队列中获取任务并扩展tuple
             riqi = self.queue.get()
             ETexe(riqi)
             self.queue.task_done()

# Main Program
if __name__ == '__main__':
    # read the config file
    CONFIGPATH = './config/' # default config path
    cong = config_list(CONFIGPATH, ['config.yml', 'devconfig.yml'])
    for key, value in cong.items():
         locals()[key] = value

    # 参数设置
    ts = time.time()
    timelines   = gen_timelines(start_ddate, end_ddate, fcst_step)
    
    print(exprs)
    # print(exprs.keys())

    for iexpr,idir in zip(list(exprs.keys()),list(exprs.values())):
        print(iexpr,idir)
        # 制作ctl描述文件
        ctlfile_dir = idir
        generate_generalctl(timelines, ctlfile_dir)

        # 创建数据提取路径
        exdata_dir = exdata_root_dir + iexpr
        if not os.path.exists(exdata_dir):
            os.makedirs(exdata_dir)

        #创建一个主进程与工作进程通信
        queue = Queue()
        #创建31个工作线程
        for x in range(11):
            worker = ETWorker(queue)
            #将daemon设置为True将会使主线程退出，即使所有worker都阻塞了
            worker.daemon = True
            worker.start()
    
        #将任务以tuple的形式放入队列中
        for link in timelines:
            queue.put((link))
    
        #让主线程等待队列完成所有的任务
        queue.join()
        # os.system('rm grapes2nc.f90 grapes2nc.exe')
        print('Took {}'.format(time.time() - ts))
