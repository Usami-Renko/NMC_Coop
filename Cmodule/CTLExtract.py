# -*- coding: utf-8 -*- 
"""
调用grads来提取grads数据中相应的变量
2018.03.23
Author ：wanghao
"""
import pandas as pd
import numpy as np
import datetime
import re
import os

# 调用grads

NUMBER = '[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'

class CTLExtract(object):
    def __init__(self,ctlfilename,varname,Ex_levels,extract_ctl,extract_data):
        self.variables = {}
        self.dimensions = {}
        self.crement = {}
        self.attributes = {}
        self.ctlfilename = ctlfilename
        self.varname = varname
        self.Ex_levels  = Ex_levels
        self.extract_ctl  = extract_ctl
        self.extract_data = extract_data

        #将ctl文件信息读入一个巨大的字符串中便于之后应用
        with open(self.ctlfilename,'r') as f:
            self.ctl = f.read()     

        self._read_dimensions() #获取ctl中的维度信息
        self._extract_data() #提取所需的变量
        self._generate_ctl() #生成新数据对应的ctl

        f.close()
 
    def _read_dimensions(self):

        if 'xdef' in self.ctl:
            p = re.compile("%s\s+(\d+)\s+linear\s+(%s)\s+(%s)" % ('xdef',NUMBER,NUMBER))
            m = p.search(self.ctl)
            self.dimensions['longitude'] = int(m.group(1))

        if 'ydef' in self.ctl:
            p = re.compile("%s\s+(\d+)\s+linear\s+(%s)\s+(%s)" % ('ydef',NUMBER,NUMBER))
            m = p.search(self.ctl)
            self.dimensions['latitude'] = int(m.group(1))
        
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
        
        # print(self.variables['levels'])
        # print(self.Ex_levels)

        if 'tdef' in self.ctl:
            p = re.compile("%s\s+(\d+)\s+linear\s+(\w+)\s+(\w+)\s" % ('tdef'))
            m = p.search(self.ctl)
            self.dimensions['time'] = int(m.group(1))

        allvar,dim,att = [],[],[]  # 生成所有变量及变量对应层次、描述内容的列表

        read = False  #识别是否为目标变量的开关

        for line in self.ctl.split('\n'):
            if line.startswith('endvars'):
                read = False
            if read:
                p = re.compile('(\w+)\s+(\d+)\s+(\d+)\s+(.*)')    #目标变量行的正则范式
                m = p.match(line)
                allvar.append(m.group(1))
                dim.append(int(m.group(2)))

            if line.startswith('var'):
                read = True

        for ivarname in self.varname:  # 此段代码来读取相应变量的数据
            index = allvar.index(ivarname)
            self.dimensions[ivarname] = dim[index]
            if self.dimensions[ivarname] == 0:  # 当读到CTL中对应的层次为0时，代表数据有一层
                self.dimensions[ivarname] = 1

    def _extract_data(self):

        extract_gs = 'extract.gs'
        
        # 
        level_index = []
        for ilevel in self.Ex_levels:
            level_index.append(self.variables['levels'].tolist().index(ilevel)+1)

        # print(level_index)

        with open(extract_gs,"w") as f:
            f.write("'reinit'\n")
            f.write("'open %s'\n" % self.ctlfilename)
            f.write("'set gxout fwrite'\n")
            f.write("'set fwrite %s'\n\n" % self.extract_data)

            f.write("it=1\n")

            f.write("while(it<=%d)\n" % self.dimensions['time'])
            f.write("'set t 'it''\n")
            f.write("'set y 1 %d'\n" % self.dimensions['latitude'])
            f.write("'set x 1 %d'\n\n" % self.dimensions['longitude'])


            for ivar in self.varname:
                if self.dimensions[ivar] == 1:
                    f.write("'set z 1'\n")
                    f.write("'d %s'\n" % ivar)
                else:
                    for iz in level_index:
                        # f.write("iz=1\n")
                        # f.write("while(iz<=%d)\n" % self.dimensions[ivar])
                        f.write("'set z {}'\n".format(iz))
                        f.write("'d %s'\n" % ivar)
                        # f.write("iz=iz+1\n")
                        # f.write("endwhile\n\n")

            f.write("it=it+1\n")
            f.write("endwhile\n\n")

            f.write("'disable fwrite'\n")
            f.write("'reinit'\n")
            f.write("quit\n")
        
        f.close()

        strCmd = "grads -lbc " + extract_gs
        os.system(strCmd)  # 调用系统命令执行grads

    def _generate_ctl(self):

        read = False  # 识别是否为目标变量的开关

        # extract_ctl = self.extract + '.ctl'

        fwrite = open(self.extract_ctl,"w")

        ncount = 0
        
        folder_path, extract_data = os.path.split(self.extract_data)

        for line in self.ctl.split('\n'):

            if 'dset' in line:
                fwrite.write('dset ^'+extract_data+'\n')
                continue

            if 'template' in line:
                fwrite.write(line.replace('template',' ')+'\n')
                continue
            
            if 'xdef' in line:
                fwrite.write(line+'\n')
                continue

            if 'ydef' in line:
                fwrite.write(line+'\n')
                continue

            if 'zdef' in line:
                # fwrite.write('zdef {} levels\n'.format(len(self.Ex_levels)))
                fwrite.write(line.replace('{}'.format(self.dimensions['levels']), '{}'.format(len(self.Ex_levels)))+'\n')
                for ilevel in self.Ex_levels:
                    fwrite.write('  {}\n'.format(ilevel))
                continue
            
            if 'tdef' in line:
                fwrite.write(line+'\n')
                continue
            
            p = re.compile("(%s)\s" % (NUMBER))
            m = p.search(line)
            if m:
                # print(m.group(1))
                if float(m.group(1)) in self.variables['levels'][:]:
                    continue

            if line.startswith('var'):
                fwrite.write('vars %d\n' % (len(self.varname)))
                break
            
            else:
                fwrite.write(line+'\n')

        for line in self.ctl.split('\n'):

            if line.startswith('endvars'):
                fwrite.write(line+'\n')
                read = False
            if read:
                p = re.compile('(\w+)\s+(\d+)\s+(\d+)\s+(.*)')    #目标变量行的正则范式
                m = p.match(line)
                if m.group(1) in self.varname:
                    if self.dimensions[m.group(1)] == 1:
                        fwrite.write(line+'\n')
                    else:
                        fwrite.write('{} {} {} {}\n'.format(m.group(1),len(self.Ex_levels),m.group(3),m.group(4)))
            if line.startswith('var'):
                read = True
        
        fwrite.close()
