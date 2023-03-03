import os
import json

import bpy

bl_info = {
    "name": "Skinning Suite",
    "author": "Richard Brenick",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Weight Paint - Select",
    "description": "",
    "warning": "",
    "doc_url": "",
    "category": "Rigging",
}

# sorry mac/linux users
CLIPBOARD_WEIGHTS_JSON_PATH = r"C:/tmp/blender_skinning_clipboard.json"
SELECTION_SAVE_JSON = "c:/tmp/saved_selection_blender.json"
if not os.path.exists(os.path.dirname(SELECTION_SAVE_JSON)):
    os.makedirs(os.path.dirname(SELECTION_SAVE_JSON))



class RemoveUnusedVertexGroups(bpy.types.Operator):
    bl_idname = "paint.skinsuite_remove_unused_vertex_groups"
    bl_label = "Remove Unused Influences"
    bl_description = "Remove vertex groups from object that don't have any skinning"
    bl_options = {'REGISTER', 'UNDO'}

    margin: bpy.props.FloatProperty(
        name="Margin", 
        default=0.0001,
        precision=4,
        min=0.0,
        max=1.0,
        )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "margin")

    def invoke(self, context: 'Context', event: 'Event'):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object
        
        used_groups = []
        for vg in ob.vertex_groups:
            for vertex in ob.data.vertices:
                try:
                    weight = vg.weight(vertex.index)
                except Exception as e:
                    weight = 0
                
                if weight > self.margin:
                    # a weight value was found for this vertex group, skip to next group
                    used_groups.append(vg)
                    break
        
        unused_groups = [vg.name for vg in ob.vertex_groups if vg not in used_groups]

        # remove groups
        for unused_group in unused_groups:
            ob.vertex_groups.remove(ob.vertex_groups.get(unused_group))

        bpy.ops.object.vertex_group_normalize_all()

        return {"FINISHED"}

"""
class SelectInfluencedVertices(bpy.types.Operator):
    bl_idname = "paint.skinsuite_select_influenced_vertices"
    bl_label = "Select Influenced Verts"
    bl_description = ""

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object

        vertex_groups = ob.vertex_groups  # type: bpy.types.VertexGroups

        ob.data.use_paint_mask_vertex = True
        bpy.ops.paint.vert_select_all(action='DESELECT')

        for vtx in ob.data.vertices:  # type: bpy.types.MeshVertex
            try:
                weight = vertex_groups.active.weight(vtx.index)
            except Exception as e:
                weight = 0

            if weight > 0:
                vtx.select = True

        return {"FINISHED"}

"""

class SelectVerticesInWeightRange(bpy.types.Operator):
    bl_idname = "paint.skinsuite_select_vertices_in_weight_range"
    bl_label = "Select Vertices in Weight Range"
    bl_description = "Find vertices that have weighting within the defined limits"
    bl_options = {'REGISTER', 'UNDO'}

    def _update_func(self, context):
        SelectVerticesInWeightRange.select_vertices_in_weight_range(
            SelectVerticesInWeightRange, 
            context, 
            lower_limit=self.lower_limit,
            upper_limit=self.upper_limit,
            )
    
    lower_limit: bpy.props.FloatProperty(
        name="Lower Limit", 
        default=0.0,
        soft_min=0.0,
        soft_max=1.0,
        precision=6,
        update=_update_func,
        )
    
    upper_limit: bpy.props.FloatProperty(
        name="Upper Limit", 
        default=1.0,
        soft_min=0.0,
        soft_max=1.0,
        precision=6,
        update=_update_func,
        )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "upper_limit")
        layout.prop(self, "lower_limit")

    def invoke(self, context, event):
        self.lower_limit = 0.0
        self.upper_limit = 1.0

        self.select_vertices_in_weight_range(
            context, 
            lower_limit=self.lower_limit,
            upper_limit=self.upper_limit,
        )
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        self.select_vertices_in_weight_range(
            context, 
            lower_limit=self.lower_limit,
            upper_limit=self.upper_limit,
        )
        return {"FINISHED"}
    
    def select_vertices_in_weight_range(self, context, lower_limit=0, upper_limit=1):
        ob = context.active_object  # type: bpy.types.Object
        vertex_groups = ob.vertex_groups  # type: bpy.types.VertexGroups
        ob.data.use_paint_mask_vertex = True

        for vtx in ob.data.vertices:  # type: bpy.types.MeshVertex
            try:
                weight = vertex_groups.active.weight(vtx.index)
            except Exception as e:
                weight = 0

            if weight > lower_limit and weight <= upper_limit:
                vtx.select = True
            else:
                vtx.select = False


