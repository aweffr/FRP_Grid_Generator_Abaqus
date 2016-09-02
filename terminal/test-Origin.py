# -*- coding: utf-8 -*-
# log:
# 修改载入坐标文件的名称
# 修改输出保存模型文件的名称
# 修改Job文件的名称
# 修改step的类型
# 修改荷载的起吊点
# 
# 2016.6.29修改log:
# 将 times, caeName等集成到代码开头
# 用shelve模块替代原来的txt保存方式

from part import *
from material import *
from section import *
from optimization import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
import math
import shelve
# import handytools

f = shelve.open(r'D:\abaqus_execpy\TrueModel\data\modelPoints.dat')

# 保存的文件名，提交的计算作业名
# 起吊点高度
times = 1
caeName = 'trueMpdel-%d'%times
jobName = 'trueModel-%d'%times
leftHeight = 8.0
rightHeight = 12.0

xBoundPoints =  f['xCoordPoints']
yBoundPoints =  f['yCoordPoints']
InnerPoints = f['inCoordPoints']
xBoundPoints_3D = f['xCoordPoints_3D']
yBoundPoints_3D = f['yCoordPoints_3D']
InnerPoints_3D = f['inCoordPoints_3D']
vect = f['vector']
f.close()

# 创建模型，命名为Model A
myModel = mdb.Model(name='Model A')

# 创建草图图形，命名为Model A，令mySketchA作为对象入口
mySketchA = myModel.ConstrainedSketch(name='Sketch A', sheetSize=200.0)

# 连接由X轴的坐标控制的点，读取lst1中的坐标
for i in range(0,len(xBoundPoints),2):
    mySketchA.Line(point1=xBoundPoints[i], point2=xBoundPoints[i+1])

# 创建草图图形，命名为Model B，令mySketchB作为对象入口
mySketchB = myModel.ConstrainedSketch(name='Sketch B', sheetSize=200.0)

# 连接由Y轴的坐标控制的点，读取lst2中的坐标
for i in range(0,len(yBoundPoints),2):
    mySketchB.Line(point1=yBoundPoints[i], point2=yBoundPoints[i+1])


# 创建PartA和PartB, PartA对应lst1, PartB对应lst2
myPartA = myModel.Part(name='Part A', dimensionality=THREE_D, type=DEFORMABLE_BODY)
myPartA.BaseWire(sketch=mySketchA)
myPartB = myModel.Part(name='Part B', dimensionality=THREE_D, type=DEFORMABLE_BODY)
myPartB.BaseWire(sketch=mySketchB)

# 创建分割点
for coord in InnerPoints_3D:
    if myPartA.edges.findAt(coord,) != None:
        try:
            myPartA.PartitionEdgeByPoint(edge = myPartA.edges.findAt(coord,), point=coord)
        except Exception as e:
            print e,'Wrong Point at:',coord,'when Partiting A'
    if myPartB.edges.findAt(coord,) != None:
        try:
            myPartB.PartitionEdgeByPoint(edge = myPartB.edges.findAt(coord,), point=coord)
        except Exception as e:
            print e,'Wrong Point at:',coord,'when Partiting B'


# 模型空间组装 Assembly
myAssembly = mdb.models['Model A'].rootAssembly

# 定义全局坐标为直角坐标系
myAssembly.DatumCsysByDefault(CARTESIAN)

# 引入PartA和PartB
Instance_A = myAssembly.Instance(dependent=ON, name='PartA', part = myPartA)
Instance_B = myAssembly.Instance(dependent=ON, name='PartB', part = myPartB)

# for coord in gravityCentre:
#     myAssembly.DatumPointByCoordinate(coords=coord)

def setMaker(coordData, targetInstance, setName='default'):
    # 定义点集合，输入格式为： 点坐标集合， 目标实体， 输出set名称
    setForAbaqus = []
    for tup in coordData:
    # 此处大坑，findAt((tup,),) 这个格式的原因待考证
        setForAbaqus.append(
            targetInstance.vertices.findAt((tup,),)
            )
    return myAssembly.Set(name = setName, vertices = setForAbaqus)

