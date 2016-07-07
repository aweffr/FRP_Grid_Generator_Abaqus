# -*- coding: utf-8 -*-
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
import shelve
from numpy import *
from operator import itemgetter

def setMaker(coordData, targetInstance, setName='default'):
    # 定义点集合，输入格式为： 点坐标集合， 目标实体， 输出set名称
    setForAbaqus = []
    for tup in coordData:
    # 此处大坑，findAt((tup,),) 这个格式的原因待考证
        setForAbaqus.append(
            targetInstance.vertices.findAt((tup,),)
            )
    return myAssembly.Set(name=setName, vertices=setForAbaqus)


# -----------------------脚本初始化----------------------
rangeOfModel = 80.0


modelFile = shelve.open("D:\\abaqus_execpy\\TrueModel\\data\\modelPoints-Current.dat")
time = modelFile["time"]
modelFile.close()

saveFileName = 'addPartC-Closer-Multi3-%d.cae'%time

myModel = mdb.models['Model A']
myAssembly = myModel.rootAssembly

set_PartA_Bound = myAssembly.sets['PartA_Boundary']
set_PartB_Bound = myAssembly.sets['PartB_Boundary']

# ---------------------脚本初始化完毕----------------------------


# ---------------------创建PartC---------------------------------
myPartC = myModel.Part(dimensionality=THREE_D, name='Part C', type=DEFORMABLE_BODY)
s = shelve.open('thirdBeam-%d.dat'%time)
pointDict = s['pointDict']
pointForSetMaker = []
for key, mat in s.items():
    mat = array(sorted(mat, key=itemgetter(0),),)
    mat = mat[0::2,3:]
    tempPointList = []
    for point in mat:
        pointForSetMaker.append(tuple(point),)
        tempPointList.append(tuple(point),)
    myPartC.WirePolyLine(mergeWire=OFF, meshable=ON, points=tempPointList)

# 引入PartC进assembly
Instance_A = myAssembly.instances['PartA']
Instance_B = myAssembly.instances['PartB']
Instance_C = myAssembly.Instance(dependent=ON, name='PartC', part=myPartC)
set_PartC_Points = setMaker(pointForSetMaker, Instance_C, 'PartC_Hingle')

# 连线，line
for key, mat in s.items():
    mat = array(sorted(mat, key=itemgetter(0),),)
    mat = mat[0::2]
    for coord in mat:
        planeCoord = coord[0:3]
        spaceCoord = coord[3:]
        vertix1 = Instance_B.vertices.findAt((planeCoord),)
        vertix2 = Instance_C.vertices.findAt((spaceCoord),)
        myAssembly.WirePolyLine(mergeWire=OFF, meshable=OFF, 
            points=((vertix1, vertix2), )
            )
connector = myModel.ConnectorSection(name='LockU1U2U3', translationalType=JOIN)
setWholePartC = myAssembly.Set(
    edges=Instance_C.edges.getByBoundingBox(
        xMin=-rangeOfModel,xMax=rangeOfModel,
        yMin=-rangeOfModel,yMax=rangeOfModel,
        zMin=-rangeOfModel,zMax=rangeOfModel,),
    name='Set-wholePartC',)
setForConnector = myAssembly.Set(
    edges=myAssembly.edges.getByBoundingBox(
        xMin=-rangeOfModel,xMax=rangeOfModel,
        yMin=-rangeOfModel,yMax=rangeOfModel,
        zMin=-rangeOfModel,zMax=rangeOfModel,),
    name='Set-connectWire',)
myAssembly.SectionAssignment(
    region=setForConnector, 
    sectionName='LockU1U2U3',
    )
myAssembly.regenerate()

# ---------------------------Part3及连接件创建结束-----------------------

# 创建后续分析步
mdb.models['Model A'].StaticStep(name='Step-2', previous='Step-1', minInc = 0.000000025, initialInc=0.0000025, maxNumInc=50000000)
mdb.models['Model A'].StaticStep(name='Step-3', previous='Step-2', minInc = 0.000000025, initialInc=0.0000025, maxNumInc=50000000)

# ModelChange
modelChange1 = myModel.ModelChange(
    activeInStep=False, 
    createStepName='Step-1', 
    includeStrain=False, 
    name='Int-1', 
    region=setForConnector)
modelChange2 = myModel.ModelChange(
    activeInStep=False, 
    createStepName='Step-1', 
    includeStrain=False, 
    name='Int-2', 
    region=setWholePartC)
modelChange1.setValuesInStep(activeInStep=True, stepName='Step-2')
modelChange2.setValuesInStep(activeInStep=True, stepName='Step-2')

# 后续边界条件修改
myModel.DisplacementBC(
    amplitude=UNSET, 
    createStepName='Step-2', 
    distributionType=UNIFORM, 
    fieldName='', fixed=ON, 
    localCsys=None, 
    name='BC-Hold-A', 
    region=set_PartA_Bound,
    u1=SET, u2=SET, u3=SET, 
    ur1=UNSET, ur2=UNSET, ur3=UNSET)
myModel.DisplacementBC(
    amplitude=UNSET, 
    createStepName='Step-2', 
    distributionType=UNIFORM, 
    fieldName='', fixed=ON, 
    localCsys=None, 
    name='BC-Hold-B', 
    region=set_PartB_Bound,
    u1=SET, u2=SET, u3=SET, 
    ur1=UNSET, ur2=UNSET, ur3=UNSET)
myModel.boundaryConditions['BC-Left'].deactivate('Step-3')
myModel.boundaryConditions['BC-Right'].deactivate('Step-3')
mdb.saveAs(pathName=saveFileName)