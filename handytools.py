# -*- coding:utf-8 -*-
# handytools.py
# 本模块含有如下内容：
# class->mylst,用于生成单独的x坐标列表，y坐标列表，以及将列表内的点变成3D坐标
# class->LinearInterpolation,给定一系列平面的点，按x坐标排序后进行线性的插值，findX命令用于寻找y坐标对应于x的根
# function->用于与Mathematica生成的坐标txt接口，处理数据
# function->mirror(inlst, sort_order),给定一系列平面的点，输出其按x坐标轴翻转后的点与原来的点的集合的点。
# function->abaqusInputDataGenerator(**kwargs),将结果输出成Abaqus建模脚本的数据格式
import matplotlib.pyplot as plt
import numpy as np
import shelve
from pprint import pprint
from math import ceil, floor
from operator import itemgetter, attrgetter

class mylst(list):
    # 继承自list，数据格式[point, point, point, ...]
    def getx(self):
        out = []
        for point in self:
            out.append(point[0])
        return out
    def gety(self):
        out = []
        for point in self:
            out.append(point[1])
        return out
    def getz(self):
        out = []
        for point in self:
            out.append(point[2])
        return out
    def threeD(self,z_offset=0.0):
        out = []
        for point in self:
            out.append((point[0]+0.0, point[1]+0.0, z_offset),)
        return out

class LinearInterpolation(object):
    def __init__(self, inlst):
        # 输入inlst的格式：[point, point, point, ...]
        self.pointdata = mylst(sorted(inlst, key = lambda x: x[0]),)
        print 'The interpolation points sorted by x:\n\t'+str(self.pointdata)
        self.inflectionPoint = mylst()
        self.inflectionPointFinder()
        print 'inflectionPoint is:\n\t'+str(self.inflectionPoint)
        
    def inflectionPointFinder(self):
        i = 1
        length = len(self.pointdata)
        while True:
            if (self.pointdata[i-1][1] - self.pointdata[i][1]) * (self.pointdata[i][1] - self.pointdata[i+1][1]) < 0:
                self.inflectionPoint.append(self.pointdata[i])
            i += 1
            if i+1 >= length:
                break
                
    
    def getY(self, x_val, pointFormat=False):
        # 输入一个x的值，返回一个y的值
        # 当pointFormat=True,返回point元组
        x_val = x_val + 0.0
        # x_left, x_right, y_left, y_right = 0.0, 0.0 ,0.0 ,0.0
        for i in range(len(self.pointdata)-1,):
            # 一旦找到x_val所在的区间，循环就终止
            if self.pointdata[i][0] <= x_val and self.pointdata[i+1][0] >= x_val:
                x_left = self.pointdata[i][0]
                y_left = self.pointdata[i][1]
                x_right = self.pointdata[i+1][0]
                y_right = self.pointdata[i+1][1]
                # print 'Find x in region: (%.3f, %.3f), (%.3f, %.3f)'%(x_left,y_left,x_right,y_right)
                break
        y_val = (x_val-x_left) * (y_left-y_right)/(x_left-x_right) + y_left
        if pointFormat:
            return (x_val, y_val)
        else:
            return y_val
    
    def findX(self, y_val, pointFormat=False):
        # 本函数要声明对于y坐标共有几个根，并返回这些根的值
        # 当pointFormat=True,返回point元组
        y_val = y_val + 0.0
        i = 0
        root_num = 0
        out = {'root_x':[None,],'log':str(),'root_numbers':root_num}
        out_point_format = mylst()
        for i in range(len(self.pointdata)-1,):
            cmp = sorted([self.pointdata[i][1],self.pointdata[i+1][1]],)
            x_left = self.pointdata[i][0]
            y_left = self.pointdata[i][1]
            x_right = self.pointdata[i+1][0]
            y_right = self.pointdata[i+1][1]
            root_found = False
            if cmp[0] < y_val and y_val < cmp[1]:
                root_found = True
                x_root = (y_val - y_left)*(x_right - x_left)/(y_right - y_left) + x_left
            elif abs(y_val - y_left) < 0.0001:
                root_found = True
                x_root = x_left
            elif abs(y_val - y_right) < 0.0001:
                root_found = True
                x_root = x_right
            if root_found and out['root_x'][-1]!=x_root:
                # print 'Now comparing point is (%.3f, %.3f), (%.3f, %.3f),and root found as (%.3f, %3f)'\
                #                              %(x_left, y_left, x_right, y_right, x_root, y_val)
                root_num += 1
                out['root_x'].append(x_root)
                out_point_format.append((x_root,y_val),)
        del out['root_x'][0]
        out['log'] = '%d root(s) found.'%root_num
        out['root_numbers'] = root_num
        if pointFormat:
            return out_point_format
        else:
            return out

