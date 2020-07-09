#!/usr/bin/env python
# coding=UTF-8

'''
@Description: make compsite pics for comparison
@Author: Hejun Xie
@Date: 2020-04-26 15:11:40
@LastEditors: Hejun Xie
@LastEditTime: 2020-07-09 11:59:02
'''


from PIL import Image
from copy import copy
import os
from utils import makenewdir
import numpy as np
import glob


def config_submodule(cong, pic_dir):

    global origin_dir, zonalmean_dir, comp_dir, gif_dir, st_levels

    for key, value in cong.items():
        globals()[key] = value

    origin_dir = os.path.join(pic_dir, origin)
    comp_dir = os.path.join(pic_dir, comp)
    gif_dir = os.path.join(pic_dir, gif)
    zonalmean_dir = os.path.join(pic_dir, zonalmean)

    if plot_zonalmean:
        st_levels = ex_levels
    else:
        st_levels = plot_levels

def sort_components(pic_file):

    plot_type = pic_file.split('/')[-1].split('.')[-2].split('_')[0]
    if plot_type == 'G':
        return 0
    elif plot_type == 'F':
        return 1
    elif plot_type == 'GMF':
        return 2
    elif plot_type == 'GMG':
        return 3
    else:
        raise ValueError("unknown plot_type: {}".format(plot_type))

def _make_comp(pic_files, comp_file):

    pic_files.sort(key=sort_components)

    if len(pic_files) == 2:
        return _make_comp2(pic_files, comp_file)
    elif len(pic_files) == 3:
        return _make_comp3(pic_files, comp_file)
    elif len(pic_files) == 4:
        return _make_comp4(pic_files, comp_file)
    else:
        raise ValueError("Too many or too little components to make comp: {}".format(comp_file))

def _make_comp4(pic_files, comp_file):

    p = Image.open(pic_files[0])
    f = Image.open(pic_files[1])
    pmf = Image.open(pic_files[2])
    pmp = Image.open(pic_files[3])
    
    d = Image.new('RGB', (p.size[0]*2, p.size[1]*2))
    d.paste(p,   (0,         0))
    d.paste(f,   (p.size[0], 0))
    d.paste(pmf, (0,         p.size[1]))
    d.paste(pmp, (p.size[0], p.size[1]))

    return d

def _make_comp3(pic_files, comp_file):

    p = Image.open(pic_files[0])
    f = Image.open(pic_files[1])
    pmf = Image.open(pic_files[2])
    
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

    return d

def _make_comp2(pic_files, comp_file):

    p = Image.open(pic_files[0])
    f = Image.open(pic_files[1])
    
    if p.size[0] <= p.size[1] * 1.3:
        d = Image.new('RGB', (p.size[0]*2, p.size[1]))
        d.paste(f, (0, 0))
        d.paste(p, (p.size[0], 0))
    else:
        d = Image.new('RGB', (p.size[0], p.size[1]*2))
        d.paste(f, (0, 0))
        d.paste(p, (0, p.size[1]))
        
    return d

def make_comp_pic(var_time_indices, var_ndims, var_plot_areas, time_incr):

    print("开始拼接图片")
    for ivar, var in enumerate(st_vars):
        # 24hrain has no FNL data and in align_vars

        time_indices_var = var_time_indices[var]
        ndim = var_ndims[var]

        if var in noFNL_vars and var != '24hrain':
            continue

        var_dir = os.path.join(comp_dir, var)
        makenewdir(var_dir)

        for iarea in var_plot_areas[var]:
            if var == '24hrain' and iarea != 'E_Asia':
                continue

            var_plot_types = copy(plot_types)
            if var == '24hrain' and 'GMF' in plot_types:
                var_plot_types.remove('GMF')
            
            print(var, var_plot_types)
            
            for itime,time_index in enumerate(time_indices_var):
                
                # [I]. make comp for isobaric surface
                for level in plot_levels:
                    ilevel = st_levels.index(level)
                    if ndim == 4:
                        match = '{}/{}/*_{}_{}hr_{}hpa_{}.png'.format(origin_dir, var, iarea, time_index*time_incr, int(level), var)
                        pic_files = glob.glob(match)
                        comp_file = 'comp_{}_{}hr_{}hpa_{}.png'.format(iarea, time_index*time_incr, int(level), var)
                    elif ndim == 3:
                        match = '{}/{}/*_{}_{}hr_{}.png'.format(origin_dir, var, iarea, time_index*time_incr, var) 
                        pic_files = glob.glob(match)
                        comp_file = 'comp_{}_{}hr_{}.png'.format(iarea, time_index*time_incr, var)
                    
                    d = _make_comp(pic_files, comp_file)
                    d.save(os.path.join(comp_dir, var, comp_file))
                
                # [II]. make comp for zonal mean 
                if plot_zonalmean:
                    if var in noFNL_vars or iarea != 'Global':
                        continue
                    
                    match = '{}/{}/*_{}_{}hr_zonalmean_{}.png'.format(zonalmean_dir, var, iarea, time_index*time_incr, var)
                    pic_files = glob.glob(match)
                    comp_file = 'comp_{}_{}hr_zonalmean_{}.png'.format(iarea, time_index*time_incr, var)

                    d = _make_comp(pic_files, comp_file)
                    d.save(os.path.join(comp_dir, var, comp_file))


def make_gif_pic(var_time_indices, var_ndims, var_plot_areas, time_incr):

    print("开始合成gif")
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
        
        var_dir = os.path.join(gif_dir, var)
        makenewdir(var_dir)

        for iarea in var_plot_areas[var]:
            for itime, time_index in enumerate(time_indices_var):
                
                pic_files = ['{}/{}/{}_{}_{}hr_{}hpa_{}.png'.format(source_dir, var, gif_type, iarea, time_index*time_incr,int(level), var) \
                    for level in st_levels]
                gif_file = '{}/{}/{}_{}_{}hr_{}_pres.gif'.format(gif_dir, var, gif_type, iarea, time_index*time_incr, var)

                if not np.array([os.path.exists(pic_file) for pic_file in pic_files]).all():
                    print("[warning]: failed to make gif {} due to missing components".format(gif_file))
                    break

                imgs = [Image.open(ipic) for ipic in pic_files]
                imgs[0].save(gif_file, save_all=True, append_images=imgs, duration=2)
