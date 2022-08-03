#########################################################################################################################################
#
# to run use the command: blender --background --python pbr_import.py --
#
# arguments:
# [-h] -> help
# --input INPUT -> input directory (string)
# --output OUTPUT -> output directory (string)
# --width WIDTH -> render width (int)
# --height HEIGHT -> render height (int)
# --samples SAMPLES -> max render samples (int)
# --texture_size SIZE -> texture size (string)
# --mesh_size SIZE -> mesh size (string)
#
#########################################################################################################################################

from random import sample
import bpy, os
from mathutils import Matrix, Vector
from urllib import request 
import math
import sys
import json
import ssl
import hashlib
import argparse


# Create cache folder path if not existing
CACHE_PATH = "cache"
if not os.path.exists(CACHE_PATH):
    os.mkdir(CACHE_PATH)

#=================================================================================
#COLOR CONVERSIONS
#=================================================================================
def rgb_int2tuple(rgbint):
  return ( rgbint // 256 // 256 % 256, rgbint // 256 % 256, rgbint % 256)

def srgb_to_linear(x: float) -> float:
	if x <= 0.0:
		return 0.0
	elif x >= 1:
		return 1.0
	elif x < 0.04045:
		return x / 12.92
	else:
		return ((x + 0.055) / 1.055) ** 2.4

def linear_from_int(rgbint):
  return list(map (lambda y: srgb_to_linear(y/255), rgb_int2tuple(rgbint)))


def rgb_to_hsv(r, g, b):
    r = float(r)
    g = float(g)
    b = float(b)
    high = max(r, g, b)
    low = min(r, g, b)
    h, s, v = high, high, high

    d = high - low
    s = 0 if high == 0 else d/high

    if high == low:
        h = 0.0
    else:
        h = {
            r: (g - b) / d + (6 if g < b else 0),
            g: (b - r) / d + 2,
            b: (r - g) / d + 4,
        }[high]
        h /= 6

    return h, s, v

def hsv_to_rgb(h, s, v):
    i = math.floor(h*6)
    f = h*6 - i
    p = v * (1-s)
    q = v * (1-f*s)
    t = v * (1-(1-f)*s)

    r, g, b = [
        (v, t, p),
        (q, v, p),
        (p, v, t),
        (p, q, v),
        (t, p, v),
        (v, p, q),
    ][int(i%6)]

    return r, g, b
#=================================================================================
#=================================================================================

def get_children(ob):
    return [ob_child for ob_child in bpy.data.objects if ob_child.parent == ob]

#Scale a 2D vector v, considering a scale s and a pivot point p
def Scale2D( v, s, p ):
    return ( p[0] + s[0]*(v[0] - p[0]), p[1] + s[1]*(v[1] - p[1]) )     

#Scale a UV map iterating over its coordinates to a given scale and with a pivot point
def ScaleUV( uvMap, scale, pivot ):
    for uvIndex in range( len(uvMap.data) ):
        uvMap.data[uvIndex].uv = Scale2D( uvMap.data[uvIndex].uv, scale, pivot )

def scale_uv(obj, amount):
    if obj.data is None:
        return

    if len(obj.data.uv_layers) <= 0:
        return
        
    # Defines the pivot and scale
    pivot = Vector( (0, 0) )
    scale = Vector( (amount, amount) )

    # Handle to UV map
    uvMap = obj.data.uv_layers[0]

    if obj is not None:
        ScaleUV( uvMap, scale, pivot )

# Flip our y axis on all our UVs
def flip_uvs_y(obj):
    min_uv_y = None
    max_uv_y = None
    for layer in obj.data.uv_layers:
        for loop in layer.data.values():
            if not min_uv_y:
                min_uv_y = loop.uv[1]
            elif loop.uv[1] < min_uv_y:
                min_uv_y = loop.uv[1]

            if not max_uv_y:
                max_uv_y = loop.uv[1]
            elif loop.uv[1] > max_uv_y:
                max_uv_y = loop.uv[1]

            loop.uv[1] *= -1

    if min_uv_y is None or max_uv_y is None:
        return
    height = max_uv_y - min_uv_y

    for loop in layer.data.values():
            loop.uv[1] += height + min_uv_y


def load_image(url, isHDRI = False):
    img = None
    is_in_cache = False

    # Hash URL
    encoded = url.encode()
    result = hashlib.sha256(encoded)

    # Make a temp filename that is valid
    tmp_filename = "./" + CACHE_PATH + "/"+ result.hexdigest()
    if isHDRI:
        tmp_filename += ".pic"
    else:
        tmp_filename += ".png"

    print(tmp_filename)

    # Checks if image is in cache
    if os.path.exists(os.path.abspath(tmp_filename)):
        is_in_cache = True

    # Load image file from url.    
    try:
        # Fetch the image if not in cache
        if not is_in_cache:
            request.urlretrieve(url, os.path.abspath(tmp_filename))

        # Create a blender datablock of it
        img = bpy.data.images.load(os.path.abspath(tmp_filename))

        # Pack the image in the blender file
        img.pack()

    except Exception as e:
        raise NameError("Cannot load image: {0}".format(e))

    return img

def load_glb(url):
    glb = None
    is_in_cache = False

    # Hash URL
    encoded = url.encode()
    result = hashlib.sha256(encoded)

    # Make a temp filename that is valid
    tmp_filename = "./" + CACHE_PATH + "/"+ result.hexdigest() + ".glb"

    print(tmp_filename)

    # Checks if image is in cache
    if os.path.exists(os.path.abspath(tmp_filename)):
        is_in_cache = True

    try:
        # Fetch the file if not iin cache
        if not is_in_cache:
            request.urlretrieve(url, os.path.abspath(tmp_filename))

        # Import glb file
        bpy.ops.import_scene.gltf(filepath=os.path.abspath(tmp_filename))

        # Handle to active object
        glb = bpy.context.view_layer.objects.active

    except Exception as e:
        raise NameError("Cannot load file: {0}".format(e))

    return glb

def create_glb(shape):
    glb = None
    # Make a temp filename that is valid
    tmp_filename = "./" + CACHE_PATH + "/"+ shape + ".glb"

    path = os.path.abspath(tmp_filename)

    # Import glb file
    bpy.ops.import_scene.gltf(filepath=path)

    # Set object origin
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')

    # Handle to active object
    glb = bpy.context.view_layer.objects.active

    flip_uvs_y(glb)

    return glb

"""Creates Light from data in json"""
def create_light(data):
    # Create light datablock
    light_data = bpy.data.lights.new(name="light-data", type='POINT')

    # Set light intensity
    light_data.energy = data['object']['intensity']*100000

    # Set light radius
    light_data.shadow_soft_size = 7

    # Create color RGB list from hex value 
    color = linear_from_int(data['object']['color'])

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

    node_background.inputs["Strength"].default_value = 1

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
    if 'name' in data:
        floor.name = data['name']

    # Create material
    if 'files' in data:
        create_material(data['files'], floor, texture_size, data['materialProps'])

    scale_uv(floor, 6)
    

"""Sets object material and transform properties"""
def set_obj_props(data, obj):
    # Create Material
    if 'files' in data['materialData']:
        create_material(data['materialData']['files'], obj, texture_size, data['materialData']['materialProps'])
    else:
        create_material(None, obj, texture_size, data['materialData']['materialProps'])


    # Handle to Texture Repeat value
    texture_repeat = None
    if 'textureRepeat' in data['materialData']['materialProps']:
        texture_repeat = data['materialData']['materialProps']['textureRepeat']

    # Apply scaling to UVs
    if texture_repeat is not None:
        scale_uv(obj, texture_repeat)


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

    child = get_children(obj)

    if child is not None and len(child) > 0:
        obj = child[0]
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')


    # Sets object name
    obj.name = data['name']

    # Flip UVs on y axis
    flip_uvs_y(obj)

    # Sets all properties for object
    set_obj_props(data, obj)

"""Create sphere object with properties from json"""
def create_sphere(data):
    sphere = create_glb(shape="sphere")

    # Add solifify modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')

    # Sets all properties for object
    set_obj_props(data, sphere)

"""Create cube object with properties from json"""
def create_cube(data):
    cube = create_glb(shape="cube")

    # Add solifify modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')

    # Flip UVs on y axis
    flip_uvs_y(cube)

    # Sets all properties for object
    set_obj_props(data, cube)

"""Create plane object with properties from json"""
def create_plane(data):
    plane = create_glb(shape="plane")

    # Add solifify modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')

    # Flip UVs on y axis
    flip_uvs_y(plane)

    # Sets all properties for object
    set_obj_props(data, plane)

"""Create cylinder object with properties from json"""
def create_cylinder(data):
    cylinder = create_glb(shape="cylinder")

    # Add solifify modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')

    # Sets all properties for object
    set_obj_props(data, cylinder)


"""Creates Principled BSDF Material and assigns textures from json"""
def create_material(files, obj, size, materialProps):
    if obj.data is None:
        return
    if len(obj.data.materials) >= 1:
        obj.data.materials.pop(index = 0)
    mat = bpy.data.materials.new(name=obj.name) #set new material to variable
    mat.use_nodes = True
    rgb = None

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
    if 'emissive' in materialProps:
        if not type(materialProps['emissive']) == str:
            shader.inputs['Emission'].default_value = (*linear_from_int(materialProps['emissive']), 1)

    # Initialize texture variables
    color = None
    displacement = None
    normal = None
    roughness = None

    # Handle to color texture
    color = nodes.new(type='ShaderNodeTexImage')
    if files is not None and size+'_color' in files:
        color.image = load_image(files[size+'_color'])

    # Handle to displacement texture
    displacement = nodes.new(type='ShaderNodeTexImage')
    if files is not None and size+'_displacement' in files:
        displacement.image = load_image(files[size+'_displacement'])
        if 'displacementScale' in materialProps:
            displacement_map.inputs["Scale"].default_value = materialProps['displacementScale']

    # Handle to normal texture
    normal = nodes.new(type='ShaderNodeTexImage')
    if files is not None and size+'_normal' in files:
        normal.image = load_image(files[size+'_normal'])
        normal.image.colorspace_settings.name = 'Non-Color'

    # Handle to roughness texture
    roughness = nodes.new(type='ShaderNodeTexImage')
    if files is not None and size+'_roughness' in files:
        roughness.image = load_image(files[size+'_roughness'])
        roughness.image.colorspace_settings.name = 'Non-Color'

    # Handle to MixRGB Node
    mix_rgb = nodes.new(type='ShaderNodeMixRGB')
    mix_rgb.blend_type = 'MULTIPLY'
    if 'color' in materialProps and not type(materialProps['color']) == str:
        rgb = (*linear_from_int(materialProps['color']), 1)
        mix_rgb.inputs[2].default_value = rgb
        mix_rgb.inputs[0].default_value = 1

    #================================================================
    # Links
    #================================================================

    # Color
    if color is not None and color.image is not None:
        links.new(color.outputs["Color"], mix_rgb.inputs[1])
        links.new(mix_rgb.outputs["Color"], shader.inputs["Base Color"] )
    elif rgb is not None:
        transmission = shader.inputs['Transmission'].default_value
        h,s,v = rgb_to_hsv(*linear_from_int(materialProps['color']))
        v_range = float(1.0-v)
        v = v + (transmission*v_range)
        s_threshold = 0.25
        if s >= s_threshold:
            s_range = s-s_threshold
            s = s - (transmission*s_range)
        rgb = (*hsv_to_rgb(h,s,v), 1)
        shader.inputs["Base Color"].default_value = rgb

    # Normal
    if normal is not None and normal.image is not None:    
        links.new(normal.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])

    # Roughness
    if roughness is not None and roughness.image is not None:
        links.new(roughness.outputs["Color"], shader.inputs["Roughness"])
    elif 'roughness' in materialProps:
        shader.inputs['Roughness'].default_value = materialProps['roughness']

    # Displacement
    if displacement is not None and displacement.image is not None:
        links.new(displacement.outputs["Color"], displacement_map.inputs["Height"])
        links.new(displacement_map.outputs["Displacement"], output.inputs["Displacement"])

    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    #==================================================================

    obj.data.materials.append(mat) #add the material to the object


