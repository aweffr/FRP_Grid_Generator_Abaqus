# -*- coding:utf-8 -*-
# file:testcase1.py
from handytools import *
import os

testlst = [(0.0, 0.0),
           (2.0,6.80),
           (5.0, 10.77),
           (10.0, 12.70),
           (15.0, 12.13),
           (20.0, 11.73),
           (25.0, 12.20),
           (30.0, 13.37),
           (35.0, 14.64),
           (40.0, 14.89),
           (45.0, 11.69),
           (48.0, 7.02),
           (50.0, 0.00)]
result = coord_generator(testlst)
print 'the keys of output is:\n\t',result.keys()
# pprint(result['inCoordPoints'])

def result_visualize(result):
    plt.figure()
    plt.scatter(result['inCoordPoints'].getx(),result['inCoordPoints'].gety(),s=40,alpha=0.5)
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
abaqusInputDataGenerator(outPath=r'C:\Users\aweff\Documents\03.python\pycharm_projects\data\modelPoints.txt',\
                         **result)
os.startfile(r'C:\Users\aweff\Documents\03.python\pycharm_projects\data\modelPoints.txt')