##'''
##generateMap_blender.py
##Author: Clayton Bennett
##Created: 5/5/2022
##
##Description: Import, scale, and place objects, like majic.
##

##Improvements to make:
# - Add way to show iterative visco-passage plots and time-passsage plots, of multiple STL's from the same plot name, which should include text from the original filename as the label, and shiould sort in chronological order..

'''
User input section:
'''
#textIdentifier = "_50x50_EI_nearest_baseExperiment.stl" # expected format of filename: variety,plotname. Ex: Purl,SW429_textIdentifier.....stl
textIdentifier = "_210x210_peaksUsed_noFloor.stl"
axis = "Force" # "Force" or "EI" # this will fix itself only if "EI" or "force" is in textIdentifer.
#axis = "EI"
tuneColorGradient = 0.18
showStems = "n" # y or n ? to show stem EI
#showStems = "y"
directory = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\CAD Drawings - Clayton\FieldMap'

'''
End, user input section.
'''


'''
COPY BELOW (Launch an instance of command windows, then copy and run these lines. Edit directory location as needed.):
cd C:\Program Files\Blender Foundation\Blender 3.1\
blender.exe --python "E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\CAD Drawings - Clayton\FieldMap\generateMap_blender.py" 
'''
#blender.exe --background --python "E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\CAD Drawings - Clayton\FieldMap\generateMap_blender.py"


##
##Useful notes:
###C:\Users\clayton\AppData\Roaming\Blender Foundation\Blender\3.1\scripts\addons
##'''

'''
Next dev:
- turn into program, with inputs of directory, text string, and if stems should be generated or not.
'''


# uniform scaling

# filename --> import ---> scale
import sys
#import pandas as pd
dir_code = "E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Code - Matlab, Python, etc\Code - Python - Data Processing, Computer"
sys.path.insert(0,dir_code)
#sys.path.insert(0,'C:\Python\Lib\site-packages')
import os
import math
import mathutils
import numpy as np
#
import bpy
import SortPlotSTLs
from SortPlotSTLs import plotcoordinates
import random
from random import randint
#from stems2021 import force_EI

inch = 0.0254

pathstring = 'E:\Backups\GoogleDrive_AgMEQ_03312022\SOCEM\Code - Matlab, Python, etc\Code - Python - Data Processing, Computer'
sys.path.insert(0, pathstring)


print("FRESH START %%%%%%%%%%%%%%%%%%%%%%%%%%%")
if ("force" in textIdentifier) or ("Force" in textIdentifier):
    axis = "Force"
elif ("EI_" in textIdentifier) or ("_EI" in textIdentifier):
    axis = "EI"

if showStems == "y":
    withStems = "_wStems"
else:
    withStems = ""

stl = ".stl"
textIdentifierText = textIdentifier.replace(stl,"")
#datetext = now
randomInteger = str(randint(1000,9999)) # this is here because i don't have internet enought to figure out how  get the dat, for file naming
exportfilename = directory + "\\" + "map_" + axis + withStems + textIdentifierText + "_" + randomInteger+ ".fbx" # this will need updated, and it will be run again later, after the tuneColorGradietn variable has been altered in the GUI
savepngname = directory + "\\" + "bake_joined.png"

if axis =="Force":
    dimension = "(lb)"
elif axis == "EI":
    dimension = "(lb*in^2)"

if showStems == "y":
    if axis == "EI":
        from stems2021 import stems_EI # this is hideous, because it doesn't know the order or the files. Needs database. Needs, dare I say, a CSV that has been exported from MATLAB.
    elif axis == "Force":
        from stems2021 import stems_force

# example file: "E:\\Backups\\GoogleDrive_AgMEQ_03312022\\SOCEM\\CAD Drawings - Clayton\\FieldMap\\UI Magic CL+,CF245_50x50_EI_nearest_baseExperiment.stl",


