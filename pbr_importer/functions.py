import bpy, os
from mathutils import Matrix, Vector
from urllib import request 
import math


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

def scale_uv(obj, amountX, amountY, offsetX = 0, offsetY = 0, isDynamic = False):
    if obj.data is None:
        return

    if len(obj.data.uv_layers) <= 0:
        return

    x_scale = amountX if amountX is not None else 1
    y_scale = amountY if amountY is not None else 1

    x_offset = offsetX if offsetX is not None else 0
    y_offset = offsetY if offsetY is not None else 0
    
    # Defines the pivot and scale
    if isDynamic:
        pivot = Vector( (.5+x_offset, .5+y_offset) )
    else:
        pivot = Vector( (x_offset, y_offset) )

    scale = Vector( (x_scale, y_scale) )

    # Handle to UV map
    uvMap = obj.data.uv_layers[0]

    if obj is not None:
        ScaleUV( uvMap, scale, pivot )

# Flip our y axis on all our UVs
def flip_uvs_y(obj):
    if obj.data is None:
        return
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

    

def load_image(url, width = None, height = None, isHDRI = False):
    img = None
    # Load image file from url.    
    try:
        # Make a temp filename that is valid
        tmp_filename = "./temp." + "pic" if isHDRI else "png"

        # Fetch the image in this file
        request.urlretrieve(url, os.path.abspath(tmp_filename))

        # Create a blender datablock of it
        img = bpy.data.images.load(os.path.abspath(tmp_filename))

        # scale image accorting to WxH
        if width is not None and height is not None:
            img.scale(width,height)

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
        create_material(data['files'], floor, 'large', data['materialProps'])

    scale_uv(floor, 6, 6)
    

"""Sets object material and transform properties"""
def set_obj_props(data, obj, isDynamic = False):
    # Create Material
    if not isDynamic:
        if 'files' in data['materialData']:
            create_material(data['materialData']['files'], obj, 'medium', data['materialData']['materialProps'])
        else:
            create_material(None, obj, 'medium', data['materialData']['materialProps'])

    # Handle to Texture Repeat value
    texture_repeat = None
    if 'textureRepeat' in data['materialData']['materialProps']:
        texture_repeat = data['materialData']['materialProps']['textureRepeat']

    # Apply scaling to UVs
    if texture_repeat is not None:
        scale_uv(obj, texture_repeat, texture_repeat)

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

    # Flip UVs on y axis
    flip_uvs_y(obj)

    # Sets all properties for object
    set_obj_props(data, obj)


"""Import dynamic glb object with properties from json"""
def import_dynamic_glb(data):
    obj = load_glb(data['files']['medium'])

    image = None

    # get dynamic image object
    if obj.name.startswith("dynamic_image"):
        image = obj
    else:
        for i in bpy.data.objects:
            if i.name.startswith("dynamic_image") and i.parent == obj:
                image = i

    # Sets all properties for object
    set_obj_props(data, obj, isDynamic=True)
    
    # Creates material for dynamic images
    if image is not None:
        create_dynamic_image_material(image, data['dynamicMaterialProps'])

"""Create sphere object with properties from json"""
def create_sphere(data):
    # Create sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments = 64, ring_count = 64, radius = 4.5)
    bpy.ops.object.shade_smooth()

    # Handle to sphere
    sphere = bpy.context.view_layer.objects.active

    # Add solifify modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')

    # Sets all properties for object
    set_obj_props(data, sphere)

"""Create cube object with properties from json"""
def create_cube(data):
    vertices = [(-2.5, -3, -2.5), (2.5, -3, -2.5), (-2.5, -3, 2.5), (2.5, -3, 2.5), (-2.5, 3, -2.5), (2.5, 3, -2.5), (-2.5, 3, 2.5), (2.5, 3, 2.5)]
    edges = []
    faces = [(0,1,3,2),(0,2,6,4),(4,6,7,5),(1,3,7,5),(3,2,6,7),(0,1,5,4)]

    mesh = bpy.data.meshes.new(data["name"])
    mesh.from_pydata(vertices,edges,faces)
    mesh.update()

    mesh.uv_layers.new(name=data["name"])

    cube = bpy.data.objects.new(data["name"], mesh)

    view_layer = bpy.context.view_layer
    view_layer.active_layer_collection.collection.objects.link(cube)

    # Add solifify modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')

    # Flip UVs on y axis
    flip_uvs_y(cube)

    # Sets all properties for object
    set_obj_props(data, cube)

"""Create plane object with properties from json"""
def create_plane(data):
    vertices = [(-1.5, -.05, -2), (1.5, -.05, -2), (-1.5, -.05, 2), (1.5, -.05, 2), (-1.5, .05, -2), (1.5, .05, -2), (-1.5, .05, 2), (1.5, .05, 2)]
    edges = []
    faces = [(0,1,3,2),(0,2,6,4),(4,6,7,5),(1,3,7,5),(3,2,6,7),(0,1,5,4)]

    mesh = bpy.data.meshes.new(data["name"])
    mesh.from_pydata(vertices,edges,faces)
    mesh.update()

    mesh.uv_layers.new(name=data["name"])

    plane = bpy.data.objects.new(data["name"], mesh)

    view_layer = bpy.context.view_layer
    view_layer.active_layer_collection.collection.objects.link(plane)

    # Add solifify modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')

    # Flip UVs on y axis
    flip_uvs_y(plane)

    # Sets all properties for object
    set_obj_props(data, plane)

"""Create cylinder object with properties from json"""
def create_cylinder(data):
    # Create cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius = 4, depth = 12)
    bpy.ops.object.shade_smooth()

    # Handle to cylinder
    cylinder = bpy.context.view_layer.objects.active

    # Add solifify modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')

    # Sets all properties for object
    set_obj_props(data, cylinder)


"""Creates Material for dynamic image objects"""
def create_dynamic_image_material(obj, props):
    if obj.data is None:
        return
    if len(obj.data.materials) >= 1:
        for i in obj.data.materials:
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

    # Handle to color texture
    color = nodes.new(type='ShaderNodeTexImage')
    color.image = load_image(props['files'], width=props['width'], height=props['height'])

    # Color
    if color is not None and color.image is not None:
        links.new(color.outputs["Color"], shader.inputs["Base Color"] )

    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    #==================================================================
    obj.data.materials.append(mat) #add the material to the object

    # Apply scaling to UVs
    if props['repeat'] is not None:
        scale_uv(obj, props['repeat']['x'] , props['repeat']['y'], offsetX = props['offset']['x'], offsetY= props['offset']['y'], isDynamic=True )

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