import bpy
from bpy.props import IntProperty,FloatVectorProperty, EnumProperty,FloatProperty
from bpy.types import Context, Event
from mathutils import *
import math
from bpy.props import BoolProperty
from bpy_extras import view3d_utils
import blf

bl_info = {
	"name":"WheelisDepth",
	"author":"tantan_typhoon",
	"version":(1.0),
	"blender":(3,3,7),
	"locaton":"Rigging",
	"description":"To move in the direction of DEPTH by the mouse wheel",
	"warnig":"",
	"support":'COMMUNITY',
	"wiki_url":"",
	"tracker_url":"",
	"category":"utility"
}

#MODULE FUNCTION AREA-------------------------------------------------
def get_region_and_space(context, area_type, region_type, space_type):
	region = None
	area = None
	space = None

	# 指定されたエリアの情報を取得する
	for a in context.screen.areas:
		if a.type == area_type:
			area = a
			break
	else:
		return (None, None)
	# 指定されたリージョンの情報を取得する
	for r in area.regions:
		if r.type == region_type:
			region = r
			break
	# 指定されたスペースの情報を取得する
	for s in area.spaces:
		if s.type == space_type:
			space = s
			break

	return (region, space)


def matrixinvert(matrix):
	minv = matrix.copy()
	minv.invert()
	return minv


def vector_rigion_by_mouse(context,event):
	vm = Vector((event.mouse_region_x,event.mouse_region_y))
	return vm

def convert_local_to_custumrestpose(aposebone,local_vector):
	local_to_custumpose = matrixinvert(aposebone.matrix)
	local_to_restpose = aposebone.matrix_basis @ local_to_custumpose
	return local_to_restpose @ local_vector

def restrotation(target_vector_local,obj_vector_local,obj):
	#TODO:matrix_basis is True? matrix_world is True?
	(l,q,s) = obj.matrix_basis.decompose()
	Matrix_rotation_reset = Matrix.LocRotScale(l,Quaternion((1.0,0.0,0.0,0.0)),s)
	obj.matrix_basis = Matrix_rotation_reset
	obj.rotation_mode = 'QUATERNION'
	q = obj_vector_local.rotation_difference(target_vector_local)
	obj.rotation_quaternion = q
	
def wheeleventpulse(event,countwheelrotation):
	if event.value == 'PRESS':
			if event.type == 'WHEELUPMOUSE':
				return countwheelrotation - 1
			if event.type == 'WHEELDOWNMOUSE':
				return countwheelrotation + 1
			if event.type == 'MIDDLEMOUSE':
				return 0
	return countwheelrotation

#objectmode area--------------------------------------------------
class WID_OT_RotationObject(bpy.types.Operator):
	bl_idname = "wid.rotationobject"
	bl_label = "WID_RotationObject"
	bl_description = "Rotate objects with the mouse wheel"
	bl_options = {'REGISTER','UNDO'}

	obj = None
	guide_obj = None
	init_matrix_world = None
	init_how_axis = None
	countwheelrotation = 0


	def execute(self,context):
		return {'FINISHED'}
    
	def modal(self,context,event):

		region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')

		if (event.type == 'ESC') or (event.type == 'LEFTMOUSE'):
			self.countwheelrotation = 0
			WID_Preferences.modalrunning = False
			self.obj.show_axis = self.init_how_axis
			self.init_matrix_world = None 
			self.obj =None
			bpy.data.objects.remove(self.guide_obj, do_unlink=True)
			#bpy.data.objects.remove(self.guide_obj)
			#bpy.data.objects.remove(bpy.data.objects['WID_guide_obj'])
			#self.guide_obj = None

			return {'FINISHED'}
		
		#イベントからマウスのリージョン座標を取得
		mouseregion = vector_rigion_by_mouse(context,event)

		self.countwheelrotation = wheeleventpulse(event,self.countwheelrotation)
		depth = WID_Preferences.Wheel_grid_distance*self.countwheelrotation
		
		#このあたりが何かおかしい,ローテーションの位置
		#マウスの位置のローカル座標ベクトルを取得(これはあっている確認済)
		vector_mouse_world = view3d_utils.region_2d_to_location_3d(region,space.region_3d,mouseregion,Vector((depth,0,0)))

		self.guide_obj.location = vector_mouse_world 
		#マウスの座標
		mvec_local = self.init_matrix_world @ vector_mouse_world
		self.obj.show_axis = True
				
		mvec_local = (self.init_matrix_world @ vector_mouse_world) 

		q = Vector((0,0,1)).rotation_difference(mvec_local)
		self.obj.rotation_quaternion = q
	
		#第一引数が定数ベクトルだと上手く言っている。
		#restrotation(mvec_local,Vector((0,0,1)),self.obj)
		
		return {'RUNNING_MODAL'}
	
	def invoke(self, context, event):
		if context.area.type == 'VIEW_3D':
			if bpy.context.active_object is not None:
				if not WID_Preferences.modalrunning:
					self.countwheelrotation = 0
					self.obj = None
					self.init_matrix_world = None
					WID_Preferences.modalrunning = True
					WID_Preferences.Wheel_grid_distance = 1
					mh = context.window_manager.modal_handler_add(self)
					self.obj = bpy.context.active_object
					self.obj.rotation_mode = 'QUATERNION'
					self.init_how_axis = self.obj.show_axis
					#self.obj.rotation_quaternion = Quaternion((1.0,0.0,0.0,0.0))
					(l,q,s) = self.obj.matrix_world.decompose()
					self.obj.matrix_world = Matrix.LocRotScale(l,Quaternion((1.0,0.0,0.0,0.0)),Vector((1,1,1)))
					
					self.init_matrix_world = self.obj.matrix_world.copy()
					
					self.init_matrix_world = matrixinvert(self.init_matrix_world)
					

					bpy.ops.mesh.primitive_uv_sphere_add(radius= 0.3,location = Vector((0,0,0)),align='CURSOR')
					self.guide_obj = bpy.context.active_object
					self.guide_obj.name = "WID_guide_obj"

					return {'RUNNING_MODAL'}
				else:
					WID_Preferences.modalrunning = False
					return {'FINISHED'}
			else:
				self.report({'INFO'}, "Please Make the object active")
				return{'FINISHED'}


#common area-------------------------------------------------
class WID_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    modalrunning = False

    Wheel_grid_distance:FloatProperty(
        name="Wheel_grid_distance",
        description="Distance moved in one wheel rotation",
        default=1,
        min=0,
    )

    LengthOption:BoolProperty(
        name="LengthOption",
        description="Whether to change the length",
        default=True
    )

    '''
    def draw(self, context):
        layout = self.layout
        layout.label(text="Key for the assignment: ")
    '''


def menu_fn_object(self,context):
	self.layout.separator()
	self.layout.operator(WID_OT_RotationObject.bl_idname)
	#self.layout.operator(testdammy22_lcation.bl_idname)


classes = [
	WID_OT_RotationObject,
	WID_Preferences,
]


def register():
	for c in classes:
		bpy.utils.register_class(c)

	#register_shortcut()
	#bpy.types.VIEW3D_MT_pose.append(menu_fn_pose)
	#bpy.types.VIEW3D_MT_object.append(menu_fn_object)
	
	bpy.types.VIEW3D_MT_object.prepend(menu_fn_object)


def unregister():
	#unregister_shortcut()
	#bpy.types.VIEW3D_MT_pose.remove(menu_fn_pose)
	bpy.types.VIEW3D_MT_object.remove(menu_fn_object)
	
	for c in classes:
		bpy.utils.unregister_class(c)
		
if __name__ == "__main__":
	register()
