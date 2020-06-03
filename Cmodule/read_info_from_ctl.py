#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: wanghao
@LastEditTime: 2020-04-29 16:12:53
@Description  : read info from ctl file
'''
import re
import os
import numpy as np
import datetime

NUMBER = '[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'
class read_info_from_ctl(object):
    def __init__(self,ctlfilename,varname=''):
        self.variables = {}
        self.dimensions = {}
        self.crement = {}
        self.attributes = {}
        self.ctlfilename = ctlfilename
        self.varname = varname

        with open(self.ctlfilename,'r') as f:
            self.ctl = f.read()
        
        p = re.compile("%s\s+(.*)" % ('dset'))
        m = p.search(self.ctl)
        path = os.path.dirname(ctlfilename)
        self.filename = path + os.sep + m.group(1)[1:]
        print(self.filename)

        self._read_dimensions() #获取ctl中的维度信息

    def _read_dimensions(self):
        if 'xdef' in self.ctl:
            p = re.compile("%s\s+(\d+)\s+linear\s+(%s)\s+(%s)" % ('xdef',NUMBER,NUMBER))
            m = p.search(self.ctl)
            self.variables['longitude'] = np.linspace(float(m.group(2)),
                                                      float(m.group(2))+float(m.group(3))*(int(m.group(1))-1),
                                                      int(m.group(1)))
            self.dimensions['longitude'] = int(m.group(1))
            self.crement['longitude'] = float(m.group(3))

        if 'ydef' in self.ctl:
            p = re.compile("%s\s+(\d+)\s+linear\s+(%s)\s+(%s)" % ('ydef',NUMBER,NUMBER))
            m = p.search(self.ctl)
            self.variables['latitude'] = np.linspace(float(m.group(2)),
                                                     float(m.group(2))+float(m.group(3))*(int(m.group(1))-1),
                                                     int(m.group(1)))
            self.dimensions['latitude'] = int(m.group(1))
            self.crement['latitude'] = float(m.group(3))

        if 'zdef' in self.ctl:
            p = re.compile("%s\s+(\d+)\s+(\w+)" % ('zdef'))
            m = p.search(self.ctl)
            if m.group(2) == 'levels':
                p = re.compile("%s\s+(\d+)\s+levels([\s\S]+)tdef" % ('zdef'))
                m = p.search(self.ctl)
                self.variables['levels'] = np.fromstring(m.group(2),sep='\n')
                self.dimensions['levels'] = len(self.variables['levels'])
            if m.group(2) == 'linear':
                p = re.compile("%s\s+(\d+)\s+(\w+)\s+(%s)\s+(%s)" % ('zdef',NUMBER,NUMBER))
                m = p.search(self.ctl)
                self.variables['levels'] = np.arange(int(m.group(3)),int(m.group(3))+int(m.group(1))*int(m.group(4)),int(m.group(4)))
                self.dimensions['levels'] = int(m.group(1))
         
        if 'tdef' in self.ctl:
            p = re.compile("%s\s+(\d+)\s+linear\s+(\w+)\s+(\w+)\s" % ('tdef'))
            m = p.search(self.ctl)

            times = []
            initime = datetime.datetime.strptime(m.group(2), '%Hz%d%b%Y')
            self.dimensions['time'] = int(m.group(1))
            
            if 'mn' in m.group(3):
                increment = datetime.timedelta(minutes=int(re.sub("\D", "", m.group(3))))
            else:
                increment = datetime.timedelta(hours=int(re.sub("\D", "", m.group(3))))
                                                                          
            self.crement['time'] = increment

            for i in range(0,self.dimensions['time']):
                times.append(initime+increment*i)
            self.variables['time'] = times

        allvar,dim,long_name = [],[],[]  # 生成所有变量及变量对应层次、描述内容的列表
        read = False

        for line in self.ctl.split('\n'):
            if line.startswith('endvars'):
                read = False
            if read:
                p = re.compile('(\w+)\s+(\d+)\s+(\d+)\s+(.*)')    #目标变量行的正则范式
                m = p.match(line)
                allvar.append(m.group(1))
                dim.append(int(m.group(2)))
                long_name.append(m.group(4))

            if line.startswith('var'):
                read = True
        
        if not self.varname:
            self.varname = allvar

        for ivarname in self.varname:  # 此段代码来读取相应变量的数据
            var = self.variables[ivarname] = Variable(ivarname)       #生成特定的变量类并在本段方法中以"var"的别名进行描述
            index = allvar.index(ivarname)
            long_name_tmp = long_name[index]
            var.dimensions = dim[index]
            if var.dimensions == 0:  # 当读到CTL中对应的层次为0时，代表数据有一层
                var.dimensions = 1

            var.attributes = {'long_name' : long_name_tmp}

class Variable(object):    #变量类定义
    def __init__(self,name,data=None):    #创世纪
         self.name = name                  #python说：“要有名字“！于是有了变量
         self.data = data                  #python说：”要有数据“！于是有了变量
         self.variables = {} 
         self.dimensions = {}    
    def __getitem__(self,index):
         return self.data[index]
    def __getattr__(self,key):
         return self.attributes[key]
