# -*- coding:utf-8 -*-
# ThirdBeamLayer.py

# 本脚本的运行环境为Anaconda, conda 4.1.4。
# 本脚本用于生成坐标数据，第三层（斜向）杆件的连接坐标点数据。
# 坐标数据为np.array格式:(deformed(float), deformed(float), deformed(float))
# 算法：
# 导入模型坐标文件(shelve格式)，modelPoints-XX.dat, 其中注意InnerPoints
# 导入后处理坐标文件(shelve格式)，washedPoints-XX.dat, 其中包括InnerPoints
# 得到内部点在变形后x,y,z的单精度坐标

import handytools as hd
import numpy as np
import shelve