class SelectWeightIslandsInRange(bpy.types.Operator):
    bl_idname = "paint.skinsuite_select_weight_islands_in_range"
    bl_label = "Select Weight Islands in Range"
    bl_description = "Find weight islands, and select those where the average weighting is between the limit values"
    bl_options = {'REGISTER', 'UNDO'}

    def _update_func(self, context):
        SelectWeightIslandsInRange.select_islands_in_range(
            SelectWeightIslandsInRange, 
            context, 
            lower_limit=self.lower_limit,
            upper_limit=self.upper_limit,
            )

    lower_limit: bpy.props.FloatProperty(
        name="Lower Limit", 
        default=0.0,
        soft_min=0.0,
        soft_max=1.0,
        precision=6,
        update=_update_func,
        )

    upper_limit: bpy.props.FloatProperty(
        name="Upper Limit", 
        default=0.1,
        soft_min=0.0,
        soft_max=1.0,
        precision=6,
        update=_update_func,
        )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "upper_limit")
        layout.prop(self, "lower_limit")
    
    def invoke(self, context, event):
        self.lower_limit = 0.0
        self.upper_limit = 0.1

        self._get_island_data(context)
        self.select_islands_in_range(
            context, 
            lower_limit=self.lower_limit,
            upper_limit=self.upper_limit,
        )
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        self.select_islands_in_range(
            context, 
            lower_limit=self.lower_limit,
            upper_limit=self.upper_limit,
        )
        return {"FINISHED"}

    def _get_island_data(self, context):
        ob = context.active_object  # type: bpy.types.Object
        active_vert_group = ob.vertex_groups.active  # type: bpy.types.VertexGroup
        
        # find all vertices with weighting
        weighting = {}
        for vtx in ob.data.vertices:  # type: bpy.types.MeshVertex
            try:
                weight = active_vert_group.weight(vtx.index)
            except Exception as e:
                weight = 0

            if weight > 0:
                weighting[vtx.index] = weight
                
        # make_edge_connection map
        vert_edge_map = {}
        for edge in ob.data.edges:
            edge = edge  # type: bpy.types.MeshEdge
            for vert_id in edge.vertices:
                connected_edges = vert_edge_map.get(vert_id, [])
                connected_edges.extend(edge.vertices)
                vert_edge_map[vert_id] = connected_edges

        # sort by highest weighted vert
        highest_inf = sorted(weighting, key=weighting.get, reverse=True)
        
        islands = []
        visited_verts = []
        for vert_id in highest_inf:

            # we've searched all the verts, exit search
            if len(visited_verts) == len(highest_inf):
                break

            if vert_id in visited_verts:
                continue

            search_list = [vert_id]

            while True:

                # find connected vertices that have weighting on them
                good_roots = []

                for search_id in search_list:
                    for connected_vert_id in vert_edge_map.get(search_id):

                        # skip verts that have already been found
                        if connected_vert_id in search_list:
                            continue

                        if connected_vert_id in good_roots:
                            continue

                        if connected_vert_id in highest_inf:
                            good_roots.append(connected_vert_id)
                
                # no weighted verts connected to these verts, exit while-loop
                if len(good_roots) == 0:
                    break

                search_list.extend(good_roots)
            
            visited_verts.extend(search_list)
            islands.append(search_list)
        
        bpy.types.WindowManager.SKINSUITE_VERT_WEIGHT_ISLAND_DATA = {
            "islands": islands,
            "weighting": weighting,
            }

    def select_islands_in_range(self, context, lower_limit=0.0, upper_limit=0.1):
        ob = context.active_object  # type: bpy.types.Object
        islands = bpy.types.WindowManager.SKINSUITE_VERT_WEIGHT_ISLAND_DATA.get("islands")
        weighting = bpy.types.WindowManager.SKINSUITE_VERT_WEIGHT_ISLAND_DATA.get("weighting")

        suspect_islands = []
        for island in islands:
            weight_values = []
            for vert_id in island:
                weight_values.append(weighting.get(vert_id))

            average_weight = sum(weight_values) / len(weight_values)
            if average_weight > lower_limit and average_weight <= upper_limit:
                suspect_islands.append(island)
        
        # select the verts
        bpy.ops.paint.vert_select_all(action='DESELECT')
        ob.data.use_paint_mask_vertex = True
        for island in suspect_islands:
            for vert_id in island:
                vtx = ob.data.vertices[vert_id]
                vtx.select = True


