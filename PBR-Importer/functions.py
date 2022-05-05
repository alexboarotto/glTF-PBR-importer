import bpy, os
from urllib import request 
import math

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
        #handle to active object
        glb = bpy.context.view_layer.objects.active
        #remove local temp file
        os.remove(os.path.abspath(tmp_filename))
    except Exception as e:
        raise NameError("Cannot load file: {0}".format(e))

    return glb


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
    camera.location.y = data['position']['z']
    camera.location.z = data['position']['y']

    # Set rotation
    camera.rotation_euler[0] += data['rotation']['_x']
    camera.rotation_euler[1] += data['rotation']['_z']
    camera.rotation_euler[2] += data['rotation']['_y']

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
    node_environment.location = -300,0

    # Add Output node
    node_output = tree_nodes.new(type='ShaderNodeOutputWorld')   
    node_output.location = 200,0

    # Link all nodes
    links = node_tree.links
    link = links.new(node_environment.outputs["Color"], node_background.inputs["Color"])
    link = links.new(node_background.outputs["Background"], node_output.inputs["Surface"])

"""Import glb object with properties from json"""
def import_glb(data):
    obj = load_glb(data['files']['gltf_original'])

    # Sets object name
    obj.name = data['name']

    # Set location
    obj.location.x = data['position'][0]
    obj.location.y = data['position'][2]
    obj.location.z = data['position'][1]

    # Set Rotation
    obj.rotation_euler[0] = data['rotation'][0]
    obj.rotation_euler[1] = data['rotation'][2]
    obj.rotation_euler[2] = data['rotation'][1]

