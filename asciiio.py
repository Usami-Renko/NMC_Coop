#!/usr/bin/env python
# coding=UTF-8

'''
@Description: handle ASCII io file I/O operation
@Author: Hejun Xie
@Date: 2020-04-27 11:07:21
@LastEditors: Hejun Xie
@LastEditTime: 2020-05-02 10:05:55
'''

import os
import sys
import numpy as np
import pandas as pd

def _read_file(filename):
    if sys.version_info[0] < 3:
        with open(filename, 'r') as fr:
            lines = fr.readlines()
    elif sys.version_info[0] >= 3:
        try:
            with open(filename, 'r', encoding = 'utf-8') as fr:
                lines = fr.readlines()
        except Exception:
            with open(filename, 'r', encoding = 'gbk') as fr:
                lines = fr.readlines()
        
    return lines

def _probe_header(filename):
    lines = _read_file(filename)
    for iline, line in enumerate(lines):
        # header always finish with 2 elements 
        if len(line.split()) == 2 and len(lines[iline+1].split()) == 5:
            return iline + 1 

def read_obs(filename):
    header = _probe_header(filename)

    dataframe = pd.read_table(filename, delim_whitespace=True, skiprows=header, skipfooter=0, 
    names=['stationid', 'longitude', 'latitude', 'altitude', 'precipitation'])
    
    return dataframe

if __name__ == "__main__":
    
    FILENAME = './nmc_obs/rr2400/2016/16010108.000'
    a = read_obs(FILENAME)
    print(a)
    