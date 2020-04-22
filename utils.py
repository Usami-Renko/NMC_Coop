#!/usr/bin/env python
# coding=UTF-8

'''
@Description: some utilities for that package
@Author: Hejun Xie
@Date: 2020-04-22 18:55:54
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-22 19:48:55
'''
# -*- coding: utf-8 -*-

import numpy as np
import os
import pickle
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
        makenewdir(os.path.dirname(self.pickle_filename))
        with open(self.pickle_filename, "wb") as f:
            pickle.dump(DATA, f)

    def pickle_load(self):
        with open(self.pickle_filename, "rb") as f:
            DATA = pickle.load(f)
        return DATA

def makenewdir(mydir):
    if not os.path.exists(mydir):
        os.system("mkdir {}".format(mydir))
        os.system("chmod -R o-w {}".format(mydir))