# change unit shown to 'in', rather than just scaling 
bpy.context.scene.unit_settings.system = 'IMPERIAL'
bpy.context.scene.unit_settings.length_unit='INCHES'

scene = bpy.data.scenes["Scene"]

#bpy.data.objects['Cube'].select_set(True)
#bpy.ops.object.delete()

#filelist = textIdentifyFiles(textIdentifier, directory) # for modularity


#xcoord, ycoord, plotlist, varietylist = plotcoordinates(textIdentifier, directory)
[X, Y, plotnames, varietynames, filenamelist] = plotcoordinates(textIdentifier, directory)
#print('X=',X)
#print('Y=',Y)
filenames_long =[]
for filename in filenamelist:
    filenames_long.append(directory+'\\'+filename)
  


'''
def print(data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")
'''
                
def move(obj,i,inch):
    #print(objectname)
    #obj = bpy.data.objects[objectname]
    #obj.select_set(True)   ## set the object
    loc = obj.location
    (x,y,z) = (X[i], Y[i], 0)
    obj.location = loc + mathutils.Vector((x*inch,y*inch,z*inch))

    #return x,y,z
    
""" def color(filename):

    print(filename) """


    
## scale
def scale(obj,maxZ,C,inch):
    #for filename in filenames:
    # filename = "Stingray CL+,CF447_50x50_EI_nearest_baseExperiment"
    
    #print(objectname) 
    #objectToSelect = bpy.data.objects[objectname]
    #objectToSelect.select_set(True)   ## set the object
    #bpy.context.view_layer.objects.active = obj ## set the object as active in the 3D viewport
    obj.scale = (1*inch, 1*inch, 5*inch) ## change the scale!!
    #print(maxZ)
    #print(objZ)
    if objZ > maxZ:
        maxZ = objZ
        print("maxZ = ", maxZ, " ", axis, dimension)
    #print(objectname)
    #return objectToSelect
    return maxZ
    
def stems(i,inch):
    (x,y,z) = (X[i], Y[i], 0)

    # create ten stems the ten stems for plot i
    c=10
    j=0
    for EI in stems_EI[i]:
        #bpy.ops.mesh.primitive_cube_add
        bpy.ops.mesh.primitive_cube_add(size=2, calc_uvs=True, enter_editmode=False, align='WORLD', location=((x+30)*inch, (y+j*c+30)*inch, EI/2*inch), rotation=(0, 0, 0), scale=(1*inch, 1*inch, EI/2*inch))
        j+=1
      
