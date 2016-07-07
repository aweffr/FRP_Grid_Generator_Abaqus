# -*- coding:utf-8 -*-
# odbProcessor.py
# 本脚本用于得到边界点和内部点的后处理（位移）数据。
# 对于边界点，数据格式为np.array(), (original, original, deformed)
# 对于内部点，数序格式为np.array(), (deformed, deformed, deformed)

import shelve
from odbAccess import *
from numpy import array, array2string, std, zeros


def isSamePoint(point1, point2, err=0.0002):
    # 输入两个点，判断两个点平面上是不是同一个点
    if abs(point1[0] - point2[0]) < err and abs(point1[1] - point2[1]) < err:
        return True
    else:
        return False

def isInnerPoints(point, innerPointLst, err=0.0002):
    # point -> 判断改点算不算内部点
    # innerPointLst -> 模型文件中内部点的坐标


    modelNodeFile.close()

def odbNodeDeformation(odbPath = 'D:/My Docs/AbaqusTemp/FRPGrid-.odb',
    outFilePath=r'D:\abaqus_execpy\outdata\coord.txt',
    modelFilePath=''):
    # odbPath -> abaqus目标后处理数据库odb的文件位置
    # outPath -> 将读取的结果输入到的shelve的位置
    # modelFilePath -> 模型变形前坐标
    odb = openOdb(path=odbPath)

    # 初始化模型坐标中的数据
    modelNodeFile = shelve.open(modelFilePath)
    xBoundPoints = modelNodeFile['xCoordPoints']
    yBoundPoints = modelNodeFile['yCoordPoints']
    InnerPoints = modelNodeFile['inCoordPoints']

    # abaqus中的API模块，提取最终变形的data.
    finalFrame = odb.steps['Step-1'].frames[-1]
    print 'finalFrame Get!'
    
    outFile = shelve.open(outFilePath)

    innerPoints_Deformed = []
    boundPoints_Deformed = []

    for value in finalFrame.fieldOutputs['U'].values:
        # 当模型中存在connector时该instance为None,需要跳过
        if value.instance == None:
            continue
        nodeLabel = value.nodeLabel
        checkLabel = value.instance.nodes[value.nodeLabel-1].label
        if nodeLabel == checkLabel:
            deformationVector = array(value.data)
            orignalCoordinate = array(value.instance.nodes[value.nodeLabel-1].coordinates)
            # 此处判断该点是否为边界点
            if isInnerPoints(orignalCoordinate, InnerPoints):
                tempArray = zeros(6, float)
                tempArray[:3] = orignalCoordinate
                tempArray[4:] = deformationVector
                innerPoints_Deformed.append(tempArray)
            else:
                orignalCoordinate[-1] = deformationVector[-1]
                # orignalCoordinate的数据结构变成（x,y,z），x,y为平面上坐标的点，z为位移的变化量
                boundPoints_Deformed.append(orignalCoordinate)
        else:
            print 'Wrong point, Label is %d'%nodeLabel

    outFile['Bound_Points'] = boundPoints_Deformed
    outFile['Inner_Points'] = innerPoints_Deformed
    print 'Odb data classfication Complete!'
    outFile.close()

def NodesFilter(shelveFileLocation, modelFilePath, outFilePath, accuracy = 0.001):
    pointInfo = shelve.open(shelveFileLocation)
    modelNodeFile = shelve.open(modelFilePath)
    outFile = shelve.open(outFilePath)

    if pointInfo.has_key("out_points"):
        out_points = pointInfo["out_points"]
        print "Raw data received! len(data) = %d"%(len(out_points))
    else:
        raise Exception, "Check the shelve file which contains the raw points info."

    xBoundPoints = modelNodeFile['xCoordPoints']
    yBoundPoints = modelNodeFile['yCoordPoints']
    InnerPoints = modelNodeFile['inCoordPoints']

    allBoundPoints = xBoundPoints + yBoundPoints

    # Init two lsts for output shelve.
    tempBound = []
    tempInner = []

    for point in out_points:
        isBoundPoints = False
        for origin_point in allBoundPoints:
            if abs(point[0]-origin_point[0]) < accuracy and abs(point[1]-origin_point[1]) < accuracy:
                tempBound.append(point)
                isBoundPoints = True
                break
        if not isBoundPoints:
            tempInner.append(point)        
    outFile['Bound_Points'] = tempBound
    outFile['Inner_Points'] = tempInner
    modelNodeFile.close()
    pointInfo.close()
    outFile.close()
    print "Raw data processing complete!"
    print "File is saved at %s"%outFilePath

    # To compute the standard error of z direction deformation.
    temp_z = []
    for point in tempBound:
    	temp_z.append(point[2])
    stderr = std(temp_z)
    print "The std err is %.3f"%stderr

if __name__ == '__main__':
    file = shelve.open("D:\\abaqus_execpy\\TrueModel\\data\\modelPoints-Current.dat")
    time = file["time"]
    
    # Copy the current file and rename it by its iter-time.
    fileToCopy = shelve.open("D:\\abaqus_execpy\\TrueModel\\data\\modelPoints-Closer-Multi3-%d.dat"%time)
    for key, value in file.iteritems():
        fileToCopy[key] = value
    file.close()
    fileToCopy.close()
    
    modelPoints = "modelPoints-Closer-Multi3-%d.dat"%time
    odbFileName = "trueModel-Closer-Multi3-%d.odb"%time
    rawDeformationDataName = "deformation-Closer-Multi3-%d.dat"%time
    washedDataName = "washedPoints-Closer-Multi3-%d.dat"%time

    odbNodeDeformation(odbPath='D:/abaqus_execpy/TrueModel/abaqusData/%s'%odbFileName,
        outPath='D:\\abaqus_execpy\\TrueModel\\data\\%s'%rawDeformationDataName)
    NodesFilter(shelveFileLocation='D:\\abaqus_execpy\\TrueModel\\data\\%s'%rawDeformationDataName,
        modelFilePath='D:\\abaqus_execpy\\TrueModel\\data\\%s'%modelPoints,
        outFilePath='D:\\abaqus_execpy\\TrueModel\\data\\%s'%washedDataName)