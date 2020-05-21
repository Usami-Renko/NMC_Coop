#/bin/sh

###
 # @Description: delete unnecessary levels in new FNL data
 # @Author: Hejun Xie
 # @Date: 2020-05-21 11:24:29
 # @LastEditors: Hejun Xie
 # @LastEditTime: 2020-05-21 12:11:47
### 

year=2019

path=./fnl_data/
outpath=./temp/fnl_data_tmp/

files=$(ls $path/$year)
# echo $files

mkdir $outpath
mkdir $outpath/$year


for file in $files
do
	cdo delete,name=gh,t,level=1500,4000 $path/$year/$file $outpath/$year/$file
done