def color(obj):

    #mat = bpy.data.materials.get('colorGradient')
    id = 'colorGradient'
    mat = bpy.data.materials.new(name=id)
    mat.use_nodes = True
    mat.node_tree.links.clear()
    mat.node_tree.nodes.clear()

    #mat = bpy.data.materials.new(name=id)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # nodes.items()
    # [('Map Range', bpy.data.materials['colorGradient'].node_tree.nodes["Map Range"]), ('ColorRamp', bpy.data.materials['colorGradient'].node_tree.nodes["ColorRamp"]), ('Gradient Texture', bpy.data.materials['colorGradient'].node_tree.nodes["Gradient Texture"]), ('Texture Coordinate', bpy.data.materials['colorGradient'].node_tree.nodes["Texture Coordinate"]), ('Mapping', bpy.data.materials['colorGradient'].node_tree.nodes["Mapping"]), ('Material Output', bpy.data.materials['colorGradient'].node_tree.nodes["Material Output"]), ('Image Texture', bpy.data.materials['colorGradient'].node_tree.nodes["Image Texture"]), ('Principled BSDF', bpy.data.materials['colorGradient'].node_tree.nodes["Principled BSDF"]), ('Diffuse BSDF', bpy.data.materials['colorGradient'].node_tree.nodes["Diffuse BSDF"])]


    materialoutput = nodes.new(type='ShaderNodeOutputMaterial')
    shader = nodes.new(type='ShaderNodeBsdfDiffuse')
    maprange = nodes.new(type='ShaderNodeMapRange')
    mapping = nodes.new(type='ShaderNodeMapping')
    colorramp = nodes.new(type='ShaderNodeValToRGB')
    gradienttexture = nodes.new(type='ShaderNodeTexGradient')
    texturecoordinates = nodes.new(type='ShaderNodeTexCoord')
    # will be used later:
    imagetexture_baked = nodes.new(type='ShaderNodeTexImage')
    shader_image = nodes.new(type='ShaderNodeBsdfPrincipled')
    shader_image = nodes["Principled BSDF"]


    ## Create useful names for things (not necessary, but here essentially as a heading)
    ## Then,change values
    # ---------------------------------------------------startsectiondave::
    materialoutput = nodes["Material Output"]
    materialoutput.target = 'ALL'

    shader = nodes["Diffuse BSDF"]
    shader.inputs[1].default_value=0.0 # roughness = 0

    mapping = nodes["Mapping"]
    mapping.vector_type = 'VECTOR'
    #mapping.inputs[1].default_value = Vector((0.0, 2.3164799213409424, 0.0))
    mapping.inputs[2].default_value = mathutils.Euler((0.0, 1.5707963705062866, 0.0), 'XYZ')
    #mapping.inputs[3].default_value = mathutils.Vector((0.0, 0.0, .125))
    #mapping.inputs[3].default_value = mathutils.Vector((0.0, 0.0, 2.125))
    mapping.inputs[3].default_value = mathutils.Vector((0.0, 0.0, tuneColorGradient))

    maprange = nodes["Map Range"]
    maprange.data_type = 'FLOAT_VECTOR'
    maprange.interpolation_type = 'STEPPED'
    maprange.clamp = True
    maprange.inputs[0].default_value = 1.0
    maprange.inputs[1].default_value = 0.0
    maprange.inputs[2].default_value = 1.0
    maprange.inputs[3].default_value = 0.0
    maprange.inputs[4].default_value = 1.0
    maprange.inputs[5].default_value = 4.0
    """ maprange.inputs[6].default_value = 
    maprange.inputs[7].default_value = 
    maprange.inputs[8].default_value = 
    maprange.inputs[9].default_value = 
    maprange.inputs[10].default_value = 
    maprange.inputs[11].default_value =  """

    colorramp = nodes["ColorRamp"]
    colorramp.color_ramp.color_mode = 'RGB'
    colorramp.color_ramp.hue_interpolation = 'NEAR'
    colorramp.color_ramp.interpolation = 'LINEAR'
    #colorramp.color_ramp.elements.new(position = 0.0)
    colorramp.color_ramp.elements[0].position = 0.0
    colorramp.color_ramp.elements[0].color = 0.196, 0.0, 0.592, 1.0
    #colorramp.color_ramp.elements.new(position = 0.2)
    colorramp.color_ramp.elements[1].position = 0.1
    colorramp.color_ramp.elements[1].color = 0.017, 0.017, 0.643, 1.0
    colorramp.color_ramp.elements.new(position = 0.2)
    colorramp.color_ramp.elements[2].color = 0.010681, 0.490, 0.694, 1.0
    colorramp.color_ramp.elements.new(position = 0.5)
    colorramp.color_ramp.elements[3].color = 0.035487, 0.796018, 0.05627, 1.0
    colorramp.color_ramp.elements.new(position = 0.8)
    colorramp.color_ramp.elements[4].color = 0.64303, 0.473186, 0.013768, 1.0
    colorramp.color_ramp.elements.new(position = 1.0)
    colorramp.color_ramp.elements[5].color = 1.0, 0.0, 0.03, 1.0

    gradienttexture = nodes['Gradient Texture']
    gradienttexture.gradient_type = 'LINEAR'

    texturecoordinate = nodes['Texture Coordinate']
    texturecoordinate.object = bpy.data.objects['joinedObjects']

    shader_image = nodes["Principled BSDF"]

    imagetexture_baked = nodes["Image Texture"]
    #--------------------------------------------------------------endsectiondave

    # link texture nodes
    links.new(shader.outputs[0], materialoutput.inputs[0])
    links.new(maprange.outputs[1], shader.inputs[0]) #error
    links.new(colorramp.outputs[0], maprange.inputs[6]) # error
    links.new(gradienttexture.outputs[0], colorramp.inputs[0])
    links.new(mapping.outputs[0], gradienttexture.inputs[0])
    links.new(texturecoordinates.outputs[3], mapping.inputs[0])
    links.new(shader.outputs[0], materialoutput.inputs[0])
    links.new(imagetexture_baked.outputs[0],shader_image.inputs[0])
    
    # control location of texture nodes in the shader editor GUI so that they are easy to read
    texturecoordinate.location = mathutils.Vector((0.0,0.0))
    mapping.location = mathutils.Vector((250.0,0.0))
    gradienttexture.location = mathutils.Vector((500.0,0.0))
    colorramp.location = mathutils.Vector((725.0,0.0))
    maprange.location = mathutils.Vector((1000.0,0.0))
    shader.location = mathutils.Vector((1250.0,0.0))
    shader_image.location = mathutils.Vector((1250.0,-200.0))
    materialoutput.location = mathutils.Vector((1600.0,0.0))
    imagetexture_baked.location = mathutils.Vector((750.0,-250.0))

    bpy.data.objects['joinedObjects'].data.materials[0]=bpy.data.materials['colorGradient']

    


    return mat

