<!--
 * @Description: README
 * @Author: Hejun Xie
 * @Date: 2020-04-23 20:31:50
 * @LastEditors: Hejun Xie
 * @LastEditTime: 2020-04-23 21:35:37
 -->
# GRAPES预报场与FNL分析场诊断画图脚本V1.0

## 1、数据提取模块

extractdata.py

从 GRAPES postvar 数据中诊断画图提取所需的变量, 并存储为nc格式的数据。
放置在提取数据目录下。

## 2. 绘图模块

plotmap.py

plot_data 函数 绘制单个变量的不同区域的地图投影填色图。
find_clevels 函数 自动根据输入的数据和绘图区域设置填色图的色标范围。

## 3. 工具模块

utils.py

用于暂时存储画图所需的变量的一个装饰器类 DATAdecorator。 
防止调整绘图脚本时重复进行数据计算, 方便绘图调试。
如果不需要重新获取数据，可将装饰器参数中的speedup选项设置为 False

读取配置文件的函数 config。

## 4. 绘图脚本模块

目的
----------

计算GRAPES不同起报时间集合下不同预报时效的平均预报场
并与对应预报时效下的FNL再分析平均场进行对比

层次结构
----------

包含两个形式上的函数, 和一个主程序脚本
get_GRAPES_data， get_FNL_data

get_GRAPES_data 
读取GRAPES提取出的nc格式的数据，并计算起报时间集合下不同预报时效的平均预报场

get_FNL_data
读取FNL再分析数据，并线性插值到GRAPES网格下,计算起报时间集合下不同预报时效的平均预报场

主程序对两个场分别进行画图，并分析两者的差值画图

目前将所需修改的内容提取到配置文件中，存放在同级目录的config文件夹下，包含一个配置文件：config.yml

- config.yml, 画图设置和提取数据设置。
```
# 起报时间信息
start_ddate: '2016010112'  # yyyymndd
end_ddate  : '2016010512'  # yyyymndd

# 起报时间间隔
fcst_step: 24 # hours

# GRAPES数据路径 
ctlfile_dir: './87_fcst_ctl/'

# GRAPES数据转换路径
exdata_dir: './ex_data/'

# FNL数据路径
fnl_dir: './fnl_data/'

# FNL数据变量名
fnl_varname:
  u: 'UGRD_P0_L100_GLL0'
  v: 'VGRD_P0_L100_GLL0'
  t: 'TMP_P0_L100_GLL0'
  h: 'HGT_P0_L100_GLL0'

# 统计变量和统计等压层
st_vars  : ['u','v','t','h']
st_levels: [1000.,925.,850.,700.,600.,500.,400.,300.,200.,100.,50.,10.]

# 预报时长
fcst: [0,72] # hours

# 图片类型
pic_prefix: 'png'

# 是否绘制单个图
make_png: True

# 是否绘制不同高度的动图
make_gif: True

# 是否绘制用于比较的拼图
make_concat: True

# 画图区域设置
plot_areas: ['Global', 'E_Asia', 'North_P', 'South_P']

# 画图类型设置 
plot_types: ['P', 'F', 'PMF']

# 画图类型名称
plot_types_name:
  P:    'Prediction'
  F:    'FNL'
  PMF:  'Prediction - FNL'

# 填色色标间隔
clevel_step:
  u: 2
  v: 2
  t: 3
  h: 30

clevel_step_PMF:
  u: 1
  v: 1
  t: 1
  h: 10

# 变量名称
variable_name:
  t:  'Temperature [K]'
  u:  'U Wind [m/s]'
  v:  'V wind [m/s]'
  h:  'Geopotential Height [gpm]'
```

使用方式
----------

1. 提取postvar数据
修改./config/config.yml后，运行python extractdata.py即可，
```python
python extractdata.py
```

2. 画图
手动添加 ./pic/目录
修改./config/config.yml后，运行python plot_postvar.py即可，
```python
python plot_postvar.py
```

图形展示
----------
- Prediction
![avatar](./pic_eg/P_North_P_72hr_500hpa_h.png)
- FNL
![avatar](./pic_eg/F_North_P_72hr_500hpa_h.png)
- Prediction - FNL
![avatar](./pic_eg/PMF_North_P_72hr_500hpa_h.png)

- Composite for comparison
![avatar](./pic_eg/comp_North_P_72hr_500hpa_u.png)

----------
Developers and Contributors
----------

王皓 - 中国气象局数值预报中心

谢和俊 - 浙江大学地球科学学院
