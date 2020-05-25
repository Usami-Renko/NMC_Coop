# -*- coding: utf-8 -*- 
'''
@Description: Extract data from Grads data
@Author: wanghao
@Date: 2020-04-20 09:59:11
@LastEditors: wanghao
@LastEditTime: 2020-05-25 10:56:52
'''

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

from utils import config_list
from asciiio import generate_generalctl

# Main Program
if __name__ == '__main__':
    # read the config file
    CONFIGPATH = './config/' # default config path
    cong = config_list(CONFIGPATH, ['config.yml', 'devconfig.yml'])
    for key, value in cong.items():
        locals()[key] = value
    
    # 参数设置
    timelines   = gen_timelines(start_ddate, end_ddate, fcst_step)

    for iexpr in exprs:
        # 制作ctl描述文件
        ctlfile_dir = list(iexpr.values())[0]
        generate_generalctl(timelines, ctlfile_dir)

        # 创建数据提取路径
        exdata_dir = exdata_dir + list(iexpr.keys())[0]
        if not os.path.exists(exdata_dir):
            os.makedirs(exdata_dir)
        
        for inn2,ddate in enumerate(timelines,1):
            print('{}. Work time :: {}'.format(inn2, ddate))
            
            ctlfilename = 	'{}/post.ctl_{}'.format(ctlfile_dir,ddate)
        
            ex_ctl  = '{}/postvar{}.ctl'.format(exdata_dir,ddate)
            ex_data = '{}/postvar{}.dat'.format(exdata_dir,ddate)

            ex_nc   = '{}/postvar{}.nc'.format(exdata_dir,ddate)
            
            t0_time = time.time()
            # 1.0 Extract need variables 
            print(u'--- 1.0 开始数据提取 ---')
            CTLExtract(ctlfilename,ex_vars,ex_levels,ex_ctl,ex_data,ddate)

            os.system('rm extract_{}.gs'.format(ddate))
            print(u'数据提取结束!')

            # 2.0 Transfer to NetCDF Format 
            print(u'--- 2.0 开始数据转换 ---')
            transf2nc(ex_ctl,ex_nc,ex_vars)
            os.system('rm {} {}'.format(ex_ctl, ex_data))
            print(u'数据转换结束!')
            t1_time = time.time()
            print(u'数据处理完成, 用时{} seconds.\n'.format(str(t1_time-t0_time)[:7]))