def seekUserInput_colorGradient(mat):

    # Display GUI

    # complex version
    # - ask user to input value for tuneColorGradient (range 0.1 to 4.0, typically 0.4)
    # - take user input, update display
    # - allow user to accept, and then continue program

    # easy verion
    # - pause the program, and prompt user to go to Blender GUI and to fiddle with the number for tuneColorGradient, in Shading > Material nodes > Mapping > Scale > Z.
    # - allow user to accept, then continue the program
    # - can do this from CMD, instead of pop up window

    collecttwohundredpassgo = (str(input('Continue? (y) ')))


    # current delay:
    # - program doesn;t run automatically anyways, issue with manipulating the GUI
    
    return mat

def deselectall():
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

def bakeprep(mat):
    # remind vars:
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader_image = nodes["Principled BSDF"]

    imagetexture_baked = nodes["Image Texture"]
    materialoutput = nodes["Material Output"]
    # change render engine to cycles
    bpy.data.scenes["Scene"].render.engine = 'CYCLES'
    # default: bpy.data.scenes["Scene"].render.engine = 'BLENDER_EEVEE'
    bpy.ops.image.new(name="bake_joined", width=4096, height=4096, color=(0, 0, 0, 1), alpha=False, generated_type='BLANK', float=False, use_stereo_3d=False, tiled=False)


    #imagetexture_baked = mat.node_tree.nodes["Image Texture"] #remind it
    imagetexture_baked.image = bpy.data.images['bake_joined']

    #create mesh
    # go to UV editor
    # select object (all), or joined object
    # press U
    deselectall()
    #bpy.context.workspace = bpy.data.workspaces['UV Editing']
    bpy.context.window.workspace = bpy.data.workspaces['UV Editing']
    bpy.ops.object.mode_set(mode='EDIT')
    #if bpy.context.workspace == bpy.data.workspaces['UV Editing']:
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.06, area_weight=0, correct_aspect=True, scale_to_bounds=False) # failing
    bpy.ops.image.save
    #else:
    #    print("Failed to active UV Editing window")

    bpy.context.window.workspace = bpy.data.workspaces['Shading']
    bpy.data.screens['Shading']
    bpy.ops.screen.area_split()
    #bpy.context.area.ui_type = 'UV'
    bpy.data.screens['Shading']
    deselectall()

    imagetexture_baked.select=True # select UV map node in shader
    bpy.context.view_layer.objects.active = bpy.data.objects['joinedObjects']
    bpy.data.objects['joinedObjects'].select_set(True)
    #bpy.ops.node.select(imagetexture_baked)

    
    scene.cycles.bake_type = 'DIFFUSE'
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.use_pass_color = True
    bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'

    #bpy.data.images['bake_joined'].select_set(True)

    #bpy.data.screens["Shading"].areas.items()
    #bpy.context.area.spaces.active
    '''
    bpy.ops.object.bake(type='DIFFUSE') # this line does literally nothing. sad.
    
    bpy.ops.object.bake(type='DIFFUSE', pass_filter=set(),
    filepath="", width=512, height=512, margin=16,
    margin_type='EXTEND', use_selected_to_active=False, max_ray_distance=0,
    cage_extrusion=0, cage_object="", normal_space='TANGENT',
    normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z', target='IMAGE_TEXTURES',
    save_mode='INTERNAL', use_clear=False, use_cage=False, use_split_materials=False, use_automatic_name=False, uv_layer="")
    
    bpy.ops.file.pack_all()

    links.new(shader_image.outputs[0], materialoutput.inputs[0])
    '''
    
    # This shit is broken. I'm giving up on complete automation. CB 6/10/2022.
    #bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    #bpy.context.area.ui_type = 'VIEW_3D'
    #bpy.context.space_data.shading.type = 'MATERIAL'
    # error: AttributeError: 'NoneType' object has no attribute 'ui_type'



    #bpy.context.view_layer.objects.active

    # detached gradient and single stems from joined STL objects. This is possible because the tallest STL object is the same height as the scale reference cube, and maxZ is a saved variable 
    




