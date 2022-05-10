from unicodedata import name
import bpy, os
from urllib import request 
import math

def hex_to_rgb(value):
    lv = len(value)
    return list(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def load_image(url, isHDRI = False):
    img = None
    # Load image file from url.    
    try:
        #make a temp filename that is valid
        tmp_filename = "./temp." + "pic" if isHDRI else "png"
        #fetch the image in this file
        request.urlretrieve(url, os.path.abspath(tmp_filename))
        #create a blender datablock of it
        img = bpy.data.images.load(os.path.abspath(tmp_filename))
        #pack the image in the blender file so...
        img.pack()
        #...we can delete the temp image
        os.remove(os.path.abspath(tmp_filename))
    except Exception as e:
        raise NameError("Cannot load image: {0}".format(e))

    return img

def load_glb(url):
    glb = None
    try:
        #make a temp filename that is valid
        tmp_filename = "./temp.glb"
        #fetch the file
        request.urlretrieve(url, os.path.abspath(tmp_filename))
        #import glb file
        bpy.ops.import_scene.gltf(filepath=os.path.abspath(tmp_filename))
        #set object origin
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
        #handle to active object
        glb = bpy.context.view_layer.objects.active
        #remove local temp file
        os.remove(os.path.abspath(tmp_filename))
    except Exception as e:
        raise NameError("Cannot load file: {0}".format(e))

    return glb


def create_light(data):
    # Create light datablock
    light_data = bpy.data.lights.new(name="light-data", type='POINT')

    # Set light intensity
    light_data.energy = 100*data['object']['intensity']

    # Set light radius
    light_data.shadow_soft_size = 1

    # Create color RGB list from hex value 
    color = hex_to_rgb(str(data['object']['color']))
    color.pop()

    # Set color
    light_data.color = color

    # Create new object, pass the light data 
    light_object = bpy.data.objects.new(name=data['object']['name'], object_data=light_data)

    # Link object to collection in context
    bpy.context.collection.objects.link(light_object)

    # Change light position
    light_object.location.x = data['position']['x']
    light_object.location.y = -data['position']['z']
    light_object.location.z = data['position']['y']

"""Creates Camera object from data in json"""
def create_camera(data):
    name = "Camera"

    # Create Camera
    camera_data = bpy.data.cameras.new(name=name)
    camera_object = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera_object)

    # Handle to camera
    camera = bpy.data.objects[name]

    # Set location
    camera.location.x = data['position']['x']
    camera.location.y = -data['position']['z']
    camera.location.z = data['position']['y']

    # Set rotation mode
    camera.rotation_mode = 'ZYX'

    # Set rotation
    camera.rotation_euler[0] = math.radians(90)
    camera.rotation_euler[0] += data['rotation']['_x']
    camera.rotation_euler[1] += data['rotation']['_y']
    camera.rotation_euler[2] += data['rotation']['_z']

    # Set FOV
    camera.data.lens_unit = 'FOV'
    camera.data.angle = math.radians(data['object']['fov']) 

    # Sets focus distance
    camera.data.dof.use_dof = True 
    camera.data.dof.focus_distance = data['object']['focus'] 


"""Imports hdri file and sets it as background"""
def import_hdri(url):
    # Get the environment node tree of the current scene
    node_tree = bpy.context.scene.world.node_tree
    tree_nodes = node_tree.nodes

    # Clear all nodes
    tree_nodes.clear()

    # Add Background node
    node_background = tree_nodes.new(type='ShaderNodeBackground')

    # Add Environment Texture node
    node_environment = tree_nodes.new('ShaderNodeTexEnvironment')
    # Load and assign the image to the node property
    node_environment.image = load_image(url, isHDRI=True) # Relative path

    # Add Output node
    node_output = tree_nodes.new(type='ShaderNodeOutputWorld')   

    # Link all nodes
    links = node_tree.links
    links.new(node_environment.outputs["Color"], node_background.inputs["Color"])
    links.new(node_background.outputs["Background"], node_output.inputs["Surface"])