def mirror(inlst, sort_order='x'):
    # 输入一系列平面第一象限的点，输出其点本身和关于x轴镜像后的点的集合，并根据需求排序。
    outlst = mylst()
    for point in inlst:
        mirror_point = (point[0], -point[1])
        outlst.append(point,)
        outlst.append(mirror_point,)
    # 在排序之前先进行坐标点去重
    outlst = list(set(outlst))
    if sort_order=='x':
        outlst = mylst(sorted(outlst, key=itemgetter(0,1)))
    if sort_order=='y':
        outlst = mylst(sorted(outlst, key=itemgetter(1,0)))
    return outlst

def showCurve(inlst):
    curve_function = LinearInterpolation(inlst)
    length = len(inlst)
    plt.figure()
    plt.plot([x for x in range(length)],[curve_function.getY(x) for x in range(length)])
    plt.show()

def coord_generator(inlst, interval=1.0, start=0.0, end=50.0):
    # 输入一系列边界点（二维,即其在第一象限的数据），生成根据此边界点生成的：
    # (1)基于x坐标轴的点,xCoordPoints
    # (2)基于y坐标轴的点,yCoordPoints
    # (3)基于上述坐标的内部的交点,inCoordPoints
    xCoordPoints = mylst()
    yCoordPoints = mylst()
    inCoordPoints = mylst()
    curve_function = LinearInterpolation(inlst)
    out = dict()

    # 生成x坐标轴的点
    x_temp, y_temp = 0.0, 0.0
    for x_temp in np.arange(start+interval, end, interval):
        y_temp = curve_function.getY(x_temp)
        xCoordPoints.append((x_temp, y_temp),)
    xCoordPoints = mirror(xCoordPoints, sort_order='x')

    # 生成y坐标轴的点
    # 寻找y的最大值
    # x_temp, y_temp = 0.0, 0.0
    # 为了避免出现边界上过于短的y轴杆件，需要对y_max做折减
    y_max = sorted(xCoordPoints.gety(),)[-1] - 0.25
    for y_temp in np.arange(0.0, y_max, interval):
        root_point_lst = curve_function.findX(y_temp, pointFormat=True)
        root_point_lst_2 = []
        print 'When y equals %.2f, root points found as: '%y_temp + str(root_point_lst)
        if len(root_point_lst)%2 != 0 and len(root_point_lst) > 2:
            print 'Exception roots!:', root_point_lst
        for point in root_point_lst:
            if not point in curve_function.inflectionPoint:
                yCoordPoints.append(point)
            else:
                print '(%.3f,%.3f) has been elimated.'%point

    yCoordPoints_Washed = []
    for i in range(0,len(yCoordPoints), 2):
        if abs(yCoordPoints[i][0] - yCoordPoints[i+1][0]) > 5.0:
            yCoordPoints_Washed.append(yCoordPoints[i])
            yCoordPoints_Washed.append(yCoordPoints[i+1])
    yCoordPoints = mirror(yCoordPoints_Washed, sort_order='y')

    # 生成inCoordPoints
    for i in range(0, len(yCoordPoints), 2):
        x_temp_left = yCoordPoints[i][0]
        y_temp_left = yCoordPoints[i][1]
        x_temp_right = yCoordPoints[i+1][0]
        y_temp_right = yCoordPoints[i+1][1]
        if x_temp_left > x_temp_right:
            x_temp_left, x_temp_right = x_temp_right, x_temp_left
        # print 'y_temp_left == y_temp_right?, %.4f == %.4f, Result: %s'%(y_temp_left, y_temp_right, str(y_temp_left == y_temp_right))
        # print 'x_temp_left = %.4f, x_temp_right = %.4f np.arange: %s'%(x_temp_left, x_temp_right, str(np.arange(ceil(x_temp_left), x_temp_right, interval)))
        if y_temp_left == y_temp_right:
            for x_temp in np.arange(ceil(x_temp_left+0.005), x_temp_right-0.005, interval):
                if abs(curve_function.getY(x_temp)-abs(y_temp_left))>0.004:
                    inCoordPoints.append((x_temp,y_temp_left),)
        elif y_temp_left != y_temp_right:
            print 'Current yCoordPoints is:\n', yCoordPoints[i-3:i+4]
            raise TypeError, 'Warning, something wrong with this yCoord data.'
    out['xCoordPoints'] = xCoordPoints
    out['yCoordPoints'] = yCoordPoints
    out['inCoordPoints'] = inCoordPoints
    return out