def plottext(i,inch,usednames):
    font_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
    font_curve.body = plotnames[i]

    (x,y,z) = (X[i], Y[i], 0)
    #font_obj = bpy.data.objects.new(name="Font Object", object_data=font_curve)
    font_obj = bpy.data.objects.new(name=plotnames[i], object_data=font_curve)
    loc = font_obj.location
    font_obj.location = loc + mathutils.Vector((x*inch,y*inch-0*inch,z*inch))
    #print(x)
    scale_plottext = 0.33
    font_obj.scale = mathutils.Vector((scale_plottext, scale_plottext, scale_plottext))
    bpy.context.scene.collection.objects.link(font_obj)

    scale_varietytext = 0.4


    if i==0:
        font_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
        font_curve.body = varietynames[i]
        usednames.append(varietynames[i])
        (x,y,z) = (X[i], Y[i], 0)
        font_obj = bpy.data.objects.new(name=varietynames[i], object_data=font_curve)
        loc = font_obj.location
        font_obj.location = loc + mathutils.Vector((x*inch,y*inch-19*inch,z*inch))
        font_obj.scale = mathutils.Vector((scale_varietytext,scale_varietytext,scale_varietytext))
        bpy.context.scene.collection.objects.link(font_obj)
        
    elif varietynames[i]!=varietynames[i-1] and not(usednames.__contains__(varietynames[i])):
        usednames.append(varietynames[i])
        font_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
        font_curve.body = varietynames[i]
        (x,y,z) = (X[i], Y[i], 0)
        font_obj = bpy.data.objects.new(name=varietynames[i], object_data=font_curve)
        loc = font_obj.location
        font_obj.location = loc + mathutils.Vector((x*inch,y*inch-19*inch,z*inch))
        font_obj.scale = mathutils.Vector((scale_varietytext, scale_varietytext, scale_varietytext))
        bpy.context.scene.collection.objects.link(font_obj)

    return usednames   
    

