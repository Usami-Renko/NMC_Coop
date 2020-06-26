#!/usr/bin/env python
# coding=UTF-8

'''
@Description: some utilities for that package
@Author: Hejun Xie
@Date: 2020-04-22 18:55:54
@LastEditors: Hejun Xie
@LastEditTime: 2020-06-25 07:54:03
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


class DATADumpManager(object):
    def __init__(self, workdir, pickle_speedup, pickle_filename, worker):
        self.workdir = workdir
        self.pickle_speedup = pickle_speedup
        self.pickle_filename = pickle_filename
        self.worker = worker
    
    def get_data(self, *args, **kwargs):        
        if not self.pickle_speedup \
            or not os.path.exists(self.pickle_filename):
            cdir = os.getcwd()
            os.chdir(self.workdir)
            DATA = self.worker(*args, **kwargs)
            os.chdir(cdir)
            if DATA is not None:
                self.pickle_dump(DATA)
        else:
            DATA = self.pickle_load()           
        return DATA

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
        pkls = glob.glob('{}/*/*/*.pkl'.format(self.dump_dir))
        for pkl in pkls:
            self.register.append(pkl.split('/')[-1].split('.')[0])
    
    def get_label(self, *args):
        label = args[0] + '_' + args[1]
        datadir = "/{}/{}/".format(args[1][0:4], args[1][0:8])
        makenewdir("{}/{}".format(self.dump_dir, args[1][0:4]))
        makenewdir("{}/{}".format(self.dump_dir, datadir))
        return label, datadir

    def get_data(self, *args, **kwargs):
        '''
        args is the datalabel
        '''
        datalabel, datadir = self.get_label(*args)
        if datalabel in self.register:
            return self.pickle_load(datalabel, datadir)
        else:
            DATA = self.worker(*args, **kwargs)
            self.pickle_dump(DATA, datalabel, datadir)
            return DATA
        
    def close(self):
        os.system("rm {}/*/*/*.pkl".format(self.dump_dir))
        del self.register

    def pickle_dump(self, DATA, datalabel, datadir):
        self.register.append(datalabel)
        datafile = "{}/{}/{}.pkl".format(self.dump_dir, datadir, datalabel)
        with open(datafile, "wb") as f:
            pickle.dump(DATA, f)
        
    def pickle_load(self, datalabel, datadir):
        datafile = "{}/{}/{}.pkl".format(self.dump_dir, datadir, datalabel)
        with open(datafile, "rb") as f:
            DATA = pickle.load(f)
        return DATA

def makenewdir(mydir):
    if not os.path.exists(mydir):
        os.system("mkdir -p {}".format(mydir))
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

def def_interp_grid(itype):
    with open('{}_grid'.format(itype),'w') as f:
        f.write('gridtype = lonlat\n')
        f.write('xsize = 360\n')
        f.write('ysize = 179\n')
        f.write('xfirst = 0\n') 
        f.write('xinc   = 1.0\n')
        f.write('yfirst = -89.0\n')
        f.write('yinc   = 1.0\n')
    f.close()

def gen_cmp_pre_ctl(ctlfile,ddate,gridrain_dir):
    (filepath, tempfilename) = os.path.split(ctlfile)
    makenewdir(filepath)
    with open(ctlfile,'w') as f:
        f.write('dset {}/SURF_CLI_CHN_MERGE_CMP_PRE_HOUR_GRID_0.10-{}.grd\n'.format(gridrain_dir,ddate))
        f.write('undef -999.0\n')
        f.write('options   little_endian\n')
        f.write('title  China Hourly Merged Precipitation Analysis\n')
        f.write('xdef  700 linear  70.05  0.10\n')
        f.write('ydef  440 linear  15.05  0.10\n')
        f.write('zdef     1 levels 1\n')
        f.write('tdef 1 linear 00Z01jun2015 1hr\n')
        f.write('vars 2\n')
        f.write('crain      1 00  CH01   combined analysis (mm/Hour)\n')
        f.write('gsamp      1 00  CH02   gauge numbers\n')
        f.write('endvars')
    f.close()

 # unit test
if __name__ == "__main__":
    gen_cmp_pre_ctl('2019081819') 
