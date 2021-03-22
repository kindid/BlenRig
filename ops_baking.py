import bpy

################################# BAKING OPERATORS ##########################################################


# Mesh Proportions Baker operator
class ARMATURE_OT_mesh_pose_baker(bpy.types.Operator):
    bl_label = "BlenRig 6 Mesh Baker"
    bl_idname = "blenrig.mesh_pose_baker"
    bl_description = "Bake current pose to mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not bpy.context.object:
            return False
        return (bpy.context.object.type == "MESH" and context.mode=='OBJECT')

    #Baking
    def bake(self, context):
        props = context.window_manager.blenrig_6_props
        if not bpy.context.object:
            return False
        old_ob = bpy.context.active_object
        bake_meshes = [ob.name for ob in bpy.context.selected_objects if ob.type=="MESH"]

        for name in bake_meshes:
            if name in bpy.data.objects:
                ob = bpy.data.objects[name]

            bpy.context.view_layer.objects.active = ob

            # Turn off SUBSURF for baking
            for mod in ob.modifiers:
                if mod.type == 'SUBSURF':
                    old_state = mod.show_viewport
                    mod.show_viewport = False

            # --- get a mesh from the object ---
            depsgraph = bpy.context.evaluated_depsgraph_get()
            mesh_owner = ob.evaluated_get(depsgraph)
            mesh = mesh_owner.to_mesh()

            for mod in ob.modifiers:
                if mod.type == 'SUBSURF':
                    mod.show_viewport = old_state

            # If Bake to shape option is off
            if props.bake_to_shape == False:
                # Check if there are shapekeys in object
                try:
                    if ob.data.shape_keys.key_blocks:
                        key = ob.data.shape_keys
                        shapekeys = key.key_blocks
                        # Transfer vertex locations to Basis key
                        for vert in ob.data.vertices:
                            shapekeys['Basis'].data[vert.index].co = mesh.vertices[vert.index].co

                        # Make baked shape active
                        for i in range(len(shapekeys)):
                            shape = shapekeys[i]
                            if shape.name == 'Basis':
                                ob.active_shape_key_index = i
                except (AttributeError):
                    # Transfer vertex locations to Mesh
                    for vert in ob.data.vertices:
                        vert.co = mesh.vertices[vert.index].co

            # If Bake to shape option is on
            else:
                # Check if there are shapekeys in object
                try:
                    ob.data.shape_keys.key_blocks
                except (AttributeError):
                    Basis = ob.shape_key_add(from_mix=False)
                    Basis.name = 'Basis'

                # Create new shape for storing the bake

                baked_shape = ob.shape_key_add(from_mix=False)
                baked_shape.name = 'Baked_shape'
                baked_shape.value = 1

                # Transfer vertex locations
                for vert in ob.data.vertices:
                    baked_shape.data[vert.index].co = mesh.vertices[vert.index].co

                # Make baked shape active
                for i in range(len(ob.data.shape_keys.key_blocks)):
                    shape = ob.data.shape_keys.key_blocks[i]
                    if shape.name == baked_shape.name:
                        ob.active_shape_key_index = i

        # Remove unused baked mesh
        ob.to_mesh_clear()
        bpy.context.view_layer.objects.active = old_ob


    #Unbind Mdef modifier if object is bound
    def mdef_unbind(self, context):
        if not bpy.context.object:
            return False

        old_ob = bpy.context.active_object

        bake_meshes = [ob.name for ob in bpy.context.selected_objects if ob.type=="MESH"]
        for name in bake_meshes:
            if name in bpy.data.objects:
                ob = bpy.data.objects[name]
            bpy.context.view_layer.objects.active = ob

            # unbind mdef modifiers
            for i in range(len(ob.modifiers)):
                mod = ob.modifiers[i]
                if mod.type in ['MESH_DEFORM']:
                    if mod.is_bound == True:
                        bpy.ops.object.meshdeform_bind(modifier=mod.name)

            # unbind sdef modifiers
            for i in range(len(ob.modifiers)):
                mod = ob.modifiers[i]
                if mod.type in ['SURFACE_DEFORM']:
                    if mod.is_bound == True:
                        bpy.ops.object.surfacedeform_bind(modifier=mod.name)

        bpy.context.view_layer.objects.active = old_ob

    def execute(self, context):
        self.bake(context)
        self.mdef_unbind(context)
        self.report({'INFO'}, "Baking done")
        return{'FINISHED'}