def scaletext(i,inch):
    font_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
    font_curve.body = str(i)

    (x,y,z) = (-5, 0, i)
    #font_obj = bpy.data.objects.new(name="Font Object", object_data=font_curve)
    font_obj = bpy.data.objects.new(name=("scale"+str(i)), object_data=font_curve)
    loc = font_obj.location
    font_obj.location = loc + mathutils.Vector((x*inch,y*inch-0*inch,z*inch))
    font_obj.rotation_euler = mathutils.Euler((3.141592/2,0,0))
    font_obj.scale = mathutils.Vector((0.1, 0.1, 0.1))
    bpy.context.scene.collection.objects.link(font_obj)
    font_curve.extrude = 1.3


def scaletitle(axis,dimension,inch):
    font_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
    font_curve.body = (axis+" "+dimension)

    (x,y,z) = (-10, 0, 0)
    #font_obj = bpy.data.objects.new(name="Font Object", object_data=font_curve)
    font_obj = bpy.data.objects.new(name=("scale"+str(i)), object_data=font_curve)
    loc = font_obj.location
    font_obj.location = loc + mathutils.Vector((x*inch,y*inch-0*inch,z*inch))
    font_obj.rotation_euler = mathutils.Euler((3.141592/2,-3.141592/2,0))
    font_obj.scale = mathutils.Vector((0.2, 0.2, 0.2))
    bpy.context.scene.collection.objects.link(font_obj)
    font_curve.extrude = 0.2
    
## Main script
i=0
#maxZ = DoubleVar()
#maxZ.set(0)
#global maxZ
maxZ = float(0.01)
objectnames = []
for filename in filenames_long:
    
    bpy.ops.import_mesh.stl(filepath=filename) ##import

    objectname = os.path.split(filename)
    objectname = objectname[-1]
    len_objectname = len(objectname)
    objectname = objectname[:len_objectname - 4] 
    obj = bpy.data.objects[objectname]
    objectnames.append(objectname)
    obj.select_set(True)   ## set the object
    
    objZ = bpy.context.object.dimensions.z*5
    maxZ = scale(obj,maxZ,objZ,inch)
    
    move(obj,i,inch)

    if showStems == "y":
        stems(i,inch)

    i+=1

obj = bpy.data.objects['Cube']
obj.select_set(True)
offset = 0
obj.scale = [4*inch, 4*inch, (maxZ/2+offset)*inch] #scale to improve color gradient, drop below z=0 plane
obj.location = mathutils.Vector((-20*inch,0,(maxZ/2-offset)*inch)) # was (-4, 0, etc)

for obj in bpy.data.collections['Collection'].all_objects:
    obj.select_set(True)

#bpy.data.objects['Cube'].select_set(False)
bpy.ops.object.join()
bpy.context.object.name = "joinedObjects"

# Shading
mat = color(bpy.context.object) #

# Seek user input
# this doesn't work like i want it to.
#mat = seekUserInput_colorGradient(mat)

# Bake mesh to texture
bakeprep(mat)

# Names
i=0  
# objectname = "fonts"
# obj = bpy.data.objects[objectname]
# obj.select_set(True)   ## set the object

usednames = []
for objectname in objectnames:
    usednames = plottext(i,inch,usednames)
    i+=1
#print("usednames = ")
#print(usednames)


# Add title and reference number to color gradient and to distance traveled
#axis = "EI"
#dimension = "(lb*in^2)"
scaletitle(axis,dimension,inch)
scaleref_doubledigits = [10,20,30,40,50,60,70,80,90]
scaleref_singledigits = [1,2,3,4,5,6,7,8,9,10]
if maxZ >= 10:
    scaleref = scaleref_doubledigits
elif maxZ < 10:
    scaleref = scaleref_singledigits
i=0
while scaleref[i] < maxZ:
    scaletext(scaleref[i],inch)
    i+=1
scaletext(round(maxZ,2),inch)


print ("\n")
print("INSTRUCTIONS:")
print("Go to UV Editor, rather than file browser")
print("Select bake_joined.png in both the UV Editor and the Image Editor.")
print("Create a Python console instance.")
print("Fiddle with the number for tuneColorGradient, through a Python console, or in Shading > Material nodes > Mapping > Scale > Z")
print("Ensure that the Scale node is selected, as a target for the bake.")
print("Bake! Manually or by pasting code, shown below.")
print("Save the image. I say again: Save. The. Image. Use the default filename, bake_joined.png")
print("Copy and paste the code below to export a FBX file.")

