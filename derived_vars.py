#!/usr/bin/env python
# coding=UTF-8

'''
@Description: handle the derived variables
@Author: Hejun Xie
@Date: 2020-04-26 18:57:38
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-29 22:05:39
'''

import numpy as np

class _VarWorkstation(object):
    def __init__(self, filehandle, dic_varname):
        '''
        A parent class to handle Vars
        '''
        self.filehandle = filehandle
        self.dic_varname = dic_varname
        self.known_vars = dict()
    
    def get_var(self, varname):
        
        var_table = self._check_register(varname)

        if var_table is not None:
            return var_table
        
        if varname in self.dic_varname:
            var_table = self._get_raw_var(varname)
        else:
            var_table = self._get_derived_var(varname)
        
        self._register_var(varname, var_table)

        return var_table

    def close(self):
        self.filehandle.close()
        del self.known_vars

    def _register_var(self, varname, data):
        if varname not in self.known_vars.keys():
            self.known_vars[varname] = data
    
    def _check_register(self, varname):
        if varname in self.known_vars.keys():
            return self.known_vars[varname]
    
    def _no_derived_var(self, varname):
        raise ValueError('Could not compute derived variable {}, please specify a valid variable name'.format(varname))

    def _get_raw_var(self, varname):
        pass

    def _get_derived_var(self, varname):
        pass


class FNLWorkStation(_VarWorkstation):
    '''
    A workstation class to handle FNL data
    '''
    def _get_raw_var(self, varname):
        return self.filehandle.variables[self.dic_varname[varname]][:]

    def _get_derived_var(self, varname):
        '''
        Get derived var
        '''
        # specific humidity [g/kg]
        if varname == 'q':
            E = self.get_var('E')
            p = self.get_var('p') 
            nlevels = len(p)
            q = np.zeros(E.shape, dtype='float32')
            for ilevel in range(nlevels):
                ip = p[ilevel]
                iE = E[ilevel, ...]
                q[ilevel, ...] =  0.6357 * iE / (ip - 0.3643 * iE)
            return q * 1000  # [kg/kg] --> [g/kg]
        # Saturation water vapor pressure [hPa]
        elif varname == 'Es':
            t = self.get_var('t') - 273.15
            Es = 6.11 * 10 ** (7.5 * t / (273.3 + t))
            return Es
        # Water vapor pressure [hPa]
        elif varname == 'E':
            Es = self.get_var('Es')
            rh = self.get_var('rh')
            E = Es * rh / 100.
            return E  
        elif varname == 'p':
            return self.get_var('p_pa') / 100 # [Pa] --> [hPa]
        else:
            return self._no_derived_var(varname)

class GRAPESWorkStation(_VarWorkstation):
    '''
    A workstation class to handle GRAPES data
    '''
    def __init__(self, filehandle, dic_varname):
        super(GRAPESWorkStation, self).__init__(filehandle, dic_varname)
        self.time_incr = int(float(self.filehandle.variables['times'].incr))

    def _get_raw_var(self, varname):
        return self.filehandle.variables[self.dic_varname[varname]][:]

    def _get_derived_var(self, varname):
        '''
        Get derived var
        '''
        if varname == "24hrain":
            ntimes = len(self.get_var('time'))
            nlat, nlon = len(self.get_var('lat')), len(self.get_var('lon'))
            ndiff = 24 // self.time_incr

            total_rain = self.get_var('rainc') + self.get_var('rainnc')

            rain24h = np.zeros((ntimes - ndiff, nlat, nlon), dtype='float32')

            for itime in range(ntimes - ndiff):
                rain24h[itime, ...] = total_rain[itime + ndiff, ...] - total_rain[itime, ...]
            
            return rain24h
        
        elif varname == 'q':
            q = self.get_var('q_kg2kg') * 1000 # [kg/kg] --> [g/kg]
            return q

        elif varname == 'w':
            w = self.get_var('w_m2s') * 100 # [m/s] --> [cm/s]
            return w
        else:
            return self._no_derived_var(varname)
