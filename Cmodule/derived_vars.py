#!/usr/bin/env python
# coding=UTF-8

'''
@Description: handle the derived variables
@Author: Hejun Xie
@Date: 2020-04-26 18:57:38
@LastEditors: Hejun Xie
@LastEditTime: 2020-06-22 15:56:02
'''

import numpy as np
from copy import deepcopy
from scipy.interpolate import griddata

from utils import hashlist, config_list
from data import GRAPESSlicedData, FNLSlicedData

class _VarWorkStation(object):
    def __init__(self, filehandle, dic_varname):
        '''
        A parent class to handle Vars
        '''
        self.filehandle = filehandle
        self.dic_varname = dic_varname
        self.known_vars = dict()
        self.indices = None
    
    def get_var(self, varname, indices=None):
        '''
        indices is none for call from self._get_derived_vars
        otherwise we update the self.indices by input indices from API
        '''
        if indices is None:
            indices = self.indices
        else:
            self.indices = indices

        var_hash = self._get_var_hash(varname, indices)
        
        var_table = self._check_register(var_hash)

        if var_table is not None:
            return var_table
        
        if varname in self.dic_varname:
            var_table = self._get_raw_var(varname)
        else:
            var_table = self._get_derived_var(varname)
        
        self._register_var(var_hash, var_table)

        return var_table

    def close(self):
        for var in self.known_vars.values():
            var.close()
        del self.known_vars

    def _register_var(self, var_hash, data):
        if var_hash not in self.known_vars.keys():
            self.known_vars[var_hash] = data
    
    def _check_register(self, var_hash):
        if var_hash in self.known_vars.keys():
            return self.known_vars[var_hash]
    
    def _no_derived_var(self, varname):
        raise ValueError('Could not compute derived variable {}, please specify a valid variable name'.format(varname))
    
    def _get_var_hash(self, varname, indices):
        hashmaterial = list(deepcopy(indices))
        hashmaterial.append(varname)
        return hashlist(hashmaterial)

    def _get_raw_var(self, varname):
        pass

    def _get_derived_var(self, varname):
        pass


class FNLWorkStation(_VarWorkStation):
    '''
    A workstation class to handle FNL data.

    We perform FNL to GRAPES interpolation in this class.
    All the grapes levels can be found in FNL dataset levels.
    No vertical interpolation needed.

    FNL levels: 
    [  10.   20.   30.   50.   70.  100.  150.  200.  250.  300.  350.  400.
      450.  500.  550.  600.  650.  700.  750.  800.  850.  900.  925.  950.
      975. 1000.]
    
    GRAPES levels:
    [1000.0, 925.0, 850.0, 700.0, 600.0, 500.0, 400.0, 300.0, 200.0, 100.0, 50.0, 10.0]
    '''

    def __init__(self, filehandle, dic_varname, interp_LAT, interp_LON, sample_field):
        '''
        Additional inputs:
            interp_LAT, interp_LON:
            A numpy meshgrid for which the data read from FNL files
            to be interpolated.
        '''
        super(FNLWorkStation, self).__init__(filehandle, dic_varname)

        # interpolation points
        self.points = None

        self.interp_LAT, self.interp_LON = interp_LAT, interp_LON

        self.sample_field = sample_field
        
        self._prepare_points()

    def _prepare_points(self):
        # pad the data to make it cyclic

        lat, lon = self.sample_field.coords['latitude'].values, self.sample_field.coords['longitude'].values
        TLAT, TLON = np.meshgrid(lat, lon)

        # pad the meshgrid to make it cyclic
        TLON = np.pad(TLON, ((0, 1), (0, 0)), 'constant', constant_values=360.0)
        TLAT = np.pad(TLAT, ((0, 1), (0, 0)), 'constant')
        TLAT[-1, :] = TLAT[0, :] 

        # flatten it
        LAT, LON = TLAT.T.flatten(), TLON.T.flatten()
        self.points = np.zeros((len(LAT), 2))
        self.points[:, 0], self.points[:, 1] = LAT, LON

        # print(self.points[:, 0])
        # print(self.points[:, 1])
    
    def _prepare_values(self, data):
        # pad the data to make it cyclic
        data_table = data.data

        if data.ndim == 3:
            data_table = np.pad(data_table, ((0, 0), (0, 0), (0, 1)),'constant')
        elif data.ndim == 2:
            data_table = np.pad(data_table, ((0, 0), (0, 1)), 'constant')
        data_table[..., -1] = data_table[..., 0]

        if data.ndim == 3:
            nlevels = data_table.shape[0]
            values = np.reshape(data_table, (nlevels, -1))
        elif data.ndim == 2:
            values = data_table.flatten()
        
        # print(values[0])
        
        return values

    def _interp_data(self, values):
        nlevels = values.shape[0]
        
        interp_nlat, interp_nlon = self.interp_LAT.shape

        interp_data = np.zeros((nlevels, interp_nlat, interp_nlon), dtype='float32')

        for ilevel in range(nlevels):
            slice_values = values[ilevel, ...]
            interp_data[ilevel, ...] = griddata(self.points, slice_values, 
                (self.interp_LAT, self.interp_LON), method='linear')

        return interp_data
    
    def _strip_data(self, data_class):
        '''
        remove polar points of the FNL data and flip the latitude axis
        '''

        data_class.data = data_class.data[:, -2:0:-1, :]
        data_class.coordinates['latitude'] = data_class.coordinates['latitude'][-2:0:-1]

        return data_class
    
    def get_var(self, varname, indices=None, interp=False, strip=False):
        data_class = super(FNLWorkStation, self).get_var(varname, indices)

        if strip:
            return self._strip_data(data_class)

        if not interp:
            return data_class

        values = self._prepare_values(data_class)
        interp_data_class = data_class.copy()
        interp_data_class.data = self._interp_data(values)

        return interp_data_class

    def _get_raw_var(self, varname):
        level_indices = self.indices
        return FNLSlicedData(self.dic_varname[varname], self.filehandle, level_indices, self.sample_field)

    def _get_derived_var(self, varname):
        '''
        Get derived var
        '''
        # specific humidity [g/kg]
        if varname == 'q':
            E = self.get_var('E')
            p = self.get_var('p')
            nlevels = E.data.shape[0]
            q = E.copy()
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
        else:
            return self._no_derived_var(varname)


