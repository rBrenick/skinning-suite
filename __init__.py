bl_info = {
    "name": "Skinning Suite",
    "author": "Richard Brenick",
    "version": (1, 2),
    "blender": (2, 80, 0),
    "location": "Weight Paint - Select",
    "description": "",
    "warning": "",
    "doc_url": "",
    "category": "Rigging",
}

from . import skinning_suite

def register():
    skinning_suite.register()

def unregister():
    skinning_suite.unregister()
