'''
@Description: a small class to handle a variable and its attributes
@Author: Hejun Xie
@Date: 2020-04-30 17:18:42
@LastEditors: Hejun Xie
@LastEditTime: 2020-05-19 17:42:10
'''

import numpy as np
from collections import OrderedDict
import copy
import os
import warnings
from nwpc_data.grib.eccodes import load_field_from_file


class _DataClass(object):
    '''
    A parent class to handle any NWP data with coordinates and attributes
    '''
    def __init__(self, varname):
        self.varname = varname
        self.data = None
        self.ndim = None
        self.coordinates = OrderedDict()
        self.attributes = dict()

    def close(self):
        del self.data
        del self.coordinates
        del self.attributes

    # Redefine operators

    # enable slice like an array
    def __getitem__(self,key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def log(self):
        cp=self.copy()
        cp.data=np.log(cp.data)
        return cp

    def __add__(self, x):
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We sum by a scalar
            cp=self.copy()
            cp.data+=x
        elif isinstance(x, _DataClass): # Sum by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data+=x.data

                # copy the attributes from x
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp

    def __radd__(self, x): # Reverse addition
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We sum by a scalar
            cp=self.copy()
            cp.data+=x
        elif isinstance(x, _DataClass): # Sum by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data+=x.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp
    
    
    def __sub__(self, x):
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We subtract by a scalar
            cp=self.copy()
            cp.data-=x
        elif isinstance(x, _DataClass): # Substract by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data-=x.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp

    def __rsub__(self, x): # Reverse subtraction (non-commutative)
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We subtract by a scalar
            cp=self.copy()
            cp.data=x-cp.data
        elif isinstance(x, _DataClass): # Substract by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data=x.data-cp.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp


    def __mul__(self, x):
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We muliply by a scalar
            cp=self.copy()
            cp.data*=x
        elif isinstance(x, _DataClass): # Multiply by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data*=x.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp
        

    def __rmul__(self, x):
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We muliply by a scalar
            cp=self.copy()
            cp.data*=x
        elif isinstance(x, _DataClass): # Multiply by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data*=x.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp
    
    # for python 2.x
    def __div__(self, x):
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We divide by a scalar
            cp=self.copy()
            cp.data/=x
        elif isinstance(x, _DataClass): # divide by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data/=x.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp

    def __rdiv__(self, x): # Reverse divsion (non-commutative)
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We divide by a scalar
            cp=self.copy()
            cp.data=x/cp.data
        elif isinstance(x, _DataClass): # divide by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data=x.data/cp.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp
    
    # for python 3.x
    def __truediv__(self, x):
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We divide by a scalar
            cp=self.copy()
            cp.data/=x
        elif isinstance(x, _DataClass): # divide by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data/=x.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp
    
    def __rtruediv__(self, x): # Reverse divsion (non-commutative)
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We divide by a scalar
            cp=self.copy()
            cp.data=x/cp.data
        elif isinstance(x, _DataClass): # divide by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data=x.data/cp.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp
    
    # for both python 2.x and 3.x
    def __floordiv__(self, x):
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We divide by a scalar
            cp=self.copy()
            cp.data//=x
        elif isinstance(x, _DataClass): # divide by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data/=x.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp

    def __rfloordiv__(self, x): # Reverse divsion (non-commutative)
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We divide by a scalar
            cp=self.copy()
            cp.data=x//cp.data
        elif isinstance(x, _DataClass): # divide by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data=x.data/cp.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp

    def __pow__(self, x):
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We divide by a scalar
            cp=self.copy()
            cp.data = cp.data**x
        elif isinstance(x, _DataClass): # divide by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data = cp.data**x.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp
    
    def __rpow__(self, x): # Reverse divsion (non-commutative)
        cp=None
        if isinstance(x,(int,float,bool,np.ndarray )): # We divide by a scalar
            cp=self.copy()
            cp.data=x**cp.data
        elif isinstance(x, _DataClass): # divide by another variable
            if self.data.shape == x.data.shape:
                cp=self.copy()
                cp.data=x.data**cp.data
                keys=self.attributes.keys()
                for att in x.attributes.keys():
                    if att not in keys:
                        cp.attributes[att]=x.attributes[att]
            else:
                raise TypeError('var:{} and var:{} do not have identical shape'.format(self.name, x.name))
        return cp


class GRAPESSlicedData(_DataClass):
    '''
    A class to handle sliced GRAPES data with coordinates and attributes
    '''
    def __init__(self, varname='', filehandle='', time_indices='', level_indices=''):
        '''
        If this __init__() is called by self.copy(),
        just do no initialization  
        '''
        if filehandle != '' and varname != '':
            self.create(varname, filehandle, time_indices, level_indices)
    
    def create(self, varname, filehandle, time_indices, level_indices):
        super(GRAPESSlicedData, self).__init__(varname)
        self.filehandle = filehandle
        self.time_indices = time_indices
        self.level_indices = level_indices
        self.surface = False

        self.raw_dims = None
        self.raw_dims_map = None
        self.raw_coordinates = None
        self.raw_indices = None

        self.dimensions = None

        self._assign_raw_coordinates()
        if self.varname in self.raw_dims:
            self.data = self.raw_coordinates[varname]
            self.ndim = 1
        else: 
            self._assign_raw_indices()
            self._slice_coordinates()
            self._slice_data()
    
    def copy(self):
        cp=GRAPESSlicedData()
        for attr in self.__dict__.keys():
            if attr != 'filehandle':
                setattr(cp,attr,copy.deepcopy(getattr(self,attr)))
            else: 
                setattr(cp,attr,getattr(self,attr))                
        return cp
    
    def _assign_raw_coordinates(self):
        self.raw_dims = ['times', 'levels', 'latitude', 'longitude']
        self.raw_dims_map = {'nlevel':'levels', 'ntime':'times',
                            'nlat':'latitude', 'nlon':'longitude'}
        self.raw_coordinates = OrderedDict()
        for raw_dim in self.raw_dims:
            self.raw_coordinates[raw_dim] = self.filehandle.variables[raw_dim][:]

        # print(self.raw_coordinates)    
    
    def _assign_raw_indices(self):
        
        self.dimensions = self.filehandle.variables[self.varname].dimensions
        self.ndim = len(self.dimensions)

        if 'nlevel' not in self.dimensions:
            self.surface = True
        
        self.raw_indices = OrderedDict()
        
        for dimension in self.dimensions:
            dim_name = self.raw_dims_map[dimension]
            if dim_name == 'levels':
                self.raw_indices[dim_name] = self.level_indices
            elif dim_name == 'times':
                self.raw_indices[dim_name] = self.time_indices
            else:
                self.raw_indices[dim_name] = range(len(self.raw_coordinates[dim_name]))    

        # print(self.dimensions)
        # print(self.raw_indices)

    def _slice_coordinates(self):
        for dimension in self.dimensions:
            dim_name = self.raw_dims_map[dimension]
            coordinates = list()
            for index in self.raw_indices[dim_name]:
                coordinates.append(self.raw_coordinates[dim_name][index])
            
            self.coordinates[dim_name] = coordinates

        # print(self.coordinates)

    def _slice_data(self):
        shape = list()
        for dimension in self.dimensions:
            dim_name = self.raw_dims_map[dimension]
            shape.append(len(self.raw_indices[dim_name]))

        # print(shape)
        
        self.data = np.zeros(tuple(shape), dtype='float32')
        
        # Currently it is not written generally enough
        if not self.surface:
            for itime, time_index in enumerate(self.time_indices):
                for ilevel, level_index in enumerate(self.level_indices):
                    self.data[itime, ilevel, ...] = \
                        self.filehandle.variables[self.varname][time_index, level_index, ...]
        else:
            for itime, time_index in enumerate(self.time_indices):
                self.data[itime, ...] = \
                    self.filehandle.variables[self.varname][time_index, ...]


class FNLSlicedData(_DataClass):
    '''
    A class to handle sliced FNL data with coordinates and attributes
    '''
    def __init__(self, varname='', filehandle='', level_indices='', sample_field=''):
        '''
        If this __init__() is called by self.copy(),
        just do no initialization  
        '''
        if filehandle != '' and varname != '':
            self.create(varname, filehandle, level_indices, sample_field)
    
    def create(self, varname, filehandle, level_indices, sample_field):
        super(FNLSlicedData, self).__init__(varname)

        self.filehandle = filehandle
        self.sample_field = sample_field
        self.level_indices = level_indices
        self.surface = False

        self.raw_dims = None
        self.raw_coordinates = None
        self.raw_indices = None

        self.dimensions = None
        self.xarray = None

        # print(self.varname)

        self._assign_raw_coordinates()
        if self.varname in self.raw_dims and self.varname != 'isobaricInhPa':
            self.data = self.raw_coordinates[varname]
            self.ndim = 1
        else:
            if self.varname != 'isobaricInhPa':
                self._get_xarray()
            self._assign_raw_indices()
            self._slice_coordinates()
            self._slice_data()

    def copy(self):
        cp=FNLSlicedData()
        for attr in self.__dict__.keys():
            if attr != 'filehandle':
                setattr(cp,attr,copy.deepcopy(getattr(self,attr)))
            else: 
                setattr(cp,attr,getattr(self,attr))                
        return cp
    
    def close(self):
        super(FNLSlicedData, self).close()
        del self.xarray
    
    def _assign_raw_coordinates(self):
        self.raw_dims = ['isobaricInhPa', 'latitude', 'longitude']
        self.raw_coordinates = OrderedDict()
        for raw_dim in self.raw_dims:
            self.raw_coordinates[raw_dim] = self.sample_field.coords[raw_dim].values

        # print(self.raw_coordinates)

    def _get_xarray(self):
        self.xarray = load_field_from_file(
            file_path = self.filehandle,
            parameter = self.varname,
            level_type = "isobaricInhPa",
            level = None,
        )
    
    def _assign_raw_indices(self):

        if self.varname == 'isobaricInhPa':
            self.dimensions = ['isobaricInhPa']
        else:
            self.dimensions = self.xarray.dims
        
        self.ndim = len(self.dimensions)

        if 'isobaricInhPa' not in self.dimensions:
            self.surface = True
        
        self.raw_indices = OrderedDict()
        
        for dimension in self.dimensions:
            if dimension == 'isobaricInhPa':
                self.raw_indices[dimension] = self.level_indices
            else:
                self.raw_indices[dimension] = range(len(self.raw_coordinates[dimension]))    

        # print(self.dimensions)
        # print(self.raw_indices)

    def _slice_coordinates(self):
        for dimension in self.dimensions:
            coordinates = list()
            for index in self.raw_indices[dimension]:
                coordinates.append(self.raw_coordinates[dimension][index])
            
            self.coordinates[dimension] = coordinates

        # print(self.coordinates)

    def _slice_data(self):
        shape = list()
        for dimension in self.dimensions:
            shape.append(len(self.raw_indices[dimension]))

        # print(shape)
        
        self.data = np.zeros(tuple(shape), dtype='float32')
        
        # Currently it is not written generally enough
        if not self.surface:
            if self.varname == 'isobaricInhPa':
                self.data = self.coordinates['isobaricInhPa']
            else:
                for ilevel, level_index in enumerate(self.level_indices):
                    self.data[ilevel, ...] = self.xarray[level_index, ...]
        else:
            self.data[...] = self.xarray[...]