class SelectMoreComponents(bpy.types.Operator):
    bl_idname = "paint.skinsuite_select_more_verts"
    bl_label = "Select More"
    bl_description = "Grow vertex selection via edge connections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object

        # make_edge_connection
        vert_edge_map = {}
        for edge in ob.data.edges:
            edge = edge  # type: bpy.types.MeshEdge
            for vert_id in edge.vertices:
                connected_edges = vert_edge_map.get(vert_id, [])
                connected_edges.append(edge)
                vert_edge_map[vert_id] = connected_edges

        indices_to_select = []
        for vtx in ob.data.vertices:
            vtx = vtx  # type: bpy.types.MeshVertex
            
            if vtx.select:
                for edge in vert_edge_map.get(vtx.index, []):
                    indices_to_select.extend(edge.vertices)
        
        indices_to_select = list(set(indices_to_select))
        for index_to_select in indices_to_select:
            ob.data.vertices[index_to_select].select = True

        return {"FINISHED"}


class SelectLessComponents(bpy.types.Operator):
    bl_idname = "paint.skinsuite_select_less_verts"
    bl_label = "Select Less"
    bl_description = "Shrink vertex selection via edge connections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object

        # make_edge_connection map
        vert_edge_map = {}
        for edge in ob.data.edges:
            edge = edge  # type: bpy.types.MeshEdge
            for vert_id in edge.vertices:
                connected_edges = vert_edge_map.get(vert_id, [])
                connected_edges.append(edge)
                vert_edge_map[vert_id] = connected_edges

        selected_verts = []
        for vtx in ob.data.vertices:
            if vtx.select:
                selected_verts.append(vtx.index)

        # find edges where we only have one vert selected
        verts_to_deselect = []
        for vert_id in selected_verts:
            for edge in vert_edge_map.get(vert_id):
                edge_verts_in_sel = len([v for v in edge.vertices if v in selected_verts])
                if edge_verts_in_sel == 1:
                    verts_to_deselect.extend(edge.vertices)
        
        verts_to_deselect = list(set(verts_to_deselect))

        for index_to_select in verts_to_deselect:
            ob.data.vertices[index_to_select].select = False
            
        return {"FINISHED"}


class RemoveWeightingOnSelected(bpy.types.Operator):
    bl_idname = "paint.skinsuite_remove_weighting_on_selected"
    bl_label = "Apply 0 Weights"
    bl_description = "Sets 0 influence on the selected group on the selected verts"

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object
        ob.data.use_paint_mask_vertex = True
        active_vert_group = ob.vertex_groups.active  # type: bpy.types.VertexGroup

        for vtx in ob.data.vertices:  # type: bpy.types.MeshVertex
            vtx = vtx # type: bpy.types.MeshVertex
            if not vtx.select:
                continue

            weighting = {}
            for vtx_grp in vtx.groups:
                vtx_grp = vtx_grp # type: bpy.types.VertexGroupElement

                if vtx_grp.group == active_vert_group.index:
                    weight_val = 0.0
                else:
                    weight_val = vtx_grp.weight
                
                if weight_val:
                    weighting[vtx_grp] = weight_val

                # set all the weighting to zero (since we'll apply normalized weights)
                vtx_grp.weight = 0.0

            un_normalized_max = sum(weighting.values())
            normalized_weights = {k: v / un_normalized_max for k, v in weighting.items()}
            # sum(normalized_weights.values())  # should be 1.0

            # apply normalized weights on selected verts
            for vtx_grp, target_weight in normalized_weights.items():
                vtx_grp.weight = target_weight

        return {"FINISHED"}