"""Import glb object with properties from json"""
def import_glb(data):
    obj = load_glb(data['files']['gltf_original'])

    # Sets object name
    obj.name = data['name']

    # Create Material
    create_material(data['materialData']['files'], obj, 'medium', data['materialData']['materialProps'])

    # Set location
    obj.location.x = data['position'][0]
    obj.location.y = -data['position'][2]
    obj.location.z = data['position'][1]

    # Sets rotation mode to XYZ
    obj.rotation_mode = 'XYZ'

    # Set Rotation
    obj.rotation_euler[0] = data['rotation'][0]
    obj.rotation_euler[1] = data['rotation'][2]
    obj.rotation_euler[2] = data['rotation'][1]

    # Set scale
    obj.scale.x = data['scale'][0]
    obj.scale.y = data['scale'][2]
    obj.scale.z = data['scale'][1]


"""Creates a plane which represents the floor"""
def create_plane(data):
    # Create plane
    bpy.ops.mesh.primitive_plane_add(size = 50)

    # Handle to floor
    floor = bpy.context.view_layer.objects.active

    # Set floor name
    floor.name = data['name']

    # Create material
    create_material(data['files'], floor, 'large', data['materialProps'])

    bpy.ops.object.modifier_add(type='ARRAY')
    floor.modifiers[0].relative_offset_displace[0] = 1
    
    bpy.ops.object.modifier_add(type='ARRAY')
    floor.modifiers[1].relative_offset_displace[0] = 0
    floor.modifiers[1].relative_offset_displace[1] = 1
    
    bpy.ops.object.modifier_add(type='ARRAY')
    floor.modifiers[2].relative_offset_displace[0] = -1
    
    bpy.ops.object.modifier_add(type='ARRAY')
    floor.modifiers[3].relative_offset_displace[0] = 0
    floor.modifiers[3].relative_offset_displace[1] = -1
    

"""Creates Principled BSDF Material and assigns textures from json"""
def create_material(files, obj, size, materialProps):
    if len(obj.data.materials) >= 1:
        obj.data.materials.pop(index = 0)
    mat = bpy.data.materials.new(name=obj.name) #set new material to variable
    mat.use_nodes = True

    # Clear nodes
    if mat.node_tree:
        mat.node_tree.links.clear()
        mat.node_tree.nodes.clear()

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')

    # Handle to shader node
    shader = nodes.new(type='ShaderNodeBsdfPrincipled')

    # Handle to normal map node
    normal_map = nodes.new(type='ShaderNodeNormalMap')

    # Handle to displacement node
    displacement_map = nodes.new(type='ShaderNodeDisplacement')

    # Assign material props
    if 'clearcoat' in materialProps:
        shader.inputs['Clearcoat'].default_value = materialProps['clearcoat']
    if 'clearcoatRoughness' in materialProps:
        shader.inputs['Clearcoat Roughness'].default_value = materialProps['clearcoatRoughness']
    if 'ior' in materialProps:
        shader.inputs['IOR'].default_value = materialProps['ior']
    if 'metalness' in materialProps:
        shader.inputs['Metallic'].default_value = materialProps['metalness']
    if 'transmission' in materialProps:
        shader.inputs['Transmission'].default_value = materialProps['transmission']

    # Initialize texture variables
    color = None
    displacement = None
    normal = None
    roughness = None

    # Handle to color texture
    if size+'_color' in files:
        color = nodes.new(type='ShaderNodeTexImage')
        color.image = load_image(files[size+'_color'])

    # Handle to displacement texture
    if size+'_displacement' in files:
        displacement = nodes.new(type='ShaderNodeTexImage')
        displacement.image = load_image(files[size+'_displacement'])

    # Handle to normal texture
    if size+'_normal' in files:
        normal = nodes.new(type='ShaderNodeTexImage')
        normal.image = load_image(files[size+'_normal'])
        normal.image.colorspace_settings.name = 'Non-Color'

    # Handle to roughness texture
    if size+'_roughness' in files:
        roughness = nodes.new(type='ShaderNodeTexImage')
        roughness.image = load_image(files[size+'_roughness'])
        roughness.image.colorspace_settings.name = 'Non-Color'

    # Links
    if color is not None:
        links.new(color.outputs["Color"], shader.inputs["Base Color"])
    if normal is not None:    
        links.new(normal.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])
    if roughness is not None:
        links.new(roughness.outputs["Color"], shader.inputs["Roughness"])
    if displacement is not None:
        links.new(displacement.outputs["Color"], displacement_map.inputs["Height"])
        links.new(displacement_map.outputs["Displacement"], output.inputs["Displacement"])

    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    obj.data.materials.append(mat) #add the material to the object