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
        os.remove(tmp_filename)
    except Exception as e:
        raise NameError("Cannot load image: {0}".format(e))

    return img

def create_camera(data):
    name = "Camera"

    # Create Camera
    camera_data = bpy.data.cameras.new(name=name)
    camera_object = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera_object)

    # Set location
    bpy.data.objects[name].location.x = data['position']['x']
    bpy.data.objects[name].location.y = data['position']['y']
    bpy.data.objects[name].location.z = data['position']['z']

    # Set rotation
    bpy.data.objects[name].rotation_euler[0] = data['rotation']['_x']
    bpy.data.objects[name].rotation_euler[1] = data['rotation']['_y']
    bpy.data.objects[name].rotation_euler[2] = data['rotation']['_z']

    # Set FOV
    bpy.data.objects[name].data.lens_unit = 'FOV'
    bpy.data.objects[name].data.angle = math.radians(data['object']['fov']) 

    # Sets focus distance
    bpy.data.objects[name].data.dof.use_dof = True 
    bpy.data.objects[name].data.dof.focus_distance = data['object']['focus'] 


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