# Hook Reset operator
class ARMATURE_OT_reset_hooks(bpy.types.Operator):
    bl_label = "BlenRig 6 Reset Hooks"
    bl_idname = "blenrig.reset_hooks"
    bl_description = "Reset Hooks on Lattices and Curves"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not bpy.context.object:
            return False
        return (bpy.context.object.type == "LATTICE", "CURVE" and context.mode=='OBJECT')

    def activar_modif(self,context):
        for a in bpy.context.object.modifiers:
            bpy.context.object.modifiers[a.name].show_viewport = True

    def reset_hooks(self,context):

        selected_lattices = [ob.name for ob in bpy.context.selected_objects if ob.type=="LATTICE"]

        for name in selected_lattices:
            if name in bpy.data.objects:
                ob = bpy.data.objects[name]

            bpy.context.view_layer.objects.active = ob

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.lattice.select_all(action='SELECT')
            for mod in ob.modifiers:
                if mod.type == 'HOOK':
                    bpy.ops.object.hook_reset(modifier=mod.name)
            bpy.ops.object.mode_set(mode='OBJECT')

        selected_curves = [ob.name for ob in bpy.context.selected_objects if ob.type=="CURVE"]

        for name in selected_curves:
            if name in bpy.data.objects:
                ob = bpy.data.objects[name]

            bpy.context.view_layer.objects.active = ob

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.curve.select_all(action='SELECT')
            for mod in ob.modifiers:
                if mod.type == 'HOOK':
                    bpy.ops.object.hook_reset(modifier=mod.name)
            bpy.ops.object.mode_set(mode='OBJECT')

    def execute(self, context):
        self.reset_hooks(context)
        self.activar_modif(context)
        self.report({'INFO'}, "Hooks Reseted")
        return{'FINISHED'}

# Hook Disable Hooks modifier
class ARMATURE_OT_disable_hooks_modif(bpy.types.Operator):
    bl_label = "BlenRig 6 Disable Hooks modifier"
    bl_idname = "blenrig.disable_hooks_modif"
    bl_description = "Disable Hooks modifier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not bpy.context.object:
            return False
        return (bpy.context.object.type == "LATTICE", "CURVE" and context.mode=='OBJECT')

    def desactivar_modif(self,context):
        for a in bpy.context.object.modifiers:
            bpy.context.object.modifiers[a.name].show_viewport = False

    def execute(self, context):
        self.desactivar_modif(context)
        self.report({'INFO'}, "Disable Lattice Hooks")
        return{'FINISHED'}

# Reset Armature related Lattices and Curves operator
class ARMATURE_OT_reset_deformers(bpy.types.Operator):
    bl_label = "BlenRig 6 Reset Deformers"
    bl_idname = "blenrig.reset_deformers"
    bl_description = "Reset Armature related Lattices and Curves"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not bpy.context.object:
            return False
        else:
            return (bpy.context.object.type=='ARMATURE' and \
                context.mode=='POSE')

    def reset_deformers(self, context):

        # preparing scene

        # activating lattices collection:
        enable_disable_colleciton(False, 'Lattices')

        bpy.ops.object.mode_set(mode='OBJECT')
        old_active = bpy.context.active_object
        old_selected = bpy.context.selected_objects
        old_visible_collections = [coll.name for coll in bpy.data.collections if coll.hide_viewport == False  ]
        for ob in old_selected:
            ob.select_set(False)

        # Armature related lattices and curves
        deformers_collection = []
        selected_deformers = []

        for ob in bpy.data.objects:
            if ob.type in 'LATTICE' or 'CURVE':
                for mod in ob.modifiers:
                    if mod.type in 'HOOK':
                        if mod.object.name == bpy.context.object.name:
                            # Toggle on active collections
                            for coll in bpy.data.collections:
                                for coll_ob in coll.objects:
                                    if ob.name == coll_ob.name:
                                        deformers_collection.append(coll.name)
                            for coll in bpy.data.collections:
                                if coll.name in deformers_collection:
                                    coll.hide_viewport = False
                            ob.select_set(True)
                            selected_deformers.append(ob.name)

        for name in selected_deformers:
            if name in bpy.data.objects:
                ob = bpy.data.objects[name]

            bpy.context.view_layer.objects.active = ob

            # Reset Hooks
            bpy.ops.blenrig.reset_hooks()

        #Back to Armature
        for ob in bpy.context.selected_objects:
            ob.select_set(False)
        for coll in bpy.data.collections:
            coll.hide_viewport = True
        for coll in bpy.data.collections:
            if coll.name in old_visible_collections:
                coll.hide_viewport = False
        bpy.context.view_layer.objects.active = old_active
        for ob in old_selected:
            ob.select_set(True)
        bpy.ops.object.mode_set(mode='POSE')
        #Hack for updating objects
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)

        # deactivating lattices collection:
        enable_disable_colleciton(True, 'Lattices')

    def execute(self, context):
        self.reset_deformers(context)
        self.report({'INFO'}, "Lattices and Curves Reset")
        return{'FINISHED'}


