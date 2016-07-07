# -*- coding:utf-8 -*-
# ThirdBeamLayer.py

# 本脚本的运行环境为Anaconda, conda 4.1.4。
# 本脚本用于生成坐标数据，第三层（斜向）杆件的连接坐标点数据。

import numpy as np
import shelve
import operator

def classification(inlst,):
	# 利用其原坐标处于一条直线上进行分类
    outDir = {}
    for point in inlst:
        tempValue = point[1] - point[0]
        if outDir.has_key(tempValue):
            outDir[tempValue].append(point)
        else:
            outDir[tempValue] = [point,]
    return outDir

modelFile = shelve.open("modelPoints-Current.dat")
time = modelFile['time']
modelFile.close()

odbDeformationData = shelve.open("washedPoints-Closer-Multi3-11.dat")

Inner_Points = f["Inner_Points"]
Inner_Points = sorted(Inner_Points, key=operator.itemgetter(0,1))
Inner_Points = Inner_Points[::2]

classifiedDict = classification(Inner_Points,)

odbDeformationData.close()

out = shelve.open("thirdBeam-%d.dat"%time)
out["log"] = "key word: 'pointDict'."
out["pointDict"] = classifiedDict
out.close()


