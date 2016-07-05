# -*- coding:utf-8 -*-
# fileName: odbProcessor-II.py
import shelve
from odbAccess import *
from numpy import array, array2string
def odbNodeDeformation(odbPath = 'D:/My Docs/AbaqusTemp/FRPGrid-.odb',outPath = r'D:\abaqus_execpy\outdata\coord.txt'):
    # odbPath -> abaqus目标后处理数据库odb的文件位置
    # outPath -> 将读取的结果输入到的shelve的位置
    odb = openOdb(path=odbPath)
    finalFrame = odb.steps['Step-1'].frames[-1]
    f = shelve.open(outPath)
    out_points = []
    print 'finalFrame Get!'
    for value in finalFrame.fieldOutputs['U'].values:
        # print 'Working in loop!'
        nodeLabel = value.nodeLabel
        checkLabel = value.instance.nodes[value.nodeLabel-1].label
        if nodeLabel == checkLabel:
            deformationVector = array(value.data)
            orignalCoordinate = array(value.instance.nodes[value.nodeLabel-1].coordinates)
            orignalCoordinate[-1] = deformationVector[-1]
            # orignalCoordinate的数据结构变成（x,y,z），x,y为平面上坐标的点，z为位移的变化量
            out_points.append(orignalCoordinate)
        else:
            print 'Wrong point, Label is %d'%nodeLabel
    f["out_points"] = out_points
    print 'Raw Data Getter Complete!'
    f.close()

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

if __name__ == '__main__':
	time = 2
    modelPoints = "modelPoints-%d.dat"%time
    odbFileName = "trueModel-%d.odb"%time
    rawDeformationDataName = "deformation-%d.dat"%time
    washedDataName = "washedPoints-%d.dat"%time

    odbNodeDeformation(odbPath='D:/abaqus_execpy/TrueModel/abaqusData/%s'%odbFileName,
        outPath='D:\\abaqus_execpy\\TrueModel\\data\\%s'%rawDeformationDataName)
    NodesFilter(shelveFileLocation='D:\\abaqus_execpy\\TrueModel\\data\\%s'%rawDeformationDataName,
        modelFilePath='D:\\abaqus_execpy\\TrueModel\\data\\%s'%modelPoints,
        outFilePath='D:\\abaqus_execpy\\TrueModel\\data\\%s'%washedDataName)