class LinkArmatureToCurrentScene(bpy.types.Operator):
    bl_idname = "paint.skinsuite_link_armature_to_scene"
    bl_label = "Link Armature To Scene"
    bl_description = "Find the armature attached to the active object, and link it to the current scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object

        armature_modifiers = [mod for mod in ob.modifiers if mod.type == "ARMATURE"]
        for armature_modifier in armature_modifiers:
            armature_obj = armature_modifier.object

            if armature_obj and not bpy.context.scene.objects.get(armature_obj.name):
                bpy.context.scene.collection.objects.link(armature_obj)

        return {"FINISHED"}


class SaveSelection(bpy.types.Operator):
    bl_idname = "paint.skinsuite_save_selection"
    bl_label = "Save Selection"
    bl_description = "Save the selected vertex ids to a file"

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object

        selected_verts = []
        for vtx in ob.data.vertices:
            vtx = vtx  # type: bpy.types.MeshVertex
            
            if vtx.select:
                selected_verts.append(vtx.index)

        with open(SELECTION_SAVE_JSON, "w") as fp:
            json.dump(selected_verts, fp, indent=2)

        return {"FINISHED"}


class SelectSavedSelection(bpy.types.Operator):
    bl_idname = "paint.skinsuite_select_saved_selection"
    bl_label = "Select Saved"
    bl_description = "Select the saved vertex ids"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object

        with open(SELECTION_SAVE_JSON, "r") as fp:
            verts_to_sel = json.load(fp)

        for vtx in ob.data.vertices:
            vtx = vtx  # type: bpy.types.MeshVertex
            
            if vtx.index in verts_to_sel:
                vtx.select = True

        return {"FINISHED"}


class DeSelectSavedSelection(bpy.types.Operator):
    bl_idname = "paint.skinsuite_deselect_saved_selection"
    bl_label = "DeSelect Saved"
    bl_description = "Deselect the saved vertex ids"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object

        with open(SELECTION_SAVE_JSON, "r") as fp:
            verts_to_sel = json.load(fp)

        for vtx in ob.data.vertices:
            vtx = vtx  # type: bpy.types.MeshVertex
            
            if vtx.index in verts_to_sel:
                vtx.select = False

        return {"FINISHED"}


class SelectUnNormalizedVertices(bpy.types.Operator):
    bl_idname = "paint.skinsuite_select_unnormalized_vertices"
    bl_label = "Select UnNormalized Verts"
    bl_description = "Find vertices where the total weight exceeds 1"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object

        ob.data.use_paint_mask_vertex = True
        bpy.ops.paint.vert_select_all(action='DESELECT')

        for vtx in ob.data.vertices:  # type: bpy.types.MeshVertex
            total_weight = 0
            for grp in vtx.groups:
                if 0:
                    grp = grp # type: bpy.types.VertexGroupElement
                total_weight += grp.weight

            if round(total_weight, 8) > 1:
                print(f"weight exceeds 1: {total_weight} - {vtx.index}")
                vtx.select = True

        return {"FINISHED"}


