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
        
def cube_between(x, y, r):
    return
    """
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
    """
        
def cylinder_between(x, y, r):
    
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
    
def getMaterial(material_name, material_default_color=(0.125, 0.125, 0.125, 1)):
    material = bpy.data.materials.get(material_name)
    
    if material is None:
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        pnode = material.node_tree.nodes.get("Principled BSDF")
        
        pnode.inputs[0].default_value = material_default_color
    
    return material
    
def parse_darts(darts,dim,id_to_pos,arcs, DART_radius=0.01):
    
    node_material = getMaterial(
        material_name="NodeMaterial",
        material_default_color=(0.25, 0.25, 0.25, 1),
    )

    # Create 'Dart' collection
    change_focus_collection("Darts")
    
    dart_parsing = time.perf_counter()
    sphere_creation = 0
    
    for dart in darts:
        
        print(dart['id'])
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
        
        # add material
        bpy.context.active_object.data.materials.append(node_material)
        
        # extract arcs
        alphas = dart['alphas']
        for d in range(dim+1):
            neighbor = alphas[d]
            if neighbor < dart_id:
                arcs[d].append((dart_id,neighbor))
                
    print("dart parsing time: {:.4f}s".format(time.perf_counter()-dart_parsing))
    print("sphere creation time: {:.4f}s".format(sphere_creation))
    
def parse_arcs(arcs,dim,id_to_pos, DART_radius=0.01):
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
        
    alpha_materials = [
        alpha0_material,
        alpha1_material,
        alpha2_material,
        alpha3_material,
    ]
    
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
            
            # add material
            bpy.context.active_object.data.materials.append(alpha_materials[d])
    
    print("arc parsing time: {:.4f}s".format(time.perf_counter()-arc_parsing))

def getInfo():
    try: 
        body = requests.get("http://localhost:8080/modeler/info")
        res = (body.json())['result']
        dimension = res['dimension']
        if res['nbGMaps'] > 1:
            print("More than one Gmap")
            ShowMessageBox("Error in the data received from Jerboa: more than one Gmap","Error", 'ERROR')
        if res['nbGMaps'] < 1:
            print("No Gmap")
            ShowMessageBox("Error in the data received from Jerboa: no Gmap","Error", 'ERROR')
        nbDarts = res['nbDarts'][0]
        return dimension, nbDarts
    except:
        print("Info Request Error")
        ShowMessageBox("Error when requesting info from Jerboa","Error", 'ERROR')
    
 
def main():
    dim, nbDarts = getInfo()
    id_to_pos = dict()
    arcs=[[] for _ in range(dim+1)]
    
    batch_size = 250
    
    for batch in range(math.ceil(nbDarts / batch_size)):
        start_loading = time.perf_counter()
        darts=[]
        try:
            
            body = requests.get("http://localhost:8080/modeler/gmap/0/darts/"
                + str(batch_size*batch)
                + "/"
                +  str(batch_size*(batch+1))
            )
            darts = (body.json())['result']   
            print("Parsing for batch {} suceeded".format(batch))
        except:
            print("Error")
            ShowMessageBox("Error while parsing data received from Jerboa","Error", 'ERROR')
            
        parse_darts(darts,dim,id_to_pos,arcs)
        print("parsing time for batch {} : {:.4f}s.".format(batch,time.perf_counter()-start_loading))    
    
    parse_arcs(arcs,dim,id_to_pos)
        
def test():
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments = 8,
        ring_count = 6,
        location=(-1,-1,-1),
        radius=0.1,
        )
    
if __name__== "__main__":
    main()