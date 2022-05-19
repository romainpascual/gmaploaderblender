# Chargeur via le protocole Rest de Jerboa pour les objets dans Blender

import requests
import bpy
import json
import math
import time

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

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
        
def cylinder_between(x, y, r):
    # 1 == x
    # 2 == y
    
    d = [(yi-xi) for xi,yi in zip(x,y)]
    dist = math.sqrt(sum(di**2 for di in d))
    
    if dist == 0:
        return
    
    mid = tuple((xi+yi)/2 for xi,yi in zip(x,y))

    bpy.ops.mesh.primitive_cylinder_add(
        radius = r, 
        depth = dist,
        location = mid,
        # vertices=8,
    ) 

    phi = math.atan2(d[1], d[0]) 
    theta = math.acos(d[2]/dist) 
    bpy.context.object.rotation_euler[1] = theta 
    bpy.context.object.rotation_euler[2] = phi 


def change_focus_collection(collection_name):
    def recurLayerCollection(layerColl, collName):
        found = None
        if (layerColl.name == collName):
            return layerColl
        for layer in layerColl.children:
            found = recurLayerCollection(layer, collName)
            if found:
                return found

    master_coll = bpy.context.view_layer.layer_collection
    target_coll_name = collection_name
    target_coll = recurLayerCollection(master_coll, target_coll_name)

    if target_coll:
        bpy.context.view_layer.active_layer_collection = target_coll
        return True
    else:
    
        target_coll = bpy.data.collections.new(target_coll_name)
        bpy.context.scene.collection.children.link(target_coll)
        target_coll = recurLayerCollection(master_coll, target_coll_name)
        bpy.context.view_layer.active_layer_collection = target_coll
        return False
    
    
def parse_gmap(darts,dim):
    DART_radius=0.01
    arcs=[[] for _ in range(dim+1)]
    id_to_pos = dict()
    
    # Create 'Dart' collection
    change_focus_collection("Darts")
    
    dart_parsing = time.perf_counter()
    sphere_creation = 0
    
    for dart in darts:
        
        # extract information
        vertex_position = dart['position']
        dart_position = (
            dart['normal']['x'],
            dart['normal']['y'],
            dart['normal']['z'],
            )
        alphas = dart['alphas']
        
        # store position
        dart_id = dart['id']
        id_to_pos[dart_id]=dart_position
        
        sphere_time=time.perf_counter()  
        # make sphere
        bpy.ops.mesh.primitive_uv_sphere_add(
            location=dart_position,
            radius=DART_radius,
            # segments = 8,
            # ring_count = 6,
            )
        sphere_creation += time.perf_counter() - sphere_time
        
        # fix dart Name
        bpy.data.objects["Sphere"].name = "Dart"+str(dart["id"])
        
        # extract arcs
        alphas = dart['alphas']
        for d in range(dim+1):
            neighbor = alphas[d]
            if neighbor < dart_id:
                arcs[d].append((dart_id,neighbor))
                
    print("dart parsing time:",time.perf_counter()-dart_parsing)
    print("sphere creation time:",sphere_creation)
    
    arc_parsing = time.perf_counter()
    
    for d in range(dim+1):
        
        # Create 'Alpha' collection
        change_focus_collection("Alpha"+str(d))
        
        for arc in arcs[d]:
            
            # Recover endpoints
            source = id_to_pos[arc[0]]
            target = id_to_pos[arc[1]]
            arc_radius = DART_radius/2
            
            # make cylinder
            cylinder_between(source,target,arc_radius)
            
            # fix name
            bpy.data.objects["Cylinder"].name = str(arc[0]) +  "to" +  str(arc[1])
    
    print("arc parsing time:",time.perf_counter()-arc_parsing)
        
def main():
    try:
        start_loading = time.perf_counter()
        body = requests.get('http://localhost:8080/modeler')
        darts = (body.json())['result']['gmaps'][0]['dartArray']
        dim = (body.json())['result']['dimension']
        print("loading time:",time.perf_counter()-start_loading)         
        parse_gmap(darts,dim)
            
    except:
        ShowMessageBox("Erreur during load of Jerboa inside Blender","Erreur", 'ERROR')
        
def test():
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments = 8,
        ring_count = 6,
        location=(-1,-1,-1),
        radius=0.1,
        )
    
if __name__== "__main__":
    main()