def mathematica_TXT_dealer(path=r'C:\Users\aweff\Documents\coord.txt',):
    f = open(path,'r')
    coordlst = mylst()
    for line in f:
        line = line.replace('{{','(')
        line = line.replace('}}',')')
        line = line.replace('{','(')
        line = line.replace('}',')')
        exec('lst = mylst(('+line+'))')
        coordlst.append(lst)
    f.close()
    return coordlst

def abaqusInputDataGenerator(outPath=r'C:\Users\aweff\Documents\03.python\pycharm_projects\modelPoints.txt',\
                             vector=(0.0,0.0,0.2), log='', **kwargs):
    f = open(outPath,'w')
    xBoundPoints =  kwargs['xCoordPoints']
    yBoundPoints =  kwargs['yCoordPoints']
    InnerPoints = kwargs['inCoordPoints']
    xBoundPoints_3D = xBoundPoints.threeD()
    yBoundPoints_3D = yBoundPoints.threeD()
    InnerPoints_3D = InnerPoints.threeD()
    f.writelines('# log: %s \n' %log)
    f.writelines('xBoundPoints = '+str(xBoundPoints)+'\n',)
    f.writelines('yBoundPoints = '+str(yBoundPoints)+'\n',)
    f.writelines('InnerPoints = '+str(InnerPoints)+'\n',)
    f.writelines('xBoundPoints_3D = '+str(xBoundPoints_3D)+'\n',)
    f.writelines('yBoundPoints_3D = '+str(yBoundPoints_3D)+'\n',)
    f.writelines('InnerPoints_3D = '+str(InnerPoints_3D)+'\n',)
    f.writelines('vect = '+str(vector)+'\n',)
    f.close()
    print 'abaqusInputDataGenerator successfully complete!'

def abaqusInputDataGenerator_shelveVersion(outPath, 
										   vector=(0.0, 0.0, 0.0), 
										   time='Unknown', **kwargs):	
	f = shelve.open(outPath)
	f["time"] = time
	f["vector"] = vector
	for key, val in kwargs.iteritems():
		f[key] = list(val)
		f[key+"_3D"] = list(val.threeD())
	f.close()
	print "shelveVersion Complete!"

if __name__ == '__main__':
#    testcase1.py
    testlst = [(0.0,0.0),(6.75,7.5),(12.5,12.5),(25.0,12.2),(37.5,15.0),(42.5, 9.0), (50.0,0)]
    result = coord_generator(testlst)
    print result.keys()
    plt.figure()
    plt.scatter(result['xCoordPoints'].getx(),result['xCoordPoints'].gety())
    plt.scatter(result['yCoordPoints'].getx(),result['yCoordPoints'].gety(),color='red')
    plt.show()
    pprint(result['xCoordPoints'])

def result_visualize(result):
    if result.has_key("inCoordPoints") and result.has_key("xCoordPoints") and result.has_key("yCoordPoints"):
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
    else:
        raise Exception, "Wrong input result data!"