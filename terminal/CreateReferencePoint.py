mdb.models['Model A'].rootAssembly.ReferencePoint(point=mdb.models['Model A'].rootAssembly.instances['PartB'].vertices[422])


mdb.models['Model A'].MPCSection(mpcType=LINK_MPC, name='ConnSect-Link', 
    userMode=DOF_MODE, userType=0)
mdb.models['Model A'].rootAssembly.WirePolyLine(mergeWire=OFF, meshable=OFF, 
    points=((mdb.models['Model A'].rootAssembly.referencePoints[11], 
    mdb.models['Model A'].rootAssembly.instances['PartB'].vertices[454]), ))
mdb.models['Model A'].rootAssembly.Set(edges=
    mdb.models['Model A'].rootAssembly.edges.getSequenceFromMask(('[#1 ]', ), )
    , name='Wire-1-Set-1')
mdb.models['Model A'].rootAssembly.Set(edges=
    mdb.models['Model A'].rootAssembly.edges.getSequenceFromMask(('[#1 ]', ), )
    , name='Set-11')
mdb.models['Model A'].rootAssembly.SectionAssignment(region=
    mdb.models['Model A'].rootAssembly.sets['Set-11'], sectionName=
    'ConnSect-Link')

mdb.models['Model A'].rootAssembly.Set(edges=
    mdb.models['Model A'].rootAssembly.edges.getSequenceFromMask(('[#3 ]', ), )
    , name='Set-10')
mdb.models['Model A'].rootAssembly.Set(name='Set-12', referencePoints=(
    mdb.models['Model A'].rootAssembly.referencePoints[12], ))

myAssembly.referencePoints.findAt(coordinate=(leftHangPoint, 0.0, 2.0),)