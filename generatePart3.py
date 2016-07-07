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
    # 本函数用于查找所有实体上该坐标列表的端点，并将其生成一个组
    # 本函数仅用于vertices
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
s = shelve.open("D:\\abaqus_execpy\\TrueModel\\data\\thirdBeam-%d.dat"%time)
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

pointDict = s['pointDict']
pointForSetMaker = []
for key, arraylst in pointDict.iteritems():
    tempPointList = []
    for point in arraylst:
        point = point[3:]
        pointForSetMaker.append(tuple(point),)
        tempPointList.append(tuple(point),)
    myPartC.WirePolyLine(mergeWire=OFF, meshable=ON, points=tempPointList)

# 引入PartC进assembly
Instance_A = myAssembly.instances['PartA']
Instance_B = myAssembly.instances['PartB']
Instance_C = myAssembly.Instance(dependent=ON, name='PartC', part=myPartC)
set_PartC_Points = setMaker(pointForSetMaker, Instance_C, 'PartC_Hingle')

# 连线，line
for key, arraylst in pointDict.iteritems():
    for point in arraylst:
        planeCoord = coord[:3]
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

# part3 连接件的集合的选中方式为，空间内所有连线全选，减去load产生的set.
# 全选
setForConnector = myAssembly.Set(
    edges=myAssembly.edges.getByBoundingBox(
        xMin=-rangeOfModel,xMax=rangeOfModel,
        yMin=-rangeOfModel,yMax=rangeOfModel,
        zMin=-rangeOfModel,zMax=rangeOfModel,),
    name='Set-connectWire',)
# 考虑单个其吊点的情况，这种情况不需要作差集。
if myAssembly.sets.has_key("MPCwires"):
    setForMPCwires = myAssembly.sets["MPCwires"]
    # 此处做集合的差集。
    setForConnector = myAssembly.SetByBoolean(
        name='Set-connectWire',
        sets=[setForConnector, setForMPCwires],
        operation=DIFFERENCE,
        )
    myAssembly.SectionAssignment(
        region=setForConnector, 
        sectionName='LockU1U2U3',
        )
myAssembly.regenerate()

# ---------------------------Part3及连接件创建结束-----------------------

# 创建后续分析步
step2 = myModel.StaticStep(name='Step-2', previous='Step-1', minInc = 0.000000025, initialInc=0.0000025, maxNumInc=50000000)
step3 = myModel.StaticStep(name='Step-3', previous='Step-2', minInc = 0.000000025, initialInc=0.0000025, maxNumInc=50000000)

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