def enable_disable_colleciton(mode, target_coll):
    # de/activating lattices collection:
    mc = None
    vlayer = bpy.context.view_layer

    # obtain Master Colecction from active object:
    obj = bpy.context.active_object
    obj_name = obj.name

    subcoll = [coll for coll in bpy.data.collections if obj_name in coll.objects]
    for coll in bpy.data.collections:
        if subcoll[0].name in coll.children:
            # get the real Master Collection, even if the user has renamed the collection:
            mc = vlayer.layer_collection.children[coll.name]

    # print(mc)
    if mc:
        for child in reversed(mc.children):
            coll = child.collection
            # print(child)
            if 'BlenRig' in coll:
                if coll.name.startswith(target_coll):
                    print('Processing: ' + mc.name + ' > ' + coll.name)
                    vlayer.layer_collection.children[mc.name].children[coll.name].exclude = mode
                    break
                else:
                    pass
    else:
        print("Error")

# Armature Baker All operator
class ARMATURE_OT_armature_baker_all_part_1(bpy.types.Operator):
    bl_label = "BlenRig 6 Armature Baker"
    bl_idname = "blenrig.armature_baker_all_part_1"
    bl_description = "Bake current pose to armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not bpy.context.object:
            return False
        else:
            return (bpy.context.object.type=='ARMATURE' and \
                context.mode=='POSE' or 'EDIT_ARMATURE')

    def bake_all(self, context):

        # preparing scene
        bpy.ops.object.mode_set(mode='OBJECT')
        old_active = bpy.context.active_object
        old_selected = bpy.context.selected_objects
        old_visible_collections = [coll.name for coll in bpy.context.view_layer.layer_collection.children if coll.hide_viewport == False]

        enable_disable_colleciton(False, 'Lattices')
        enable_disable_colleciton(False, 'Mesh_Deform_Cage')
        enable_disable_colleciton(False, 'FaceRigMesh')
        enable_disable_colleciton(False, 'GameModel')
        enable_disable_colleciton(False, 'MDef')


        for ob in old_selected:
            ob.select_set(False)


        # unparenting external objects related to the armature
        deformers_collection = []
        parent_pairs = []
        for ob in bpy.data.objects:
            if ob.parent is not None:
                if ob.parent.name == bpy.context.object.name:
                    # Toggle on active collections
                    for coll in bpy.context.collection.children:
                        for coll_ob in coll.objects:
                            if ob.name == coll_ob.name:
                                deformers_collection.append(coll.name)
                    for coll in bpy.context.view_layer.layer_collection.children:
                        if coll.name in deformers_collection:
                            coll.hide_viewport = False
                    ob.select_set(True)
                    parent_pairs.append([ob, ob.parent, ob.parent_bone])
                    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        #Back to Armature
        for ob in bpy.context.selected_objects:
            ob.select_set(False)
        bpy.context.view_layer.objects.active = old_active
        for ob in old_selected:
            ob.select_set(True)

        bpy.ops.object.mode_set(mode='POSE')
        posebones = bpy.context.object.pose.bones

        # Bake Armature
        bpy.ops.pose.armature_apply()

        arm = bpy.context.object.data

        # Reset Constraints
        for b in posebones:
            for con in b.constraints:
                if con.type not in ['LIMIT_DISTANCE', 'STRETCH_TO', 'CHILD_OF']:
                    continue
                if con.type == 'LIMIT_DISTANCE':
                    con.distance = 0
                elif con.type == 'STRETCH_TO':
                    con.rest_length = 0

        bpy.ops.object.mode_set(mode='OBJECT')
        for ob in bpy.context.selected_objects:
            ob.select_set(False)

        # re-parenting external objects related to the armature
        for pp in parent_pairs:
            ob, parent, bone = pp
            ob.parent = parent
            ob.parent_type = 'BONE'
            ob.parent_bone = bone
            #Reseting Hooks
            ob.select_set(True)
            bpy.ops.blenrig.reset_hooks()

        #Back to Armature
        for ob in bpy.context.selected_objects:
            ob.select_set(False)
        #Set to visible collections back
        for coll in bpy.context.view_layer.layer_collection.children:
            coll.hide_viewport = True
        for coll in bpy.context.view_layer.layer_collection.children:
            if coll.name in old_visible_collections:
                coll.hide_viewport = False
        bpy.context.view_layer.objects.active = old_active
        for ob in old_selected:
            ob.select_set(True)

        bpy.ops.object.mode_set(mode='POSE')

        # deactivating lattices collection:
        enable_disable_colleciton(True, 'Lattices')
        enable_disable_colleciton(True, 'Mesh_Deform_Cage')
        enable_disable_colleciton(True, 'FaceRigMesh')
        enable_disable_colleciton(True, 'GameModel')
        enable_disable_colleciton(True, 'MDef')


    def armature_update_values(self, context):

        armobj = bpy.context.active_object

        #Bone Length Properties Update
        for b in armobj.pose.bones:
            if b.keys() != '[]':
                if 'b_length_L' in b.keys():
                    b['b_length_L'] = b.bone.length
                if 'b_length_R' in b.keys():
                    b['b_length_R'] = b.bone.length
                if 'b_length' in b.keys():
                    b['b_length'] = b.bone.length
        #Floor constraints distance calculation
        for b in armobj.pose.bones:
            for C in b.constraints:
                if C.type == 'FLOOR':
                    if 'Floor_Lips' in C.name:
                        C.offset = abs((b.head[2] - armobj.pose.bones[C.subtarget].head[2]) * 0.9)
                    if 'Floor_Foot' in C.name:
                        C.offset = abs(b.head[2] - armobj.pose.bones[b.custom_shape_transform.name].head[2])
        #Blink rate calculation
        for b in armobj.pose.bones:
            if b.name == 'blink_ctrl_L':
                try:
                    b['Blink_Rate_L'] = abs(armobj.pose.bones['eyelid_up_ctrl_L'].head[2] - armobj.pose.bones['eyelid_low_ctrl_L'].head[2])
                except:
                    pass
            if b.name == 'blink_ctrl_R':
                try:
                    b['Blink_Rate_R'] = abs(armobj.pose.bones['eyelid_up_ctrl_R'].head[2] - armobj.pose.bones['eyelid_low_ctrl_R'].head[2])
                except:
                    pass

    def sav(self, context):
        arm = bpy.context.active_object
        enable_disable_colleciton(False, 'MDef')
        cage_select = bpy.context.view_layer.objects['BlenRigMdefCage']
        bpy.context.view_layer.objects.active = cage_select
        bpy.ops.object.select_all(action='DESELECT')
        cage_select.select_set(1)
        bpy.ops.blenrig.mesh_pose_baker()
        enable_disable_colleciton(True, 'MDef')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = arm
        self.bake_all(context)
        self.armature_update_values(context)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.blenrig.fix_misaligned_bones()
        bpy.ops.blenrig.auto_bone_roll()
        bpy.context.object.data.layers[29] = True
        bpy.context.object.data.layers[31] = False
        bpy.context.object.data.show_axes = True
        bpy.context.scene.cursor.location = [0,0,0]

    def execute(self, context):
        self.sav(context)
        self.report({'INFO'}, "1º Baking part done")
        return{'FINISHED'}

