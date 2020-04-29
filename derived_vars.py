#!/usr/bin/env python
# coding=UTF-8

'''
@Description: handle the derived variables
@Author: Hejun Xie
@Date: 2020-04-26 18:57:38
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-29 16:05:03
'''

import numpy as np

derived_vars = ['24hrain', 'w_cm2s']

def _get_derived_var_grapes(filehandle, varname, ex_vars):
    derived_var = None

    # compute the total precipitation in the upcoming 24 hours of a given time
    if varname == "24hrain":
        time_incr = int(float(filehandle.variables['times'].incr))
        ntimes = len(filehandle.variables['times'][:])
        nlat, nlon = len(filehandle.variables['latitude'][:]), len(filehandle.variables['longitude'][:])
        ndiff = 24 // time_incr

        total_rain = filehandle.variables['rainc'][:] + filehandle.variables['rainnc'][:]
        derived_var = np.zeros((ntimes - ndiff, nlat, nlon))

        for itime in range(ntimes - ndiff):
            derived_var[itime, ...] = total_rain[itime + ndiff, ...] - total_rain[itime, ...]
    elif varname == 'w_cm2s':
        derived_var = filehandle.variables['w'][:] * 100 # [m/s] --> [cm/s]
    else:
        raise ValueError('Could not compute derived variable, please specify a valid variable name')
        
    return derived_var

def get_var_grapes(filehandle, varname, ex_vars):
    
    if varname in ex_vars:
        var_table = filehandle.variables[varname]
    else:
        var_table = _get_derived_var_grapes(filehandle, varname, ex_vars)

    return var_table