set_PartA_InnerPoints = setMaker(InnerPoints_3D, Instance_A, 'PartA_Inner')
set_PartB_InnerPoints = setMaker(InnerPoints_3D, Instance_B, 'PartB_Inner')
set_PartA_BoundaryPoints = setMaker(xBoundPoints_3D, Instance_A, 'PartA_Boundary')
set_PartB_BoundaryPoints = setMaker(yBoundPoints_3D, Instance_B, 'PartB_Boundary')

# 沿向量vect平移PartA，用于考虑连接件长度
# myAssembly.translate(instanceList=('PartA',), vector=vect)

# 创建连接件的耦合单元
myModel.Coupling(controlPoint=set_PartB_InnerPoints,
                 couplingType=KINEMATIC, 
                 influenceRadius=0.05,
                 localCsys=None,
                 name='Coup', 
                 surface=set_PartA_InnerPoints, 
                 u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=OFF)

# 赋予材料属性及截面
myMaterial = myModel.Material(name='FRP')
myMaterial.Elastic(table=((46000000000.0, 0.28), ))
myMaterial.Density(table=((1500.0, ), ))
myModel.PipeProfile(name='P1', r=0.05/2, t=0.002)
myModel.BeamSection(consistentMassMatrix=False, 
                    integration=DURING_ANALYSIS,
                    material='FRP',
                    name='Pipe',
                    poissonRatio=0.0,
                    profile='P1',
                    temperatureVar=LINEAR)

# 将截面赋予到Part上
partSetB = myPartB.Set(
    edges=myPartB.edges.getByBoundingBox(xMin=-60.0,xMax=60.0,yMin=-60.0,yMax=60.0,zMin=-60.0,zMax=60.0), 
    name='PartB')

myPartB.SectionAssignment(
    offset=0.0,
    offsetField='',
    offsetType=MIDDLE_SURFACE,
    region=partSetB,
    sectionName='Pipe', 
    thicknessAssignment=FROM_SECTION)

myPartB.assignBeamSectionOrientation(
    method=N1_COSINES, 
    n1=(0.0, 0.0, -1.0), 
    region=partSetB)

partSetA= myPartA.Set(
    edges=myPartA.edges.getByBoundingBox(xMin=-60.0,xMax=60.0,yMin=-60.0,yMax=60.0,zMin=-60.0,zMax=60.0), 
    name='PartA')

myPartA.SectionAssignment(
    offset=0.0, 
    offsetField='', 
    offsetType=MIDDLE_SURFACE, 
    region=partSetA, 
    sectionName='Pipe', 
    thicknessAssignment=FROM_SECTION)

myPartA.assignBeamSectionOrientation(
    method=N1_COSINES, 
    n1=(0.0, 0.0, -1.0), 
    region=partSetA)

# Meshing
myPartA.seedPart(deviationFactor=0.1, minSizeFactor=0.1, size=0.25)
myPartA.generateMesh()

myPartB.seedPart(deviationFactor=0.1, minSizeFactor=0.1, size=0.25)
myPartB.generateMesh()

# Step,Load
Step_1 = myModel.StaticStep(initialInc=0.5, maxNumInc=1000, name='Step-1',previous='Initial')
Step_1.setValues(initialInc=0.00025, maxInc=0.2, maxNumInc=500000, minInc=1e-10, nlgeom=ON, \
                 solutionTechnique=FULL_NEWTON,)

set_Whole = myAssembly.Set(
    edges=Instance_A.edges.getByBoundingBox(xMin=-60.0,xMax=60.0,yMin=-60.0,yMax=60.0,zMin=-60.0,zMax=60.0)+\
    Instance_B.edges.getByBoundingBox(xMin=-60.0,xMax=60.0,yMin=-60.0,yMax=60.0,zMin=-60.0,zMax=60.0), 
    name='Whole')