class ARMATURE_OT_armature_baker_all_part_2(bpy.types.Operator):
    bl_label = "BlenRig 6 Armature Baker"
    bl_idname = "blenrig.armature_baker_all_part_2"
    bl_description = "Bake current pose to armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not bpy.context.object:
            return False
        else:
            return (bpy.context.object.type=='ARMATURE' and \
                context.mode=='EDIT_ARMATURE')

    def after_custom_align(self, context):
        bpy.ops.blenrig.custom_bone_roll()
        bpy.ops.blenrig.store_roll_angles()
        bpy.context.object.data.show_axes = False 
        bpy.context.object.data.layers[29] = False 
        bpy.context.object.data.layers[31] = True 
        bpy.ops.object.mode_set(mode='POSE')
        bpy.context.object.data.pose_position = 'REST'
        bpy.ops.blenrig.reset_constraints()
        bpy.ops.blenrig.reset_deformers()
        bpy.context.object.data.pose_position = 'POSE'
        bpy.context.object.data.reproportion = False
        bpy.context.scene.cursor.location = [0,0,0]

    def execute(self, context):
        self.after_custom_align(context)
        self.report({'INFO'}, "Baking Finish")
        return{'FINISHED'}

# Armature Advanced Baker operator
class ARMATURE_OT_advanced_armature_baker(bpy.types.Operator):
    bl_label = "BlenRig 6 Armature Baker"
    bl_idname = "blenrig.advanced_armature_baker"
    bl_description = "Bake current pose to armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not bpy.context.object:
            return False
        else:
            return (bpy.context.object.type=='ARMATURE' and \
                context.mode=='POSE')

    def bake_armature(self, context):

        # preparing scene
        bpy.ops.object.mode_set(mode='OBJECT')
        old_active = bpy.context.active_object
        old_selected = bpy.context.selected_objects
        old_visible_collections = [coll.name for coll in bpy.context.view_layer.layer_collection.children if coll.hide_viewport == False]

        enable_disable_colleciton(False, 'Lattices')
        enable_disable_colleciton(False, 'Mesh_Deform_Cage')
        enable_disable_colleciton(False, 'FaceRigMesh')
        enable_disable_colleciton(False, 'GameModel')



        for ob in old_selected:
            ob.select_set(False)


        # unparenting external objects related to the armature
        deformers_collection = []
        parent_pairs = []
        for ob in bpy.data.objects:
            if ob.parent is not None:
                if ob.parent.name == bpy.context.object.name:
                    # Toggle on active collections
                    for coll in bpy.context.scene.collection.children:
                        for coll_ob in coll.objects:
                            if ob.name == coll_ob.name:
                                deformers_collection.append(coll.name)
                    for coll in bpy.context.view_layer.layer_collection.children:
                        if coll.name in deformers_collection:
                            coll.hide_viewport = False
                    ob.select_set(True)
                    parent_pairs.append([ob, ob.parent, ob.parent_bone])
                    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        #Back to Armature
        for ob in bpy.context.selected_objects:
            ob.select_set(False)
        bpy.context.view_layer.objects.active = old_active
        for ob in old_selected:
            ob.select_set(True)

        bpy.ops.object.mode_set(mode='POSE')
        posebones = bpy.context.object.pose.bones

        # Bake Armature
        bpy.ops.pose.armature_apply()

        arm = bpy.context.object.data

        # Reset Constraints
        for b in posebones:
            for con in b.constraints:
                if con.type not in ['LIMIT_DISTANCE', 'STRETCH_TO', 'CHILD_OF']:
                    continue
                if con.type == 'LIMIT_DISTANCE':
                    con.distance = 0
                elif con.type == 'STRETCH_TO':
                    con.rest_length = 0
                #elif con.type == 'CHILD_OF':
                    #bpy.ops.object.mode_set(mode='EDIT')
                    #arm.edit_bones.active = arm.edit_bones[b.name]
                    #bpy.ops.object.mode_set(mode='POSE')
                    #print ('"{}"'.format(con.name))
                    #bpy.ops.constraint.childof_clear_inverse(constraint=con.name, owner='BONE')
                    #bpy.ops.constraint.childof_set_inverse(constraint=con.name, owner='BONE')
                    ## somehow it only works if you run it twice
                    #bpy.ops.constraint.childof_set_inverse(constraint=con.name, owner='BONE')
                    #bpy.ops.object.mode_set(mode='EDIT')
                    #arm.edit_bones[b.name].select = False
        bpy.ops.object.mode_set(mode='OBJECT')
        for ob in bpy.context.selected_objects:
            ob.select_set(False)

        # re-parenting external objects related to the armature
        for pp in parent_pairs:
            ob, parent, bone = pp
            ob.parent = parent
            ob.parent_type = 'BONE'
            ob.parent_bone = bone
            #Reseting Hooks
            ob.select_set(True)
            bpy.ops.blenrig.reset_hooks()

        #Back to Armature
        for ob in bpy.context.selected_objects:
            ob.select_set(False)
        #Set to visible collections back
        for coll in bpy.context.view_layer.layer_collection.children:
            coll.hide_viewport = True
        for coll in bpy.context.view_layer.layer_collection.children:
            if coll.name in old_visible_collections:
                coll.hide_viewport = False
        bpy.context.view_layer.objects.active = old_active
        for ob in old_selected:
            ob.select_set(True)

        bpy.ops.object.mode_set(mode='POSE')

        #deactivating lattices collection:
        enable_disable_colleciton(True, 'Lattices')
        enable_disable_colleciton(True, 'Mesh_Deform_Cage')
        enable_disable_colleciton(True, 'FaceRigMesh')
        enable_disable_colleciton(True, 'GameModel')


    def armature_update_values(self, context):

        armobj = bpy.context.active_object

        #Bone Length Properties Update
        for b in armobj.pose.bones:
            if b.keys() != '[]':
                if 'b_length_L' in b.keys():
                    b['b_length_L'] = b.bone.length
                if 'b_length_R' in b.keys():
                    b['b_length_R'] = b.bone.length
                if 'b_length' in b.keys():
                    b['b_length'] = b.bone.length
        #Floor constraints distance calculation
        for b in armobj.pose.bones:
            for C in b.constraints:
                if C.type == 'FLOOR':
                    if 'Floor_Lips' in C.name:
                        C.offset = abs((b.head[2] - armobj.pose.bones[C.subtarget].head[2]) * 0.9)
                    if 'Floor_Foot' in C.name:
                        C.offset = abs(b.head[2] - armobj.pose.bones[b.custom_shape_transform.name].head[2])

        #Blink rate calculation
        for b in armobj.pose.bones:
            if b.name == 'blink_ctrl_L':
                try:
                    b['Blink_Rate_L'] = abs(armobj.pose.bones['eyelid_up_ctrl_L'].head[2] - armobj.pose.bones['eyelid_low_ctrl_L'].head[2])
                except:
                    pass
            if b.name == 'blink_ctrl_R':
                try:
                    b['Blink_Rate_R'] = abs(armobj.pose.bones['eyelid_up_ctrl_R'].head[2] - armobj.pose.bones['eyelid_low_ctrl_R'].head[2])
                except:
                    pass

    def execute(self, context):
        self.bake_armature(context)
        self.armature_update_values(context)
        self.report({'INFO'}, "Baking done")
        return{'FINISHED'}

