# -*- coding: utf-8 -*- 
"""
Extract data from Grads data
2018.03.23
@author:wanghao
"""
import sys
#sys.path.append('/g3/wanghao/Python/Cmodule/CTLReader/CTLReader_Py')
#sys.path.append('/g3/wanghao/Python/Cmodule/CTLExtract')
#sys.path.append('/g3/wanghao/Python/Cmodule/Transf2nc')
#sys.path.append('/g3/wanghao/Python/Cmodule/gen_info')
sys.path.append('./Cmodule')
from CTLExtract import CTLExtract
from CTLReader import CTLReader
from transf2nc import transf2nc
from gen_timelines import gen_timelines
import os
import datetime
import time
from utils import config

# Main Program
if __name__ == '__main__':
    # read the config file
    
    cong = config_list(['config.yml', 'devconfig.yml'])
    for key, value in cong.items():
        locals()[key] = value
    
    # 参数设置
    timelines   = gen_timelines(start_ddate, end_ddate, fcst_step)
    
    if not os.path.exists(exdata_dir):
        os.makedirs(exdata_dir)

    for inn,ddate in enumerate(timelines,1):
        print('{}. Work time :: {}'.format(inn, ddate))
        
        ctlfilename = 	'{}/post.ctl_{}'.format(ctlfile_dir,ddate)
    
        ex_ctl  = '{}/postvar{}.ctl'.format(exdata_dir,ddate)
        ex_data = '{}/postavr{}.dat'.format(exdata_dir,ddate)

        ex_nc   = '{}/postvar{}.nc'.format(exdata_dir,ddate)
        
        t0_time = time.time()
        # 1.0 Extract need variables 
        print(u'--- 1.0 开始数据提取 ---')
        CTLExtract(ctlfilename,ex_vars,ex_levels,ex_ctl,ex_data)

        os.system('rm extract.gs')
        print(u'数据提取结束!')

        # 2.0 Transfer to NetCDF Format 
        print(u'--- 2.0 开始数据转换 ---')
        transf2nc(ex_ctl,ex_nc,ex_vars)
        os.system('rm {} {}'.format(ex_ctl, ex_data))
        print(u'数据转换结束!')
        t1_time = time.time()
        print(u'数据处理完成, 用时{} seconds.\n'.format(str(t1_time-t0_time)[:7]))
