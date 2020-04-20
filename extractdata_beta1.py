# -*- coding: utf-8 -*- 
"""
Extract data from Grads data
2018.03.23
@author:wanghao
"""
import sys
# sys.path.append('/g3/wanghao/Python/Cmodule/CTLReader/CTLReader_Py')
# sys.path.append('/g3/wanghao/Python/Cmodule/CTLExtract')
# sys.path.append('/g3/wanghao/Python/Cmodule/Transf2nc')
# sys.path.append('/g3/wanghao/Python/Cmodule/gen_info')

sys.path.append('/home/shiyu1997/NMC/Cmodule/')

from CTLExtract import CTLExtract
from CTLReader import CTLReader
from transf2nc import transf2nc
from gen_timelines import gen_timelines
import os
import datetime
import time
import yaml

# Main Program
if __name__ == '__main__':
    # read the config file
    curPath       = os.path.dirname(os.path.realpath(__file__))
    cong_yamlPath = os.path.join(curPath+"/config/", "config_xhj.yml")
    if sys.version_info[0] < 3:
        cong = yaml.load(open(cong_yamlPath))
    elif sys.version_info[0] >= 3:
        cong = yaml.load(open(cong_yamlPath), Loader=yaml.FullLoader)
    
    start_ddate    = cong['start_ddate'] #yyyymnddhh
    end_ddate      = cong['end_ddate']   #yyyymnddhh
    ctlfile_dir    = cong['ctlfile_dir']
    exdata_dir     = cong['exdata_dir']
    st_vars        = cong['st_vars']
    st_levels      = cong['st_levels']
    pic_prefix     = cong['pic_prefix'] 
    
    # 参数设置
    fcst_step   = 24  # hours
    timelines   = gen_timelines(start_ddate, end_ddate, fcst_step)
    
    if not os.path.exists(exdata_dir):
        os.makedirs(exdata_dir)

    for inn,ddate in enumerate(timelines,1):
        print('{}. Work time :: {}'.format(inn, ddate))
        
        ctlfilename = 	'{}/post.ctl_{}'.format(ctlfile_dir,ddate)
    
        ex_ctl  = '{}/postvar{}.ctl'.format(exdata_dir,ddate)
        ex_data = '{}/postvar{}.dat'.format(exdata_dir,ddate)

        ex_nc   = '{}/postvar{}.nc'.format(exdata_dir,ddate)
        
        t0_time = time.time()
        # 1.0 Extract need variables 
        print(u'--- 1.0 开始数据提取 ---')
        CTLExtract(ctlfilename,st_vars,st_levels,ex_ctl,ex_data)

        os.system('rm extract.gs')
        print(u'数据提取结束!')

        # 2.0 Transfer to NetCDF Format 
        print(u'--- 2.0 开始数据转换 ---')
        transf2nc(ex_ctl,ex_nc,st_vars)
        os.system('rm {} {}'.format(ex_ctl, ex_data))
        print(u'数据转换结束!')
        t1_time = time.time()
        print(u'数据处理完成, 用时{} seconds.\n'.format(str(t1_time-t0_time)[:7]))
