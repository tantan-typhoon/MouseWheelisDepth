# SPDX-License-Identifier: GPL-3.0-or-later
'''
Copyright (C) 2023 tantan-typhoon
 
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
import bpy
from bpy.props import IntProperty,FloatVectorProperty, EnumProperty,FloatProperty
from bpy.types import Context, Event
from mathutils import *
import math
from bpy.props import BoolProperty
from bpy_extras import view3d_utils
import blf

bl_info = {
	"name":"MouseWheelisDepth",
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

#	OPERATOR CLASS AREA***********************************************
class MWID_OT_RotationObject(bpy.types.Operator):
	bl_idname = "mwid.rotationobject"
	bl_label = "MWID_RotationObject"
	bl_description = "Rotate object with the mouse wheel"
	bl_options = {'REGISTER','UNDO'}

	obj = None
	guide_obj = None
	init_matrix_world = None
	init_how_axis = None
	countwheelrotation = 0
	prefs = None

	@classmethod
	def poll(cls, context):
		return context.mode == 'OBJECT'


	def execute(self,context):
		return {'FINISHED'}
	
	def modal(self,context,event):
		if (event.type == 'ESC') or (event.type == 'LEFTMOUSE'):
			self.countwheelrotation = 0
			self.prefs.modalrunning = False
			self.obj.show_axis = self.init_how_axis
			self.init_matrix_world = None
			self.obj =None
			if self.guide_obj is not None:
				bpy.data.objects.remove(self.guide_obj, do_unlink=True)
				self.guide_obj = None

			return {'FINISHED'}
		
		#イベントからマウスのリージョン座標を取得
		mouseregion = vector_rigion_by_mouse(context,event)

		self.countwheelrotation = wheeleventpulse(event,self.countwheelrotation)
		depth = self.prefs.Wheel_grid_distance*self.countwheelrotation

		region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
		
		#このあたりが何かおかしい,ローテーションの位置
		#マウスの位置のローカル座標ベクトルを取得(これはあっている確認済)
		vector_mouse_world = view3d_utils.region_2d_to_location_3d(region,space.region_3d,mouseregion,Vector((depth,0,0)))
		if self.guide_obj is not None:
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
		self.prefs = bpy.context.preferences.addons[__name__].preferences
		if context.area.type == 'VIEW_3D':
			
			if bpy.context.active_object is not None:
				if not self.prefs.modalrunning:
					self.countwheelrotation = 0
					self.obj = None
					self.init_matrix_world = None
					self.prefs.modalrunning = True
					
					mh = context.window_manager.modal_handler_add(self)
					self.obj = bpy.context.active_object
					self.obj.rotation_mode = 'QUATERNION'
					self.init_how_axis = self.obj.show_axis
					(l,q,s) = self.obj.matrix_world.decompose()
					
					self.obj.matrix_world = Matrix.LocRotScale(l,Quaternion((1.0,0.0,0.0,0.0)),s)
					
					self.init_matrix_world = self.obj.matrix_world.copy()
					self.init_matrix_world = matrixinvert(self.init_matrix_world)
					
					if self.prefs.Guide_Object_Option :
						bpy.ops.mesh.primitive_uv_sphere_add(radius= 0.3,location = Vector((0,0,0)),align='CURSOR')
						self.guide_obj = bpy.context.active_object
						self.guide_obj.name = "MWID_guide_obj"

					return {'RUNNING_MODAL'}
				else:
					self.prefs.modalrunning = False
					return {'FINISHED'}
			else:
				self.report({'INFO'}, "Please Make the object active")
				return{'FINISHED'}


class MWID_OT_MoveObject(bpy.types.Operator):
	bl_idname = "mwid.moveobject"
	bl_label = "MWID_MoveObject"
	bl_description = "Move object with the mouse wheel"
	bl_options = {'REGISTER','UNDO'}

	obj = None
	guide_obj = None
	init_matrix_world = None
	init_how_axis = None
	countwheelrotation = 0
	prefs = None

	@classmethod
	def poll(cls, context):
		return context.mode == 'OBJECT'

	def execute(self,context):
		return {'FINISHED'}
	
	
	def modal(self,context,event):

		if (event.type == 'ESC') or (event.type == 'LEFTMOUSE'):
			self.countwheelrotation = 0
			self.prefs.modalrunning = False
			self.obj.show_axis = self.init_how_axis
			self.init_matrix_world = None
			self.obj =None
			

			return {'FINISHED'}
		
		#イベントからマウスのリージョン座標を取得
		mouseregion = vector_rigion_by_mouse(context,event)
		self.countwheelrotation = wheeleventpulse(event,self.countwheelrotation)
		depth = self.prefs.Wheel_grid_distance*self.countwheelrotation

		#マウスの位置のローカル座標ベクトルを取得(これはあっている確認済)
		region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
		vector_world = view3d_utils.region_2d_to_location_3d(region,space.region_3d,mouseregion,Vector((depth,0,0)))

		#マウスのワールド座標上にオブジェクトの位置を移動
		self.obj.matrix_world.translation = vector_world

		return {'RUNNING_MODAL'}
	
	def invoke(self, context, event):
		self.prefs = bpy.context.preferences.addons[__name__].preferences
		if context.area.type == 'VIEW_3D':
			if bpy.context.active_object is not None:
				
				if not self.prefs.modalrunning:
					self.prefs.modalrunning = True
					self.prefs.Wheel_grid_distanc = 1
					mh = context.window_manager.modal_handler_add(self)
					self.obj = bpy.context.active_object
					self.init_how_axis = self.obj.show_axis
					
					return {'RUNNING_MODAL'}
			else:
				self.prefs.modalrunning = False
				return {'FINISHED'}

#	Panel CLASS AREA******************************************************************
class MWID_PT_OBjectmodeOptionPaneleObject(bpy.types.Panel):
	bl_label = "MWID_Option"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "MWID"
	bl_context = "objectmode"


	def draw(self,context):
		
		layout = self.layout
		prefs = bpy.context.preferences.addons[__name__].preferences
		layout.operator(MWID_OT_RotationObject.bl_idname, text="RotationObject")
		layout.label(text="shortcutkey:R+Shift")
		layout.operator(MWID_OT_MoveObject.bl_idname, text="MoveObject")
		layout.label(text="shortcutkey:F+Shift")
		layout.prop(prefs,"Wheel_grid_distance",text = "Wheel_grid_distance")
		layout.prop(prefs,"Guide_Object_Option",text = "Guide_Object_Option")
		
#POSE MODE AREA------------------------------------------------------------

#	OPETATOR CLASS AREA***************************************************
class MWID_OT_Posebonetransform(bpy.types.Operator):
	bl_idname = "mwid.posebonetransform"
	bl_label = "PoseboneTransform"
	bl_description = "To Move Pose Bones with the Mouse Wheel"
	bl_options = {'REGISTER','UNDO'}
	
	init_matrix_basis = None
	apbone = None
	prefs = None
	countwheelrotation = 0

	@classmethod
	def poll(cls, context):
		return context.mode == 'POSE'

	#M:matrix,c:custum,r:rest,l:local,p:pose,larm:localarmature
	M_l_to_cpbone = None
	M_l_to_rpbone = None
	M_w_to_larm = None
	l = None


	def execute(self,context):
		return {'FINISHED'}

	def modal(self,context,event):

		#escキーで終了
		if (event.type == 'ESC') or (event.type == 'LEFTMOUSE'):
			self.prefs.modalrunning = False
			return {'FINISHED'}
		
		#ホイールのイベントからデプス値を設定
		self.countwheelrotation =  wheeleventpulse(event,self.countwheelrotation)
		
		#解像度を掛け算
		d = self.prefs.Wheel_grid_distance * self.countwheelrotation

		#イベントからマウスのリージョン座標を取得
		mouseregion = vector_rigion_by_mouse(context,event)
		#マウスの位置のローカル座標ベクトルを取得(これはあっている確認済)
		region,space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
		vector_mouse_world = view3d_utils.region_2d_to_location_3d(region,space.region_3d,mouseregion,Vector((d,0,0)))
		#ボーン座標上のy向き単位ベクトル
		vector_y = Vector((0,1,0))
		
		#ワールド座標からレストポーズ座標への変換行列を取得
		M_w_to_rpbone = self.M_l_to_rpbone @ self.M_w_to_larm

		#マウスのワールド座標ベクトルをレストポーズ座標へ変換
		V_m_rpbone = (M_w_to_rpbone @ vector_mouse_world) - self.l
		
		#ボーン座標のY軸方向ベクトルとマウスの座標ベクトルの回転を取得し回転。
		self.apbone.rotation_mode = 'QUATERNION'
		q = vector_y.rotation_difference(V_m_rpbone)
		self.apbone.rotation_quaternion = q

		#長さのスケールを変更
		if self.prefs.LengthOption :
			self.apbone.scale.y = V_m_rpbone.length/vector_y.length

		return {'RUNNING_MODAL'}

	def invoke(self, context, event):
		self.prefs = bpy.context.preferences.addons[__name__].preferences
		if not self.prefs.modalrunning:

			self.prefs.modalrunning = True
			mh = context.window_manager.modal_handler_add(self)

			self.countwheelrotation = 0

			self.apbone = bpy.context.active_pose_bone
			self.M_l_to_cpbone = matrixinvert(self.apbone.matrix)
			self.M_l_to_rpbone = self.apbone.matrix_basis @ self.M_l_to_cpbone
			self.M_w_to_larm = matrixinvert(bpy.context.active_object.matrix_world)
			#ポーズモードのローテーションを取得する。
			(l,q,s) = self.apbone.matrix_basis.decompose()
			self.l = l

			return {'RUNNING_MODAL'}

		else:
			self.prefs.modalrunning = False				
			return {'FINISHED'}

#	PANEL CLASS AREA*******************************************************************
class MWID_PT_OptoionPanelPose(bpy.types.Panel):
	bl_label = "MWID_PT_OptoionPanelPose"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "MWID"
	bl_context = "posemode"


	def draw(self,context):
		
		layout = self.layout
		prefs = bpy.context.preferences.addons[__name__].preferences
		layout.operator(MWID_OT_Posebonetransform.bl_idname, text="Posebonetransform")
		layout.label(text="shortcutkey:T+Shift")
		layout.prop(prefs,"Wheel_grid_distance",text = "Wheel_grid_distance")
		layout.prop(prefs,"LengthOption",text = "LengthOption")

#common area-------------------------------------------------
class MWID_Preferences(bpy.types.AddonPreferences):
	bl_idname = __name__

	modalrunning = False

	Wheel_grid_distance:FloatProperty(
		name="Wheel_grid_distance",
		description="Distance moved in one wheel rotation",
		default=0.5,
		min=0,
	)

	LengthOption:BoolProperty(
		name="LengthOption",
		description="Whether to change the length",
		default=False
	)

	Guide_Object_Option:BoolProperty(
		name="Guide_Object_Option",
		description="Whether to use guide balls or not",
		default=False
	)

addon_keymaps = []
def register_shortcut():
		wm = bpy.context.window_manager
		kc = wm.keyconfigs.addon
		if kc:
			km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
			km1 = km.keymap_items.new(
			idname=MWID_OT_RotationObject.bl_idname,
			type='R',
			value='PRESS',
			shift=True,
			ctrl=False,
			alt=False,
			)
		
			km2 = km.keymap_items.new(
			idname=MWID_OT_MoveObject.bl_idname,
			type='F',
			value='PRESS',
			shift=True,
			ctrl=False,
			alt=False,
			)

			km3 = km.keymap_items.new(
			idname=MWID_OT_Posebonetransform.bl_idname,
			type='T',
			value='PRESS',
			shift=True,
			ctrl=False,
			alt=False,
			)


		# ショートカットキー一覧に登録
		addon_keymaps.append((km, km1))
		addon_keymaps.append((km, km2))
		addon_keymaps.append((km, km3))

def unregister_shortcut():
	for km, kmi in addon_keymaps:
	# ショートカットキーの登録解除
	# 引数
	#   第1引数: km.keymap_items.newで作成したショートカットキー
	#            [bpy.types.KeyMapItem]
		km.keymap_items.remove(kmi)
	# ショートカットキー一覧をクリア
	addon_keymaps.clear()
	

def menu_fn_object(self,context):
	self.layout.separator()
	self.layout.operator(MWID_OT_RotationObject.bl_idname)
	self.layout.operator(MWID_OT_MoveObject.bl_idname)
	self.layout.separator()

def menu_fn_posemode(self,context):
	self.layout.separator()
	self.layout.operator(MWID_OT_Posebonetransform.bl_idname)

classes = [
	MWID_OT_RotationObject,
	MWID_Preferences,
	MWID_OT_MoveObject,
	MWID_PT_OBjectmodeOptionPaneleObject,
	MWID_OT_Posebonetransform,
	MWID_PT_OptoionPanelPose,
]


def register():
	for c in classes:
		bpy.utils.register_class(c)

	register_shortcut()
	#bpy.types.VIEW3D_MT_pose.prepend(menu_fn_posemode)
	#bpy.types.VIEW3D_MT_object.append(menu_fn_object)
	
	#bpy.types.VIEW3D_MT_object.prepend(menu_fn_object)


def unregister():
	unregister_shortcut()
	#bpy.types.VIEW3D_MT_pose.remove(menu_fn_posemode)
	#bpy.types.VIEW3D_MT_object.remove(menu_fn_object)
	
	for c in classes:
		bpy.utils.unregister_class(c)
		
if __name__ == "__main__":
	register()
