import bpy, os
from mathutils import Matrix, Vector
from urllib import request 
import math

def hex_to_rgb(value):
    lv = len(value)
    rgb255 = list(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return [x/255 for x in rgb255]

#Scale a 2D vector v, considering a scale s and a pivot point p
def Scale2D( v, s, p ):
    return ( p[0] + s[0]*(v[0] - p[0]), p[1] + s[1]*(v[1] - p[1]) )     

#Scale a UV map iterating over its coordinates to a given scale and with a pivot point
def ScaleUV( uvMap, scale, pivot ):
    for uvIndex in range( len(uvMap.data) ):
        uvMap.data[uvIndex].uv = Scale2D( uvMap.data[uvIndex].uv, scale, pivot )

def scale_uv(obj, amount):
    # Defines the pivot and scale
    pivot = Vector( (0.5, 0.5) )
    scale = Vector( (amount, amount) )

    # Handle to UV map
    uvMap = obj.data.uv_layers[0]

    if obj is not None:
        ScaleUV( uvMap, scale, pivot )

def load_image(url, isHDRI = False):
    img = None
    # Load image file from url.    
    try:
        # Make a temp filename that is valid
        tmp_filename = "./temp." + "pic" if isHDRI else "png"

        # Fetch the image in this file
        request.urlretrieve(url, os.path.abspath(tmp_filename))

        # Create a blender datablock of it
        img = bpy.data.images.load(os.path.abspath(tmp_filename))

        # Pack the image in the blender file
        img.pack()

        # Delete the temp image from local directory
        os.remove(os.path.abspath(tmp_filename))

    except Exception as e:
        raise NameError("Cannot load image: {0}".format(e))

    return img

def load_glb(url):
    glb = None
    try:
        # Make a temp filename that is valid
        tmp_filename = "./temp.glb"

        # Fetch the file
        request.urlretrieve(url, os.path.abspath(tmp_filename))

        # Import glb file
        bpy.ops.import_scene.gltf(filepath=os.path.abspath(tmp_filename))

        # Set object origin
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')

        # Handle to active object
        glb = bpy.context.view_layer.objects.active

        # Remove local temp file
        os.remove(os.path.abspath(tmp_filename))

    except Exception as e:
        raise NameError("Cannot load file: {0}".format(e))

    return glb

"""Creates Light from data in json"""
def create_light(data):
    # Create light datablock
    light_data = bpy.data.lights.new(name="light-data", type='POINT')

    # Set light intensity
    light_data.energy = data['object']['intensity']*100000

    # Set light radius
    light_data.shadow_soft_size = 1

    # Create color RGB list from hex value 
    color = hex_to_rgb(hex(data['object']['color'])[2:8])

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

    # Sets active camera
    bpy.context.scene.camera = camera

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

    node_background.inputs["Strength"].default_value = .3

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


"""Creates a plane which represents the floor"""
def create_floor(data):
    # Create plane
    bpy.ops.mesh.primitive_plane_add(size = 200)

    # Handle to floor
    floor = bpy.context.view_layer.objects.active

    # Set floor name
    floor.name = data['name']

    # Create material
    if 'files' in data:
        create_material(data['files'], floor, 'large', data['materialProps'])

    scale_uv(floor, 6)
    

"""Sets object material and transform properties"""
def set_obj_props(data, obj):
    # Create Material
    if 'files' in data['materialData']:
        create_material(data['materialData']['files'], obj, 'medium', data['materialData']['materialProps'])

    texture_repeat = None
    if 'textureRepeat' in data['materialData']['materialProps']:
        texture_repeat = data['materialData']['materialProps']['textureRepeat']

    if texture_repeat is not None:
        scale_uv(obj, texture_repeat)
    else:
        scale_uv(obj, 1.7)

    # Set location
    obj.location.x = data['position'][0]
    obj.location.y = -data['position'][2]
    obj.location.z = data['position'][1]

    # Sets rotation mode to YZX
    obj.rotation_mode = 'YZX'

    # Set Rotation
    obj.rotation_euler[0] = data['rotation'][0]
    obj.rotation_euler[1] = -data['rotation'][2]
    obj.rotation_euler[2] = data['rotation'][1]

    # Set scale
    obj.scale.x = data['scale'][0]
    obj.scale.y = data['scale'][2]
    obj.scale.z = data['scale'][1]


"""Import glb object with properties from json"""
def import_glb(data):
    obj = load_glb(data['files']['gltf_original'])

    # Sets object name
    obj.name = data['name']

    # Sets all properties for object
    set_obj_props(data, obj)

"""Create sphere object with properties from json"""
def create_sphere(data):
    # Create sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments = 64, ring_count = 64, radius = 4.5)
    bpy.ops.object.shade_smooth()

    # Handle to sphere
    sphere = bpy.context.view_layer.objects.active

    # Sets all properties for object
    set_obj_props(data, sphere)

"""Create cube object with properties from json"""
def create_cube(data):
    # Create cube
    bpy.ops.mesh.primitive_cube_add(size = 1)

    # Handle to cube
    cube = bpy.context.view_layer.objects.active

    # Sets all properties for object
    set_obj_props(data, cube)

    # Set dimensions
    cube.dimensions = [5, 6, 5]

"""Create plane object with properties from json"""
def create_plane(data):
    # Create plane
    bpy.ops.mesh.primitive_cube_add(size = 1)

    # Handle to plane
    plane = bpy.context.view_layer.objects.active

    # Sets all properties for object
    set_obj_props(data, plane)

    # Set dimensions
    plane.dimensions = [3, 0.1, 4]

"""Create cylinder object with properties from json"""
def create_cylinder(data):
    # Create cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius = 4, depth = 12)
    bpy.ops.object.shade_smooth()

    # Handle to cylinder
    cylinder = bpy.context.view_layer.objects.active

    # Sets all properties for object
    set_obj_props(data, cylinder)


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
    if 'sheen' in materialProps:
        shader.inputs['Sheen'].default_value = materialProps['sheen']

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
        if 'displacementScale' in materialProps:
            displacement_map.inputs["Scale"].default_value = materialProps['displacementScale']

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

    # Handle to Color ramp node for Base Color
    mix_rgb = nodes.new(type='ShaderNodeMixRGB')
    mix_rgb.blend_type = 'MULTIPLY'
    rgb = hex_to_rgb(hex(materialProps['color'])[2:10])
    rgb.append(1.0)
    mix_rgb.inputs[2].default_value = rgb

    #================================================================
    # Links
    #================================================================

    # Color
    if color is not None:
        links.new(color.outputs["Color"], mix_rgb.inputs[1])
    links.new(mix_rgb.outputs["Color"], shader.inputs["Base Color"])

    # Normal
    if normal is not None:    
        links.new(normal.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])

    # Roughness
    if roughness is not None:
        links.new(roughness.outputs["Color"], shader.inputs["Roughness"])

    # Displacement
    if displacement is not None:
        links.new(displacement.outputs["Color"], displacement_map.inputs["Height"])
        links.new(displacement_map.outputs["Displacement"], output.inputs["Displacement"])

    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    #==================================================================

    obj.data.materials.append(mat) #add the material to the object