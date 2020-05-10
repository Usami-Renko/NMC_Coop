#!/usr/bin/env python
# coding=UTF-8

'''
@Description: handle ASCII io file I/O operation
@Author: Hejun Xie
@Date: 2020-04-27 11:07:21
@LastEditors: Hejun Xie
@LastEditTime: 2020-05-10 19:48:17
'''

import os
import sys
import numpy as np
import pandas as pd
import datetime as dt
import re

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

def _write_file(filename, lines):
    with open(filename, 'w') as fw:
        print(filename)
        fw.writelines(lines)

def _probe_header(filename):
    lines = _read_file(filename)
    for iline, line in enumerate(lines):
        # header always finish with 2 elements 
        if len(line.split()) == 2 and len(lines[iline+1].split()) == 5:
            return iline + 1

def read_obs(filename):
    if not os.path.exists(filename):
        raise IOError('{} OBS file not found'.format(filename))

    header = _probe_header(filename)

    dataframe = pd.read_table(filename, delim_whitespace=True, skiprows=header, skipfooter=0, 
    names=['stationid', 'longitude', 'latitude', 'altitude', 'precipitation'])
    
    return dataframe

def _transfer_generalctl(lines, initdatetime):
    lines[0] = 'dset ^postvar' + initdatetime.strftime("%Y%m%d%H") + '_%f3\n'
    for iline, line in enumerate(lines):
        if line.split()[0] == 'tdef':
            ctltimestring = initdatetime.strftime('%Hz') + \
                initdatetime.strftime('%d%b%Y').upper()
            lines[iline] = re.sub("\d{2}z\d{2}\w{3}\d{4}", ctltimestring, lines[iline])
    return lines

def generate_generalctl(timelines, datadir):

    initdatetimes = [dt.datetime.strptime(timeline, "%Y%m%d%H") for timeline in timelines]

    template_ctl_filename = 'post.ctl_' + initdatetimes[0].strftime("%Y%m%d%H")
    template_ctl_path = os.path.join(datadir, template_ctl_filename)

    if not os.path.exists(template_ctl_path):
        raise IOError('tempelate CTL file {} not found under dir {}'.format(template_ctl_filename, datadir))

    template_ctl_lines = _read_file(template_ctl_path)

    for initdatetime in initdatetimes[1:]:
        ctl_lines = _transfer_generalctl(template_ctl_lines, initdatetime)
        ctl_filename = 'post.ctl_' + initdatetime.strftime("%Y%m%d%H")
        ctl_path = os.path.join(datadir, ctl_filename)
        _write_file(ctl_path, ctl_lines)

if __name__ == "__main__":
    datadir = '../87_fcst_ctl/'
    timelines = ['2016010112', '2016010212', '2016010312']
    generate_generalctl(timelines, datadir)
