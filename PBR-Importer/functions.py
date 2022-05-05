import bpy, os, io
from urllib import request 
import math

def load_image(url):
    img = None
    # Load image file from url.    
    try:
        #make a temp filename that is valid
        tmp_filename = "/tmp/temp.png"
        #fetch the image in this file
        request.urlretrieve(url, tmp_filename)
        #create a blender datablock of it
        img = bpy.data.images.load(tmp_filename)
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