myModel.Gravity(
    comp3=-9.8,
    createStepName='Step-1', 
    name='Gravity',
    distributionType=UNIFORM,
    field='')


set_loadLeft = myAssembly.Set(
    name='Set-loadLeft', 
    vertices=Instance_B.vertices.getByBoundingBox(xMin=14.9,xMax=15.1,yMin=-0.1,yMax=0.1,zMin=-0.1,zMax=0.1)
    )
set_loadRight = myAssembly.Set(
    name='Set-loadRight', 
    vertices=Instance_B.vertices.getByBoundingBox(xMin=41.9,xMax=42.1,yMin=-0.1,yMax=0.1,zMin=-0.1,zMax=0.1)
    )
set_loadMiddle = myAssembly.Set(
    name='Set-loadMiddle', 
    vertices=Instance_B.vertices.getByBoundingBox(xMin=29.9,xMax=30.1,yMin=-0.1,yMax=0.1,zMin=-0.1,zMax=0.1)
    )
set_symBoundCondition = myAssembly.Set(
    name='Set-symBoundCondition',
    vertices=Instance_B.vertices.getByBoundingBox(xMin=0.0,xMax=60.0,yMin=-0.1,yMax=0.1,zMin=-0.1,zMax=0.1)
)

myModel.DisplacementBC(amplitude=UNSET,
                       createStepName='Step-1',
                       distributionType=UNIFORM,
                       fieldName='',
                       fixed=OFF,
                       localCsys=None,
                       name='set_SymBoundCondition',
                       region=set_symBoundCondition,
                       u1=UNSET, u2=0.0, u3=UNSET, ur1=0.0, ur2=UNSET, ur3=0.0)

myModel.DisplacementBC(amplitude=UNSET, 
                       createStepName='Step-1', 
                       distributionType=UNIFORM, 
                       fieldName='', 
                       fixed=OFF, 
                       localCsys=None, 
                       name='BC-Left', 
                       region=set_loadLeft, 
                       u1=UNSET, u2=0.0, u3=leftHeight, ur1=0.0, ur2=UNSET, ur3=0.0)

myModel.DisplacementBC(amplitude=UNSET, 
                       createStepName='Step-1',
                       distributionType=UNIFORM, 
                       fieldName='', 
                       fixed=OFF, 
                       localCsys=None, 
                       name='BC-Right', 
                       region=set_loadRight,
                       u1=UNSET, u2=0.0, u3=rightHeight, ur1=0.0, ur2=UNSET, ur3=0.0)

myModel.DisplacementBC(amplitude=UNSET, 
                       createStepName='Step-1',
                       distributionType=UNIFORM, 
                       fieldName='', 
                       fixed=OFF, 
                       localCsys=None, 
                       name='BC-Middle', 
                       region=set_loadMiddle,
                       u1=0.0, u2=UNSET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET)

submitJob = mdb.Job(atTime=None, 
        name=jobName,
        contactPrint=OFF, 
        description='Made by Python', 
        echoPrint=OFF, 
        explicitPrecision=SINGLE, 
        getMemoryFromAnalysis=True, 
        historyPrint=OFF, 
        memory=95, memoryUnits=PERCENTAGE, 
        model='Model A', modelPrint=OFF, 
        multiprocessingMode=DEFAULT,  
        nodalOutputPrecision=SINGLE, 
        numCpus=8, numDomains=8, numGPUs=0, queue=None, 
        scratch='', 
        type=ANALYSIS,
        userSubroutine='', 
        waitHours=0, waitMinutes=0)
submitJob.submit(consistencyChecking=OFF)
mdb.saveAs(pathName='D:/abaqus_execpy/TrueModel/abaqusData/%s'%caeName)