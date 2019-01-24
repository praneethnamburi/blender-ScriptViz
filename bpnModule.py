import os
import errno
import numpy as np
from mathutils import Vector #pylint: disable=import-error
import sys
import glob

def raiseNotFoundError(thisDirFiles):
    if isinstance(thisDirFiles, str):
        thisDirFiles = [thisDirFiles]
    for dirFile in thisDirFiles:
        if not os.path.exists(dirFile):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), dirFile)

def checkIfOutputExists(func):
    def checkedFunction(*args, **kwargs):
        output = func(*args, **kwargs)
        raiseNotFoundError(output)
        return output
    return checkedFunction

@checkIfOutputExists
def getFileName_full(fPath, fName):
    fullName = os.path.join(os.path.normpath(fPath), fName)
    return fullName

@checkIfOutputExists
def marmosetAtlasPath(src='bma'):
    if src=='bma':
        if sys.platform == 'linux':
            fPath = "/media/praneeth/Reservoir/GDrive Columbia/issalab_data/Marmoset brain/Woodward segmentation/meshes/"
        else:
            fPath = "D:\\GDrive Columbia\\issalab_data\\Marmoset brain\\Woodward segmentation\\meshes"
    return fPath

# function syntax for making a decorator
def baseNames(func):
    def baseModFunc(*args, **kwargs):
        # input validation code goes here
        fOut = func(*args, **kwargs) #commentretyg
        # output validation and modification code goes here
        fOutBase = [os.path.basename(k) for k in fOut]
        return fOutBase
    return baseModFunc

@baseNames
@checkIfOutputExists
def getMeshNames(fPath=marmosetAtlasPath(), searchStr='*smooth*.stl'):
    mshNames = glob.glob(fPath + searchStr)
    return mshNames

