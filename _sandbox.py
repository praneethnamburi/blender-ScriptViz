"""Sandbox. Not involving blender."""
#%%
import os
os.chdir('D:\\Workspace\\blenderPython')

#%%
import numpy as np
def dummyFunc(*args, **kwargs):
    if not args and not kwargs:
        raise TypeError("At least one input argument is required") # needs at least one input argument
    if not args and kwargs:
        if len(kwargs) != 3:
            raise ValueError("Supply exactly 3 keyword arguments: name, v, f")
        else: # check for the keyword argument values
            if False not in [k in b for k in ['name', 'v', 'f']]:
                pass # make mesh from python data
                # msh(name=name, v=vertices, f=faces)
            else:
                raise ValueError("Acceptable keywords: (name, v, f)")
    if args and not kwargs:
        if len(args) == 3 and isinstance(args[0], str):
            pass # make mesh from python data assuming args[0] is name, args[1] is v and args[2] is f
            # msh(name, v, f)
        elif len(args) == 2:
            if isinstance(args[0], str) and isinstance(args[1], str):
                if args[0].lower()[-4:] == '.stl':
                    pass # msh(stlfile, 'awesomeMesh')
                elif args[0].lower()[-4:] == '.stl':
                    pass # msh('awesomeMesh', stlfile)
                else:
                    raise ValueError("Two string args. One of them must be the name of an stl file.")
            else:
                pass # msh(v, f)
        elif len(args) == 1:
            if isinstance(args[0], str):
                if args[0].lower()[-4:] == '.stl':
                    pass # load the STL file with the mesh name being the loaded file name
                    # msh(stlfile)
                else:
                    pass # name of a mesh in blender
                    # msh(blender mesh name)
                    # check if the string is the name of a mesh in blender
            elif isinstance(args[0], bpy.types.Mesh):
                pass # msh(blender mesh object)
            elif isinstance(args[0], bpy.types.Object):
                pass # msh(blender obj name) # make sure it is an object containing only one mesh
            else:
                raise ValueError("One arg detected. It must be a string, a blender mesh, or a blender object")
        else:
            raise TypeError("Wrong number of input arguments.")
    if args and kwargs:
        if len(args) == 1 and isinstance(args[0], str) and len(kwargs) == 1 and 'name' in kwargs:
            pass # msh(stlfile, name='awesomeMesh')
        elif len(args) == 2 and len(kwargs) == 1 and 'name' in kwargs:
            pass # msh(v, f, name='awesomeMesh')
        else:
            raise TypeError("Wrong number of input arguments")

# Goal of the dispatcher is to return a blender object!

    # make a mesh from an STL file
    # msh(stlfile, 'awesomeMesh')       -> loadSTL([stlFile]), rename mesh to awesomeMesh
    # msh('awesomeMesh', stlfile)       -> loadSTL([stlFile]), rename mesh to awesomeMesh
    # msh(stlfile)                      -> loadSTL([stlFile])
    # msh(stlfile, name='awesomeMesh')  -> loadSTL([stlFile]), rename mesh to awesomeMesh

    # # make a mesh from python data
    # msh(name=name, v=vertices, f=faces) -> makeMesh(name, v, f)
    # msh(name, v, f)                     -> makeMesh(name, v, f)
    # msh(v, f, name='awesomeMesh')       -> makeMesh(name, v, f)
    # msh(v, f)                           -> makeMesh('autoMshName', v, f)

    # # get a mesh from the blender environment
    # msh(blender mesh name)   -> return mesh object
    # msh(blender mesh object) -> do nothing
    # msh(blender obj name)

# addonPath = os.path.realpath(r'C:\blender\2.80.0\2.80\scripts\addons')
# if addonPath not in sys.path:
#     sys.path.append(addonPath)
# from io_mesh_stl.stl_utils import read_stl

# objName = bpy.path.display_name(os.path.basename(path))
# tris, tri_nors, pts = stl_utils.read_stl(path)
# tri_nors = tri_nors if self.use_facet_normal else None
# blender_utils.create_and_link_mesh(objName, tris, tri_nors, pts, global_matrix)

# TODO: Put this in bpn (make meshes from stl, find meshes from blender workspace, create meshes from faces and vertices)
# # How to make a mesh using vertices and triangles
# tris, tri_nors, pts = read_stl(eyebar_path)
# def makeMesh(name, v, f):
#     mesh = bpy.data.meshes.new(name)
#     mesh.from_pydata(v, [], f)
#     mesh.update()

#     obj = bpy.data.objects.new(name, mesh)
#     bpy.context.collection.objects.link(obj)
#     bpy.context.view_layer.objects.active = obj
#     obj.select_set(True)
#     return mesh

# mBpy = makeMesh('eyeBar', pts, tris)