print ("\n")
print("#COPY AND PASTE THIS INTO THE BLENDER PYTHON CONSOLE, FIRST:")
print("exportfilename = "+ "\"" + exportfilename + "\"")
print("savepngname = "+ "\"" + savepngname + "\"")
print("mat = bpy.data.materials.get('colorGradient')# clarify material reference jargon")
print("links = mat.node_tree.links")
print("nodes = mat.node_tree.nodes")
print("shader_image = nodes['Principled BSDF']")
print("materialoutput = nodes['Material Output']")
print("mapping = nodes['Mapping']")
print("import mathutils")
print ("\n")

print("#COPY AND PASTE THIS INTO THE BLENDER PYTHON CONSOLE, TO ALTER COLOR GRADIENT:")
print("tuneColorGradient = " + str(tuneColorGradient))
print("mapping.inputs[3].default_value = mathutils.Vector((0.0, 0.0, tuneColorGradient))")
print ("\n")

print("#BAKE MANUALLY TO ENJOY A LOADING BAR, OR YOU CAN PASTE THIS LINE IF YOU DON'T REMEMBER HOW TO BAKE:")
print("#This will not work if you have not selected the bake_joined image node in the colorGradient texture material.")
print("bpy.ops.object.bake(type='DIFFUSE')")
print ("\n")

print("#IF YOU MESS UP THE BAKE, PASTE THIS BEFORE TRYING AGAIN:")
print("shader = nodes['Diffuse BSDF']")
print("links.new(shader.outputs[0], materialoutput.inputs[0])")
print("bpy.context.scene.render.engine = 'CYCLES' # change back to EEVEE")
print ("\n")

print("#SAVE THE IMAGE")
print("\n")

print("#SELECT bake_joined NODE")
print("\n")


print("#COPY AND PASTE THIS INTO THE BLENDER PYTHON CONSOLE, AFTER BAKING:")
print("bpy.context.scene.render.engine = 'BLENDER_EEVEE' # change back to EEVEE")
print("links.new(shader_image.outputs[0], materialoutput.inputs[0]) # change link to show baked texture, instead of procedural texture")
print("bpy.ops.file.pack_all() # pack image")
print("# export")
print("bpy.ops.export_scene.fbx(filepath=exportfilename, check_existing=True, filter_glob='*.fbx', use_selection=False, use_active_collection=False, global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_space_transform=True, bake_space_transform=False, object_types={'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'}, use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='OFF', use_subsurf=False, use_mesh_edges=False, use_tspace=False, use_custom_props=False, add_leaf_bones=True, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_step=1, bake_anim_simplify_factor=1, path_mode='COPY', embed_textures=True, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True, axis_forward='Y', axis_up='Z')")
print ("\n")

print("#IF YOU GET THE ERROR 'No such file or directory' AND/OR YOUR EXPORT DOES NOT HAVE COLOR, MAKE SURE TO SAVE THE IMAGE, IN THE UV FRAME.")
print("\n")

print("#If this is the last line in CMD, the file hasn't baked yet.")
print("\n")

'''
## Dev:
# Add underline to color gradient numbers # low priority
# Add material for text color # secondary priority
# Add individual stems # high priority
# Texture bake automatically # highest priority
# Export automatically # high priority
# change variable listing and location to be based on directory location and text pattern, rather than manually pasting lists from spreadsheet # high priority

# learn to group objects by name, to exclude certain objects: Group all SOCEM with a yardstick, and then all stems with a yardstick: If you do this, will they correlate?

# auto group bsed on plotheights spreadsheet, to reference variety names.
# Have a second script to copy and paste and finish the job of bakig and exporting, once window is changed.
'''
