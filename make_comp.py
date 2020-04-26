#!/usr/bin/env python
# coding=UTF-8

'''
@Description: make compsite pics for comparison
@Author: Hejun Xie
@Date: 2020-04-26 15:11:40
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-26 15:26:21
'''


from utils import config
from PIL import Image


# read the config file
cong = config()

for key, value in cong.items():
    globals()[key] = value


# Main Program
if __name__ == "__main__":
    
    time_indices = [int(i/time_incr) for i in fcst]

    print("开始拼接图片")
    for iarea in plot_areas:
            for itime,time_index in enumerate(time_indices):
                for ivar, var in enumerate(st_vars):
                    for ilevel,level in enumerate(st_levels):
                        pic_dir = './pic/'
                        pic_files = ['{}_{}_{}hr_{}hpa_{}.png'.format(plot_type, iarea, time_index*time_incr, int(level), var) for plot_type in plot_types]
                        p = Image.open(pic_dir + pic_files[0])
                        f = Image.open(pic_dir + pic_files[1])
                        pmf = Image.open(pic_dir + pic_files[2])
                        
                        d = Image.new('RGB', (p.size[0]*3, p.size[1]))
                        d.paste(p, (0, 0))
                        d.paste(f, (p.size[0], 0))
                        d.paste(pmf, (p.size[0]*2, 0))

                        comp_file = 'comp_{}_{}hr_{}hpa_{}.png'.format(iarea, time_index*time_incr, int(level), var)
                        d.save(pic_dir+comp_file)
