# -*- coding:utf-8 -*-
# filename: iterprocess.py
from handytools import *
from operator import itemgetter, attrgetter
from pprint import pprint

# 读入(x,y,z)，其中(x,y)是原来的坐标,z是竖向位移的向量


f = open(r'C:\Users\aweff\Documents\03.python\pycharm_projects\data\referencePoint_washed-7.txt','r')
data = mylst()
data_for_iteration = mylst([(0.0,0.0),(60.0,0.0),])
factor = 0.5
for line in f:
    temp = None
    exec('temp = '+line)
    if temp[1] > 0:
        data.append(temp)
data = mylst(
    sorted(data, key=itemgetter(2,))
)
deformation = data.getz()
average_deformation = sum(deformation) / len(deformation)
err = 0.0;
print 'average_deformation:'+str(average_deformation)

# print 'base_deformation:', base_deformation


for point in data:
    err += abs(point[2]-average_deformation)
    temp = (point[0],\
            point[1]+factor*(point[2]-average_deformation),)
    data_for_iteration.append(temp)
err = err / len(deformation)
data_for_iteration = sorted(data_for_iteration,key=itemgetter(0))
# pprint({'data_for_iteration':data_for_iteration})

# curve = LinearInterpolation(data_for_iteration)
# for y in range(0,17,1):
#     print curve.findX(y,pointFormat=True)
# showCurve(data_for_iteration)
result = coord_generator(data_for_iteration,start=0.0,end=60.0)
# pprint(result)
def result_visualize(result):
    plt.figure()
    plt.scatter(result['inCoordPoints'].getx(),result['inCoordPoints'].gety(),s=50,alpha=0.5)
    i = 0
    while True:
        point_lst = mylst(result['yCoordPoints'][i:i+2])
        plt.plot(point_lst.getx(), point_lst.gety(), lw=2.5)
        i += 2
        if i + 1 > len(result['yCoordPoints']):
            break
    j = 0
    while True:
        point_lst2 = mylst(result['xCoordPoints'][j:j+2])
        # pprint(point_lst2)
        plt.plot(point_lst2.getx(),point_lst2.gety(),lw=2.5)
        j += 2
        if j + 1>len(result['xCoordPoints']):
            break
    plt.show()
result_visualize(result)

abaqusInputDataGenerator(outPath=r'C:\Users\aweff\Documents\03.python\pycharm_projects\data\modelPoints-8.txt',\
                         log = 'Rang Wo Zhuang Bi Rang Wo Fei !!! 8th time!',
                         **result)
print 'average_deformation: '+str(average_deformation)
print 'Error: '+str(err)