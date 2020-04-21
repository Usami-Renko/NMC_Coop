# -*- coding: utf-8 -*- 
'''
@Author: wanghao
@Date: 2019-01-22 15:31:50
@LastEditors: wanghao
@LastEditTime: 2020-04-21 21:57:38
@Description: 转换数据在一个文件中的数据
'''
import sys
from CTLReader import CTLReader
from netCDF4 import Dataset
import numpy as np
import time
import datetime

class transf2nc(object):
    def __init__(self,ctlname,nc_filename,var=-1):
        
        data = CTLReader(ctlname)
        times_tmp = [itime.strftime("%Y%m%d%H%M") for itime in data.variables['time']]

        # 提取维度信息
        nt = data.dimensions['time']
        nz = data.dimensions['levels']
        ny = data.dimensions['latitude']
        nx = data.dimensions['longitude']

        ncfile = Dataset(nc_filename,'w')

        ncfile.createDimension('ntime',nt)
        ncfile.createDimension('nlevel',nz)
        ncfile.createDimension('nlat',ny)
        ncfile.createDimension('nlon',nx)

        times     = ncfile.createVariable('times',np.int,('ntime'))
        levels    = ncfile.createVariable('levels',np.float32,('nlevel'))
        latitude  = ncfile.createVariable('latitude',np.float32,('nlat'))
        longitude = ncfile.createVariable('longitude',np.float32,('nlon'))
        
        times[:]     = [int(itime) for itime in times_tmp] 
        latitude[:]  = data.variables['latitude'][:]
        longitude[:] = data.variables['longitude'][:]
        levels[:]    = data.variables['levels'][:]

        for ivar in var:
            if data.variables[ivar].dimensions['levels'] == 1:
                locals()[ivar] = ncfile.createVariable(ivar,np.float32,('ntime','nlat','nlon'))
                locals()[ivar][:] = data.variables[ivar][:]
                # add attributes
                # locals()[ivar].units = 'mm'
                locals()[ivar].long_name = data.variables[ivar].attributes['long_name']
            else:
                locals()[ivar] = ncfile.createVariable(ivar,np.float32,('ntime','nlevel','nlat','nlon'))
                locals()[ivar][:] = data.variables[ivar][:]
                # add attributes
                #locals()[ivar].units = 'mm'
                locals()[ivar].long_name = data.variables[ivar].attributes['long_name']

        # times     = ncfile.createVariable('times',,('tm'))
        # Variable Attributes
        latitude.units  = 'degree_north'
        longitude.units = 'degree_east'
        levels.units    = 'hPa'
        times.units     = 'days since 2000-01-01 00:00:00'
        times.calendar  = 'gregorian'
        times.incr      = '{}'.format(data.crement['time'].seconds/3600)

        # Global Attributes
        ncfile.description = 'Transf postvar data to NC'
        ncfile.history = 'Created ' + time.ctime(time.time())
        ncfile.source = 'netCDF4 python module tutorial'

        ncfile.close()