class GRAPESWorkStation(_VarWorkStation):
    '''
    A workstation class to handle GRAPES data
    
    e.g.
    ws = GRAPESWorkStation(filehandle, dic_varname)
    var_table = ws.get_data(varname, (time_indices, level_indices))
    ws.close()
    
    Input:
        filehandle: The netCDF4 file handler.
        dic_varname: A dict. mapping raw data name into netCDF4 variable names.
        varname: Name of the var.
        time_indices: Slicing indices in time diemnsion (must be a numpy array). 
        level_indices: Slicing indices in level dimension (must be a numpy array).
    Output:
        var_table: the sliced var table in the shape of 
        (len(time_indices), len(level_indices), nlat, nlon) for 3D vars,
        but (len(time_indices), nlat, nlon) for 2D vars
    '''

    def __init__(self, filehandle, dic_varname):
        super(GRAPESWorkStation, self).__init__(filehandle, dic_varname)
        self.time_incr = int(self.filehandle.variables['time'][1] - self.filehandle.variables['time'][0])        

    def _get_raw_var(self, varname):
        time_indices, level_indices = self.indices
        # the data class can only handle raw data names
        return GRAPESSlicedData(self.dic_varname[varname], self.filehandle, time_indices, level_indices)

    def _get_derived_var(self, varname):
        '''
        Get derived var
        '''
        if varname == "24hrain":
            accum_rain1 = self.get_var('accum_rain')
            ndiff = 24 // self.time_incr
            time_indices, level_indices = self.indices
            new_indices = (time_indices+ndiff, level_indices)
            accum_rain2 = self.get_var('accum_rain', new_indices)
            rain24h = accum_rain2 - accum_rain1
            return rain24h
        
        elif varname == 'accum_rain':
            accum_rain = self.get_var('rainc') + self.get_var('rainnc')
            return accum_rain
        
        elif varname == 'q':
            q = self.get_var('q_kg2kg') * 1000 # [kg/kg] --> [g/kg]
            return q

        elif varname == 'w':
            w = self.get_var('w_m2s') * 100 # [m/s] --> [cm/s]
            return w
        
        elif varname == 'shf':
            accum_hf1 = self.get_var('hf')
            ndiff = 24 // self.time_incr
            time_indices, level_indices = self.indices
            new_indices = (time_indices-ndiff, level_indices)
            accum_hf2 = self.get_var('hf', new_indices)
            shf = accum_hf1 - accum_hf2
            return shf / (3600 * 24) 
        
        elif varname == 'phf':
            accum_qf1 = self.get_var('qf')
            ndiff = 24 // self.time_incr
            time_indices, level_indices = self.indices
            new_indices = (time_indices-ndiff, level_indices)
            accum_qf2 = self.get_var('qf', new_indices)
            phf = (accum_qf1 - accum_qf2) * 2.5e6
            return phf / (3600 * 24)

        else:
            return self._no_derived_var(varname)
