#!/usr/bin/env python
# coding=UTF-8

'''
@Description: make compsite pics for comparison
@Author: Hejun Xie
@Date: 2020-04-26 15:11:40
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-30 13:39:06
'''


from utils import config_list
from PIL import Image
from copy import copy
import os


# read the config file
cong = config_list(['config.yml', 'devconfig.yml'])

for key, value in cong.items():
    globals()[key] = value

origin_dir = os.path.join(pic_dir, origin_dir)
comp_dir = os.path.join(pic_dir, comp_dir)

# Main Program
if __name__ == "__main__":
    
    time_indices = [int(i/time_incr) for i in fcst]

    print(u"开始拼接图片")
    for ivar, var in enumerate(st_vars):
        # 24hrain has no FNL data and in align_vars
        if var in noFNL_vars:
            continue

        time_indices_var = copy(time_indices)
        if var in moist_vars and 0 in time_indices_var:
            time_indices_var.remove(0)

        for iarea in plot_areas:
            for itime,time_index in enumerate(time_indices_var):
                    for ilevel,level in enumerate(st_levels):
                        pic_files = ['{}_{}_{}hr_{}hpa_{}.png'.format(plot_type, iarea, time_index*time_incr, int(level), var) for plot_type in plot_types]
                        p = Image.open(os.path.join(origin_dir, pic_files[0]))
                        f = Image.open(os.path.join(origin_dir, pic_files[1]))
                        pmf = Image.open(os.path.join(origin_dir, pic_files[2]))
                        
                        if p.size[0] <= p.size[1]:
                            d = Image.new('RGB', (p.size[0]*3, p.size[1]))
                            d.paste(p, (0, 0))
                            d.paste(f, (p.size[0], 0))
                            d.paste(pmf, (p.size[0]*2, 0))
                        else:
                            d = Image.new('RGB', (p.size[0], p.size[1]*3))
                            d.paste(p, (0, 0))
                            d.paste(f, (0, p.size[1]))
                            d.paste(pmf, (0, p.size[1]*2))

                        comp_file = 'comp_{}_{}hr_{}hpa_{}.png'.format(iarea, time_index*time_incr, int(level), var)
                        d.save(os.path.join(comp_dir, comp_file))
