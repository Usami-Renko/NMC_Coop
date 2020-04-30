#!/usr/bin/env python
# coding=UTF-8

'''
@Description: make gif pics
@Author: Hejun Xie
@Date: 2020-04-26 15:27:26
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-30 12:35:44
'''


from utils import config_list
from PIL import Image
import os


# read the config file
cong = config_list(['config.yml', 'devconfig.yml'])

for key, value in cong.items():
    globals()[key] = value

origin_dir = os.path.join(pic_dir, origin_dir)
comp_dir = os.path.join(pic_dir, comp_dir)
gif_dir = os.path.join(pic_dir, gif_dir)

# Main Program
if __name__ == "__main__":

    time_indices = [int(i/time_incr) for i in fcst]

    print('开始合成gif')
    for iarea in plot_areas:
        for itime, time_index in enumerate(time_indices):
            for ivar, var in enumerate(st_vars):
                
                if var in noFNL_vars:
                    gif_type = 'P'
                    origin_dir = origin_dir
                else:
                    gif_type = 'comp'
                    origin_dir = comp_dir
                
                if var in moist_vars and time_index == 0:
                    continue
                
                gif_file = '{}/{}_{}_{}hr_{}_pres.gif'.format(gif_dir, gif_type, iarea, time_index*time_incr, var)
                pic_files = []
                for ilevel,level in enumerate(st_levels):
                    pic_files.append('{}/{}_{}_{}hr_{}hpa_{}.png'.format(origin_dir, gif_type, iarea, time_index*time_incr,int(level), var))
                
                imgs = []
                for ipic in pic_files:
                    temp = Image.open(ipic)
                    imgs.append(temp)
                    # os.system('rm {}'.format(ipic))
                imgs[0].save(gif_file,save_all=True,append_images=imgs,duration=2)
