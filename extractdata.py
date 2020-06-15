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
import os
import datetime
import time
from utils import config_list, def_interp_grid
from queue import Queue
from threading import Thread
from asciiio import generate_generalctl
import numpy as np
import collections

def ETexe(ddate):
    ts = time.time() 
    ctlfilename =   '{}/post.ctl_{}'.format(ctlfile_dir,ddate)

    ex_ctl  = '{}/postvar{}.ctl'.format(exdata_dir,ddate)
    ex_data = '{}/postvar{}.dat'.format(exdata_dir,ddate)
    
    interp2fnl_ctl  = '{}/postvar{}_interp2fnl.ctl'.format(exdata_dir,ddate)
    interp2fnl_data = '{}/postvar{}_interp2fnl.dat'.format(exdata_dir,ddate)
    interp2fnl_nc_temp = '{}/postvar{}_interp2fnl_temp.nc'.format(exdata_dir,ddate)
    interp2fnl_nc   = '{}/postvar{}_interp2fnl.nc'.format(exdata_dir,ddate)

    nointerp_ctl  = '{}/postvar{}_nointerp.ctl'.format(exdata_dir,ddate)
    nointerp_data = '{}/postvar{}_nointerp.dat'.format(exdata_dir,ddate)
    nointerp_nc   = '{}/postvar{}_nointerp.nc'.format(exdata_dir,ddate) 

    ex_nc   = '{}/postvar{}.nc'.format(exdata_dir,ddate)
    
    interp2fnl_vars = [ivar for ivar in ex_vars if ivar in def_interp2fnl_vars]
    nointerp_vars   = [ivar for ivar in ex_vars if ivar not in def_interp2fnl_vars]
    
    # 1.0 Extract need variables 
    print('--- 1.0 begin extract data ---')
    # extract interp vars 
    CTLExtract(ctlfilename,interp2fnl_vars,ex_levels,interp2fnl_ctl,interp2fnl_data,ddate,itype='interp')
    os.system('rm extract_interp_{}.gs'.format(ddate))
    # extract nointerp vars
    CTLExtract(ctlfilename,nointerp_vars,ex_levels,nointerp_ctl,nointerp_data,ddate,itype='nointerp')
    os.system('rm extract_nointerp_{}.gs'.format(ddate))
    print('finish extract data!')

    # 2.0 interpolation, grapes2fnl resolution
    print('--- 2.0 begin to interp and transfer postvar data ---')
    os.system('cdo -b F64 -f nc import_binary {} {}'.format(interp2fnl_ctl,interp2fnl_nc_temp))
    os.system('rm {} {}'.format(interp2fnl_ctl,interp2fnl_data))
    def_interp_grid('fnl')
    if os.path.exists(interp2fnl_nc):
        os.system('rm {}'.format(interp2fnl_nc))
    os.system('cdo remapbil,fnl_grid {} {}'.format(interp2fnl_nc_temp,interp2fnl_nc)) 
    os.system('rm {} {}'.format(interp2fnl_nc_temp, 'fnl_grid'))

    os.system('cdo -b F64 -f nc import_binary {} {}'.format(nointerp_ctl,nointerp_nc))
    os.system('rm {} {}'.format(nointerp_ctl,nointerp_data))
    
    os.system('cdo merge {} {} {}'.format(nointerp_nc,interp2fnl_nc,ex_nc))
    os.system('rm {} {}'.format(nointerp_nc,interp2fnl_nc))
    print('finish interp and transfer data.')

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
        #创建工作线程
        for x in range(nthreads):
            worker = ETWorker(queue)
            #将daemon设置为True将会使主线程退出，即使所有worker都阻塞了
            worker.daemon = True
            worker.start()
    
        #将任务以tuple的形式放入队列中
        for link in timelines:
            queue.put((link))
    
        #让主线程等待队列完成所有的任务
        queue.join()
        print('Took {}'.format(time.time() - ts))
