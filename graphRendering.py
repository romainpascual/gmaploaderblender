# Chargeur via le protocole Rest de Jerboa pour les objets dans Blender
"""
MIT License
Copyright (c) 2020 Octavio Gonzalez-Lugo 
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import requests
import bpy
import json

import numpy as np
 

#Generates a list with the names of the objects
def MakeObjectNames(ObjectName,NumberOfObjects):
    """
    ObjectName -> Base name of the object created
    NumberOfObjects -> Number of objects to be created
    """
    NamesContainer=[]
    NamesContainer.append(ObjectName)

    for k in range(1,NumberOfObjects):
        if k<=9:
            NamesContainer.append(ObjectName+".00"+str(k))
        elif k>9 and k<=99:
            NamesContainer.append(ObjectName+".0"+str(k))
        elif k>99 and k<=999:
            NamesContainer.append(ObjectName+"."+str(k))

    return NamesContainer

#Wrapper function to create a list of shpere object names
def MakeNodesNames(NumberOfElements):
    return MakeObjectNames("Sphere",NumberOfElements)

#Wrapper function to create a list of cube object names
def MakeEdgeNames(NumberOfElements):
    return MakeObjectNames("Cylinder",NumberOfElements)

#Calculates the distance between two points
def Distance(PointA,PointB):
    return np.sqrt(sum([(val-sal)**2 for val,sal in zip(PointA,PointB)]))

#Calculates the midpoint between two points
def MidPointLocation(PointA,PointB):
    return tuple([(val+sal)/2 for val,sal in zip(PointA,PointB)])

def Rotation(PointA,PointB):
    return np.arctan((PointA[1]-PointB[1])/(PointA[0]-PointB[0]))-(np.pi/2)


def MakeCircularLayout(nNodes,radious):
    """
    Add the nodes geometries for the graph circular layout
    
    nNodes  -> Number of nodes in the graph
    radious -> Radious of the circle in the circular layout
    """
    NodesNames=MakeNodesNames(nNodes)
    NodeNameToPosition={}
    degreeSlice=(2*np.pi)/nNodes
    
    node_material = getMaterial(
        material_name="NodeMaterial",
        material_default_color=(0.25, 0.25, 0.25, 1),
        )

    for k in range(nNodes):
    
        degree=k*degreeSlice
        Xpos=radious*np.cos(degree)
        Ypos=radious*np.sin(degree)
        bpy.ops.mesh.primitive_uv_sphere_add(location=(Xpos,Ypos,0))
        bpy.data.objects[NodesNames[k]].scale=(0.01,0.01,0.01)
        bpy.context.active_object.data.materials.append(node_material)        
        NodeNameToPosition[NodesNames[k]]=(Xpos,Ypos,0)

    return NodesNames,NodeNameToPosition

def AddEdgesFromIncidenceList(IncidenceList,NodesNames,NodesLocations):
    """
    Add the edge geometries for the graph
    
    IncidenceList   -> Dictionary with the nodes that shared an edge 
    NodesNames      -> List with the name of the nodes 
    NodesLocations  -> Dictionary that contains the location of the nodes 
    """
    
    numberOfNodes=len(NodesNames)
    numberOfEdges=len(IncidenceList)
    
    print(IncidenceList)
    
    FromNumberToName={}
    for k in range(numberOfNodes):
        FromNumberToName[k]=NodesNames[k]

    EdgeNames=MakeEdgeNames(numberOfEdges)
    EdgeLocations={}
    
    alpha0_material = getMaterial(
        material_name="Alpha0",
        material_default_color=(0, 0, 0, 1),
    )
        
    alpha1_material = getMaterial(
        material_name="Alpha1",
        material_default_color=(1, 0, 0, 1),
    )
        
    alpha2_material = getMaterial(
        material_name="Alpha2",
        material_default_color=(0, 0, 1, 1),
    )
        
    alpha3_material = getMaterial(
        material_name="Alpha3",
        material_default_color=(0, 0.8, 0, 1),
    )
        
    edgemat = [
        alpha0_material,
        alpha1_material,
        alpha2_material,
        alpha3_material,
    ]

    for k in range(numberOfEdges):
    
        nodeA=FromNumberToName[k]
        nodeB=FromNumberToName[IncidenceList[k]]

        pointA=NodesLocations[nodeA]
        pointB=NodesLocations[nodeB]

        midpoint=MidPointLocation(pointA,pointB)
        edgeLength=Distance(pointA,pointB)/2
        rotation=Rotation(pointA,pointB)
        EdgeLocations[EdgeNames[k]]=midpoint
        bpy.ops.mesh.primitive_cylinder_add(location=midpoint, scale=(0.005,0.005,edgeLength))
        # bpy.data.objects[EdgeNames[k]].scale=(0.1,edgeLength,0.01)
        bpy.data.objects[EdgeNames[k]].rotation_euler=(0,0,rotation)
        bpy.context.active_object.data.materials.append(
            edgemat[k%4]
            ) 
    
    return EdgeNames,EdgeLocations

def getMaterial(material_name, material_default_color=(0.125, 0.125, 0.125, 1)):
    material = bpy.data.materials.get(material_name)
    
    if material is None:
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        pnode = material.node_tree.nodes.get("Principled BSDF")
        
        pnode.inputs[0].default_value = material_default_color
    
    return material
    

def makeGraph():
	nNodes=5
	edgeList={}

	for k in range(nNodes):
		cvector=[j for j in range(nNodes) if j!=k]
		edgeList[k]=int(np.random.choice(cvector))

	NodesNames,NodesLocations = MakeCircularLayout(nNodes,1)
	EdgeNames,EdgeLocations=AddEdgesFromIncidenceList(edgeList,NodesNames,NodesLocations)

if __name__== "__main__":
    makeGraph()
    newMaterial("nodes")