# Reset Constraints Operator
class ARMATURE_OT_reset_constraints(bpy.types.Operator):
    bl_label = "BlenRig 6 Reset Constraints"
    bl_idname = "blenrig.reset_constraints"
    bl_description = "Reset all posebone constraints"

    @classmethod
    def poll(cls, context):
        if not bpy.context.object:
            return False
        else:
            return (bpy.context.object.type=='ARMATURE' and \
                context.mode=='POSE')

    def execute(self, context):
        pbones = context.active_object.pose.bones
        edit_bones = context.active_object.data.edit_bones
        if len(pbones) < 1:
            self.report({'INFO'}, "No bones found")
            return{'FINISHED'}

        amount = 0
        arm = bpy.context.object.data

        for pbone in pbones:
            for con in pbone.constraints:
                if con.type == 'LIMIT_DISTANCE':
                    amount += 1
                    con.distance = 0
                elif con.type == 'STRETCH_TO':
                    amount += 1
                    con.rest_length = 0
                #elif con.type == 'CHILD_OF':
                    #bpy.ops.object.mode_set(mode='EDIT')
                    #arm.edit_bones.active = arm.edit_bones[pbone.name]
                    #bpy.ops.object.mode_set(mode='POSE')
                    #print ('"{}"'.format(con.name))
                    #bpy.ops.constraint.childof_clear_inverse(constraint=con.name, owner='BONE')
                    #bpy.ops.constraint.childof_set_inverse(constraint=con.name, owner='BONE')
                    ## somehow it only works if you run it twice
                    #bpy.ops.constraint.childof_set_inverse(constraint=con.name, owner='BONE')
                    #bpy.ops.object.mode_set(mode='EDIT')
                    #arm.edit_bones[b.name].select = False
                    #bpy.ops.object.mode_set(mode='POSE')
        self.report({'INFO'}, str(amount) + " constraints reset")

        return{'FINISHED'}
