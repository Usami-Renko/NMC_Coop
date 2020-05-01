#!/usr/bin/env python
# coding=UTF-8

'''
@Description: make compsite pics for comparison
@Author: Hejun Xie
@Date: 2020-04-26 15:11:40
@LastEditors: Hejun Xie
@LastEditTime: 2020-05-01 14:58:24
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
gif_dir = os.path.join(pic_dir, gif_dir)


def _make_comp(pic_files, comp_file):

    p = Image.open(os.path.join(origin_dir, pic_files[0]))
    f = Image.open(os.path.join(origin_dir, pic_files[1]))
    pmf = Image.open(os.path.join(origin_dir, pic_files[2]))
    
    if p.size[0] <= p.size[1] * 1.3:
        d = Image.new('RGB', (p.size[0]*3, p.size[1]))
        d.paste(p, (0, 0))
        d.paste(f, (p.size[0], 0))
        d.paste(pmf, (p.size[0]*2, 0))
    else:
        d = Image.new('RGB', (p.size[0], p.size[1]*3))
        d.paste(p, (0, 0))
        d.paste(f, (0, p.size[1]))
        d.paste(pmf, (0, p.size[1]*2))

    d.save(os.path.join(comp_dir, comp_file))

def make_comp_pic(var_time_indices, var_ndims):

    print(u"开始拼接图片")
    for ivar, var in enumerate(st_vars):
        # 24hrain has no FNL data and in align_vars

        time_indices_var = var_time_indices[var]
        ndim = var_ndims[var]

        if var in noFNL_vars:
            continue

        for iarea in plot_areas:
            for itime,time_index in enumerate(time_indices_var):
                for ilevel,level in enumerate(st_levels):
                    if ndim == 4:
                        pic_files = ['{}_{}_{}hr_{}hpa_{}.png'.format(plot_type, iarea, time_index*time_incr, int(level), var) \
                            for plot_type in plot_types]
                        comp_file = 'comp_{}_{}hr_{}hpa_{}.png'.format(iarea, time_index*time_incr, int(level), var)
                    elif ndim == 3:
                        pic_files = ['{}_{}_{}hr_{}.png'.format(plot_type, iarea, time_index*time_incr, var) for plot_type in plot_types]
                        comp_file = 'comp_{}_{}hr_{}.png'.format(iarea, time_index*time_incr, var)
                    _make_comp(pic_files, comp_file)


def make_gif_pic(var_time_indices, var_ndims):

    print(u"开始合成gif")
    for ivar, var in enumerate(st_vars):

        time_indices_var = var_time_indices[var]
        ndim = var_ndims[var]

        if ndim == 3:
            continue

        if var in noFNL_vars:
            gif_type = 'P'
            source_dir = origin_dir
        else:
            gif_type = 'comp'
            source_dir = comp_dir

        for iarea in plot_areas:
            for itime, time_index in enumerate(time_indices_var):
                
                pic_files = ['{}/{}_{}_{}hr_{}hpa_{}.png'.format(source_dir, gif_type, iarea, time_index*time_incr,int(level), var) \
                    for level in st_levels]
                gif_file = '{}/{}_{}_{}hr_{}_pres.gif'.format(gif_dir, gif_type, iarea, time_index*time_incr, var)
            
                imgs = [Image.open(ipic) for ipic in pic_files]
                imgs[0].save(gif_file, save_all=True, append_images=imgs, duration=2)