class CopySelectedVertexWeights(bpy.types.Operator):
    bl_idname = "paint.skinsuite_copy_selected_vertex_weights"
    bl_label = "Copy Selected Weights"
    bl_description = "Copy the average weighting of all selected vertices"

    def execute(self, context):
        ob = context.active_object  # type: bpy.types.Object

        max_influence = 8

        # get weighting data of all selected vertices
        weight_data = {}
        for vtx in ob.data.vertices: 
            if 0:
                vtx = vtx  # type: bpy.types.MeshVertex
            if not vtx.select:
                continue

            weight_data[vtx.index] = {}
            for grp in vtx.groups:
                if 0:
                    grp = grp # type: bpy.types.VertexGroupElement
                
                if grp.weight == 0:
                    continue

                vg_name = ob.vertex_groups[grp.group].name
                weight_data[vtx.index][vg_name] = grp.weight
        
        if not weight_data:
            self.report({'ERROR'}, "No weight data found in selection.")
            return {"FINISHED"}
    
        ###########################################
        # Calculate average weighting of all verts

        # sum up all weight data
        total_vals = {}
        for vtx_data in weight_data.values():
            for vg_name, weight_val in vtx_data.items():
                v = total_vals.get(vg_name, 0.0)
                v += weight_val
                total_vals[vg_name] = v

        # get most affecting bones
        most_vals = {k: v for k, v in sorted(total_vals.items(), key=lambda item: item[1])[-max_influence:]}
        total_weight = sum(most_vals.values())
        
        # average out the results from 0.0 to 1.0
        averaged = {}
        for k, v in most_vals.items():
            ratio = v / total_weight
            averaged[k] = ratio

        # make sure the weights make sense
        print(f"average weight sum: {sum(averaged.values())}")
        assert(round(sum(averaged.values()), 8) == 1)

        with open(CLIPBOARD_WEIGHTS_JSON_PATH, "w+") as fp:
            json.dump(averaged, fp)
        
        self.report({'INFO'}, f"Saved weights to: {CLIPBOARD_WEIGHTS_JSON_PATH}")
        return {"FINISHED"}


class PasteSelectedVertexWeights(bpy.types.Operator):
    bl_idname = "paint.skinsuite_paste_selected_vertex_weights"
    bl_label = "Paste Weights on Selected"
    bl_description = "Paste the copied weighting onto the selected verts, with a weighting slider"
    bl_options = {'REGISTER', 'UNDO'}

    def _update_func(self, context):
        PasteSelectedVertexWeights.set_weights_on_selected(
            PasteSelectedVertexWeights, 
            context, 
            paste_weight=self.paste_weight,
            )
    
    paste_weight: bpy.props.FloatProperty(
        name="Weight", 
        default=1.0,
        min=0.0,
        max=1.0,
        update=_update_func,
        )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "paste_weight")

    def invoke(self, context, event):
        self.store_selected_vert_data(context)
        self.set_weights_on_selected(context, paste_weight=self.paste_weight)
        return context.window_manager.invoke_props_dialog(self)

    def store_selected_vert_data(self, context):
        with open(CLIPBOARD_WEIGHTS_JSON_PATH, "r") as fp:
            json_data = json.load(fp)
        
        json_bones = json_data.keys()
        ob = context.active_object  # type: bpy.types.Object

        # get weight data
        sel_weight_data = {}
        for vtx in ob.data.vertices: 
            if 0:
                vtx = vtx  # type: bpy.types.MeshVertex

            if not vtx.select:
                continue
            
            sel_weight_data[vtx] = {}
            for grp in vtx.groups:
                vg_name = ob.vertex_groups[grp.group].name

                sel_weight_data[vtx][vg_name] = grp.weight
            
            # assign missing vertex groups
            missing_bones = [b for b in json_bones if b not in sel_weight_data[vtx].keys()]
            for missing_bone in missing_bones:
                v_group = ob.vertex_groups.get(missing_bone)
                if v_group is None:
                    v_group = ob.vertex_groups.new(name=missing_bone)

                # this can be optimized
                v_group.add([vtx.index], 0, 'REPLACE')

        bpy.types.WindowManager.SKINSUITE_COPY_PASTE_WEIGHT_DATA = {
            "sel": sel_weight_data,
            "json": json_data
            }

    def set_weights_on_selected(self, context, paste_weight=1.0):
        sel_weight_data = bpy.types.WindowManager.SKINSUITE_COPY_PASTE_WEIGHT_DATA.get("sel")
        json_weight_data = bpy.types.WindowManager.SKINSUITE_COPY_PASTE_WEIGHT_DATA.get("json")

        ob = context.active_object  # type: bpy.types.Object

        # blend in weights
        for vtx, weight_data in sel_weight_data.items(): 
            if 0:
                vtx = vtx  # type: bpy.types.MeshVertex
            
            for grp in vtx.groups:
                vg_name = ob.vertex_groups[grp.group].name
                json_weight = json_weight_data.get(vg_name)
                if json_weight is None:
                    continue
                
                pre_weight = weight_data.get(vg_name, 0)

                # blend in json
                new_val = lerp(pre_weight, json_weight, paste_weight)
                grp.weight = new_val
    

    def execute(self, context):
        self.set_weights_on_selected(context, paste_weight=self.paste_weight)
        bpy.ops.object.vertex_group_normalize_all()
        self.report({'INFO'}, f"Pasted weights from: {CLIPBOARD_WEIGHTS_JSON_PATH}")
        return {"FINISHED"}


