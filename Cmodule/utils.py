#!/usr/bin/env python
# coding=UTF-8

'''
@Description: some utilities for that package
@Author: Hejun Xie
@Date: 2020-04-22 18:55:54
@LastEditors: Hejun Xie
@LastEditTime: 2020-05-18 11:23:05
'''
# -*- coding: utf-8 -*-

import numpy as np
import os
import sys
import yaml
import pickle
import hashlib
import glob
from functools import wraps 


class DATAdecorator(object):
    def __init__(self, workdir, pickle_speedup, pickle_filename):
        self.workdir = workdir
        self.pickle_speedup = pickle_speedup
        self.pickle_filename = pickle_filename
    
    def __call__(self, worker):
        @wraps(worker)
        def wrapped_worker(*args, **kwargs):
            if not self.pickle_speedup \
                or not os.path.exists(self.pickle_filename):
                cdir = os.getcwd()
                os.chdir(self.workdir)
                DATA = worker(*args, **kwargs)
                os.chdir(cdir)
                self.pickle_dump(DATA)
            else:
                DATA = self.pickle_load()           
            return DATA
        return wrapped_worker
            
    def pickle_dump(self, DATA):
        print('Dump data at {}'.format(self.pickle_filename))
        makenewdir(os.path.dirname(self.pickle_filename))
        with open(self.pickle_filename, "wb") as f:
            pickle.dump(DATA, f)

    def pickle_load(self):
        print('Load data at {}'.format(self.pickle_filename))
        with open(self.pickle_filename, "rb") as f:
            DATA = pickle.load(f)
        return DATA

class DumpDataSet(object):
    def __init__(self, dump_dir, worker):
        self.dump_dir = dump_dir
        self.worker = worker
        
        self.register = list()
        makenewdir(dump_dir)
        self.get_register()
    
    def get_register(self):
        pkls = glob.glob('{}/*.pkl'.format(self.dump_dir))
        for pkl in pkls:
            self.register.append(pkl.split('/')[-1].split('.')[0])

    def get_data(self, *args, **kwargs):
        '''
        args is the datalabel
        '''

        datahash = hashlist(args)

        if datahash in self.register:
            return self.pickle_load(datahash)
        else:
            DATA = self.worker(*args, **kwargs)
            self.pickle_dump(DATA, datahash)
            return DATA
        
    def close(self):
        os.system("rm {}/*.pkl".format(self.dump_dir))
        del self.register

    def pickle_dump(self, DATA, datahash):
        self.register.append(datahash)
        datafile = "{}/{}.pkl".format(self.dump_dir, datahash)
        with open(datafile, "wb") as f:
            pickle.dump(DATA, f)
        
    def pickle_load(self, datahash):
        datafile = "{}/{}.pkl".format(self.dump_dir, datahash)
        with open(datafile, "rb") as f:
            DATA = pickle.load(f)
        return DATA

def makenewdir(mydir):
    if not os.path.exists(mydir):
        os.system("mkdir {}".format(mydir))
        os.system("chmod -R o-w {}".format(mydir))

def config(config_path, config_file):
    cong_yamlPath = os.path.join(config_path, config_file)
    if sys.version_info[0] < 3:
        cong = yaml.load(open(cong_yamlPath))
    elif sys.version_info[0] >= 3:
        try:
            cong = yaml.load(open(cong_yamlPath), Loader=yaml.FullLoader)
        except:
            cong = yaml.load(open(cong_yamlPath))
    return cong

def config_list(config_path, config_files):
    cong = dict()
    for config_file in config_files:
        new_cong = config(config_path, config_file)
        cong.update(new_cong)
    
    return cong

def hashlist(objectlist):
    obj_string = ''
    for object in objectlist:
        obj_string += str(object)
    
    return hashlib.md5(obj_string.encode()).hexdigest()