"""Load and return json file"""
def load_data(path):
    file = open(path, mode='r')
    data = file.read()
    file.close()

    return json.loads(data)

"""Renders scene to specified filepath"""
def render(output_dir, output_filename = 'render.jpg'):  
    bpy.context.scene.render.filepath = os.path.join(os.path.abspath(output_dir), output_filename)
    bpy.ops.render.render(write_still = True)

def set_render_settings():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = samples
    scene.render.resolution_x = width
    scene.render.resolution_y = height

def _get_argv_after_doubledash():
    """
    Given the sys.argv as a list of strings, this method returns the
    sublist right after the '--' element (if present, otherwise returns
    an empty list).
    """
    try:
        idx = sys.argv.index("--")
        return sys.argv[idx+1:] # the list after '--'
    except ValueError as e: # '--' not in the list:
        return []


def main():
    # add arguments to command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', help="input directory", type= str, required=True)
    parser.add_argument('--output', help="output directory", type= str,  required=True)
    parser.add_argument('--height', help="render height", type= int, default= 1000)
    parser.add_argument('--width', help="render width", type= int, default= 1000)
    parser.add_argument('--samples', help="render samples", type= int, default= 3)
    parser.add_argument('--texture_size', help="texture size", type= str,  default='large')
    parser.add_argument('--mesh_size', help="mesh size", type= str,  default='large')

    # parse arguments
    args = parser.parse_args(args=_get_argv_after_doubledash())

    # assign arguments to global variables
    global input_dir
    global output_dir
    global height
    global width
    global samples
    global texture_size
    global mesh_size
    input_dir = args.input
    output_dir = args.output
    height = args.height
    width = args.width
    samples = args.samples
    texture_size = args.texture_size
    mesh_size = args.mesh_size

    ssl._create_default_https_context = ssl._create_unverified_context

    json = load_data(input_dir)

    # Remove all objects
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)

    # Create camera
    create_camera(json['camera'])

    # Create light
    create_light(json['light'])

    # Import HDRI image as enviroment
    import_hdri(json['environment'])

    # Create floor
    create_floor(json['floor'])

    # Import all objects
    for i in json['objects']:
        if i['name'] == "Sphere":
            create_sphere(i)
        if i['name'] == "Cube":
            create_cube(i)
        if i['name'] == "Plane":
            create_plane(i)
        if i['name'] == "Cylinder":
            create_cylinder(i)
        if i['type'] == "gltf":
            import_glb(i)

    set_render_settings()
    
    render(output_dir = output_dir)


if __name__ == "__main__":
    main()