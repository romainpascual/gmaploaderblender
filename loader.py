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


def ShowMessageBox(Smessage = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
    
##  ==================================================================================

def hakim():
    DART_radius=0.01

    try:
        body = requests.get('http://localhost:8080/modeler')
        darts = (body.json())['result']['gmaps'][0]['dartArray']
        print("Found ", len(darts))
        for dart in darts:
            position = dart['position']
            eclated = dart['normal']
            # https://docs.blender.org/api/current/bpy.ops.mesh.html
            bpy.ops.mesh.primitive_uv_sphere_add(location=(dart['normal']['x'], dart['normal']['y'], dart['normal']['z']), radius=DART_radius)
            
            
    except:
        ShowMessageBox("Erreur during load of Jerboa inside Blender","Erreur", 'ERROR')
        

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

    for k in range(nNodes):
    
        degree=k*degreeSlice
        Xpos=radious*np.cos(degree)
        Ypos=radious*np.sin(degree)
        bpy.ops.mesh.primitive_uv_sphere_add(location=(Xpos,Ypos,0))
        bpy.data.objects[NodesNames[k]].scale=(0.05,0.05,0.05)
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

    for k in range(numberOfEdges):
    
        nodeA=FromNumberToName[k]
        nodeB=FromNumberToName[IncidenceList[k]]

        pointA=NodesLocations[nodeA]
        pointB=NodesLocations[nodeB]

        midpoint=MidPointLocation(pointA,pointB)
        edgeLength=Distance(pointA,pointB)/2
        rotation=Rotation(pointA,pointB)
        EdgeLocations[EdgeNames[k]]=midpoint
        bpy.ops.mesh.primitive_cylinder_add(location=midpoint, scale=(0.01,0.01,edgeLength))
        # bpy.data.objects[EdgeNames[k]].scale=(0.1,edgeLength,0.01)
        bpy.data.objects[EdgeNames[k]].rotation_euler=(0,0,rotation)
    
    return EdgeNames,EdgeLocations

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