class bpnClass:
    """
    Place everything that uses bpy here. This was the best way I could think of
    to extend blender's functionality without unnecessarily passing bpy to every 
    function that I call.
    Use this class by instantiating a bpn object like so in the blender python console:
    bpn = bpnModule.bpnClass(bpy) # pass the bpy module (object)
    """
    def __init__(self, bpyLive):
        self.bpy = bpyLive

    # Make some demo functions here! 
    # Animating DNA, 
    def demo_animateDNA(self):
        objList, _ = self.plotDNA()
        self.animateObj_whole(objList, np.arange(0, 101, 20))
    # meshDance
    # brainExplosion

    # Blender usefulness exercise #1 - Plotting
    # Plotting two strands of DNA
    def plotDNA(self):
        """
        Plot DNA. Demonstrates how to plot in Blender.
        Use: objList, mshList = bpn.pn_plotDNA()
        """
        x = np.linspace(0, 2.0*np.pi, 100)
        y = lambda x, offset: np.sin(x+offset)
        h1, m1 = self.plot(y(x, np.pi/2), y(x, 0), x)
        h2, m2 = self.plot(y(x, -np.pi/2), -y(x, 0), x)
        return [h1, h2], [m1, m2] # objList, mshList
    
    def plot(self, x, y, z=0):
        mshName = 'autoMshName'
        # create a mesh
        msh = self.genMesh(mshName, x, y, z)
        # instantiate an object
        obj = self.genObj(msh)
        return obj, msh

    def genMesh(self, mshName, xVals, yVals, zVals=None):
        """Generates a mesh for plotting."""
        n = np.size(xVals)
        if zVals is None:
            zVals = np.zeros(n)
        msh = self.bpy.data.meshes.new(mshName)
        msh.vertices.add(n)
        msh.edges.add(n-1)
        for i in range(n):
            msh.vertices[i].co = (xVals[i], yVals[i], zVals[i])
            if i < n-1:
                msh.edges[i].vertices = (i, i+1)
        return msh

    def genObj(self, msh, name='autoObjName', location=(0.0,0.0,0.0)):
        """Generates an object fraom a mesh and attaches it to the current scene."""
        obj = self.bpy.data.objects.new(name, msh)
        # put that object in the scene
        obj.location = Vector(location)
        self.bpy.context.scene.collection.objects.link(obj)
        return obj

    # Blender usefulness exercise #2 - animation
    # Animate the two strands of DNA
    def animateObj_whole(self, objList, frameList): # skeleton to transform the entire object
        scn = self.bpy.context.scene # assuming there is only one scene
        scn.frame_end = frameList[-1]+1 # assuming frameList is monotonically increasing
        for frameNum in frameList:
            scn.frame_set(frameNum+1) # because keyframes are 1-indexed in Blender
            for obj in objList:
                obj.rotation_euler = Vector((0, 0, 2*np.pi*frameNum/frameList[-1]))
                obj.keyframe_insert(data_path='rotation_euler', index=-1)

    # Blender usefulness exercise #3 - importing marmoset brain meshes
    def loadSTL(self, fPath=marmosetAtlasPath(), searchStr='*smooth*.stl'):
        fNames=getMeshNames(fPath, searchStr)
        for fName in fNames:
            self.bpy.ops.import_mesh.stl(filepath=getFileName_full(fPath, fName))

    def getMshCenter(self, msh):
        msh = self.chkType(msh, 'Mesh')

    # Blender usefulness exercise #4 - basic mesh access and manipulation
    def getMshCoords(self, msh):
        msh = self.chkType(msh, 'Mesh')
        coords = np.array([v.co for v in msh.vertices])
        return coords

    def setMshCoords(self, msh, coords):
        """
        Set vertex positions of a mesh using a numpy array of size nVertices x 3.
        Note that this will only work when blender 3D viewport is in object mode.
        Therefore, this code will temporarily change the 3D viewport mode to Object,
        change the mesh coordinates and switch it back.
        """
        msh = self.chkType(msh, 'Mesh')
        modeChangeFlag = False
        if not self.bpy.context.object.mode == 'OBJECT':
            current_mode = self.bpy.context.object.mode
            modeChangeFlag = True
            self.bpy.ops.object.mode_set(mode='OBJECT')

        for vertexCount, vertex in enumerate(msh.vertices):
            vertex.co = Vector(coords[vertexCount, :])

        if modeChangeFlag:
            self.bpy.ops.object.mode_set(mode=current_mode)

    def getMesh(self, msh, mshProperty=None):
        """
        Return a mesh given its name.
        Given an object (or its name), return its mesh.
        """        
        return self.chkType(msh, 'Mesh')
    
    def getObject(self, obj):
        """Return an object given its name."""
        return self.chkType(obj, 'Object')
        
    def chkType(self, inp, inpType='Mesh'):
        """
        Check if a given input is a mesh or an object.
        inpType is either 'Mesh' or 'Object'
        If inp is the name of a mesh/object, then find and return the appropriate python object.
        If you requested a mesh but gave an object name, then return the mesh.
        If you input an object, but are looking for a mesh, return the associated mesh.
        """
        if inpType == 'Mesh':
            inpType_bpyData = 'meshes'
        elif inpType == 'Object':
            inpType_bpyData = 'objects'
        if isinstance(inp, str):
            if inp in [k.name for k in getattr(self.bpy.data, inpType_bpyData)]:
                return getattr(self.bpy.data, inpType_bpyData)[inp]
            elif (inpType == 'Mesh') and (inp in [k.name for k in self.bpy.data.objects]):
                # if you requested a mesh but gave an object name, then return the mesh
                return self.bpy.data.objects[inp].data
            else:
                raise ValueError("Could not find " + inp + " of type " + inpType)
        if isinstance(inp, self.bpy.types.Object) and inpType=='Mesh':
            return inp.data # in blender, obj.data points to the mesh corresponding to that object
        if not isinstance(inp, getattr(self.bpy.types, inpType)):
            # this will only happen if you didn't pass a mesh, object, or an appropriate string
            raise TypeError("Expected input of type bpy.types." + inpType + ", got, " + str(type(inp)) + " instead")
        return inp

    # Blender usefulness exercise #5 - add primitives
    def addPrimitive(self, type='monkey', location=(1.0, 3.0, 5.0)):
        """
        Add a primitive at a given location - just simplifies syntax
        type can be circle, cone, cube, cylinder, grid, ico_sphere, uv_sphere,
        monkey, plane, torus
        Adding a primitive while in edit mode will add the primitive to the
        mesh that is being edited in mesh mode! This means that you can inherit
        animations (and perhaps modifiers) by adding to a mesh!
        """
        funcName = 'primitive_'+type+'_add'
        if hasattr(self.bpy.ops.mesh, funcName):
            getattr(self.bpy.ops.mesh, funcName)(location=location)
        else:
            raise ValueError(f"{type} is not a valid argument")