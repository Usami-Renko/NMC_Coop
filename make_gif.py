#!/usr/bin/env python
# coding=UTF-8

'''
@Description: make gif pics
@Author: Hejun Xie
@Date: 2020-04-26 15:27:26
@LastEditors: Hejun Xie
@LastEditTime: 2020-04-26 15:31:12
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

    print('开始合成gif')
    for iarea in plot_areas:
        for itime, time_index in enumerate(time_indices):
            for ivar, var in enumerate(st_vars):
                gif_file = './pic/comp_{}_{}hr_{}_pres.gif'.format(iarea, time_index*time_incr, var)
                pic_files = []
                for ilevel,level in enumerate(st_levels):
                    pic_files.append('./pic/comp_{}_{}hr_{}hpa_{}.png'.format(iarea, time_index*time_incr,int(level), var))
                
                imgs = []
                for ipic in pic_files:
                    temp = Image.open(ipic)
                    imgs.append(temp)
                    # os.system('rm {}'.format(ipic))
                imgs[0].save(gif_file,save_all=True,append_images=imgs,duration=2)