def lerp(a, b, t):
    return a + (b - a) * t


class RENDER_PT_SkinSuiteVertexGroupTools(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    bl_idname = "DATA_PT_SkinSuiteVertexGroupTools"
    bl_category = 'SKM'
    bl_parent_id = 'DATA_PT_vertex_groups'
    bl_label = "Skinning Suite Tools"

    bl_options = {"HEADER_LAYOUT_EXPAND"}

    def draw(self, context):
        layout = self.layout
        copy_paste_row = layout.row()
        copy_paste_row.operator(CopySelectedVertexWeights.bl_idname)
        copy_paste_row.operator(PasteSelectedVertexWeights.bl_idname)
        layout.operator(RemoveUnusedVertexGroups.bl_idname)
        layout.operator(RemoveWeightingOnSelected.bl_idname)
        layout.operator(LinkArmatureToCurrentScene.bl_idname)
        layout.separator()
        layout.operator(SelectUnNormalizedVertices.bl_idname)
        layout.operator(SelectVerticesInWeightRange.bl_idname)
        layout.operator(SelectWeightIslandsInRange.bl_idname)
        layout.separator()
        select_row = layout.row()
        select_row.operator(SelectMoreComponents.bl_idname)
        select_row.operator(SelectLessComponents.bl_idname)
        saved_select_row = layout.row()
        saved_select_row.operator(SaveSelection.bl_idname)
        saved_select_row.operator(SelectSavedSelection.bl_idname)
        saved_select_row.operator(DeSelectSavedSelection.bl_idname)


CLASS_LIST = [
    LinkArmatureToCurrentScene,
    SelectMoreComponents,
    SelectLessComponents,
    SaveSelection,
    SelectSavedSelection,
    DeSelectSavedSelection,
    SelectVerticesInWeightRange,
    SelectWeightIslandsInRange,
    SelectUnNormalizedVertices,
    RemoveWeightingOnSelected,
    RemoveUnusedVertexGroups,
    CopySelectedVertexWeights,
    PasteSelectedVertexWeights,
]


def menu_func(self, context):
    for cls in CLASS_LIST:
        self.layout.operator(cls.bl_idname)


def register():
    for cls in CLASS_LIST:
        bpy.utils.register_class(cls)
    bpy.utils.register_class(RENDER_PT_SkinSuiteVertexGroupTools)

    # add to menu so we can register shortcuts
    bpy.types.VIEW3D_MT_select_paint_mask_vertex.append(menu_func)

def unregister():
    for cls in CLASS_LIST:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(RENDER_PT_SkinSuiteVertexGroupTools)

    # add to menu so we can register shortcuts
    bpy.types.VIEW3D_MT_select_paint_mask_vertex.remove(menu_func)