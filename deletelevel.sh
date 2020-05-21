#/bin/sh

###
 # @Description: delete unnecessary levels in new FNL data
 # @Author: Hejun Xie
 # @Date: 2020-05-21 11:24:29
 # @LastEditors: Hejun Xie
 # @LastEditTime: 2020-05-21 11:35:57
### 

path=./fnl_data/2019/
files=$(ls $path)
# echo $files

for file in $files
do
	cdo delete,name=gh,t,level=1500,4000 $path/$file $path/$file.tmp
done
