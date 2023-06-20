import bpy
from bpy.props import FloatVectorProperty, EnumProperty
from mathutils import Vector
import math
import gpu
import gpu_extras.presets
from bpy.props import BoolProperty
from bpy_extras import view3d_utils
import bgl
import blf


bl_info = {
	"name":"borntransformbywheel",
	"author":"tanatan",
	"version":(0.1),
	"blender":(3,0,0),
	"locaton":"Rigging",
	"description":" transform of born to  depth  direction by mouse wheel",
	"warnig":"",
	"support":'TESTING',
	"wiki_url":"",
	"tracker_url":"",
	"category":"pose"
}

#アーマチェア座標からpose座標への変換行列を得るための関数
#objにアーマチェアを代入し、matrix_mapに空のマップオブジェクトを代入すると
#(ボーン名:local座標to pose座標の変換行列)マップりすとを得る)
def set_pose_matrices(obj, matrix_map):
	#"Assign pose space matrices of all bones at once, ignoring constraints."

	def rec(pbone, parent_matrix):
		if pbone.name in matrix_map:
			matrix = matrix_map[pbone.name]
			#print("matrix_map1:",matrix_map)

			# # Instead of:
			# pbone.matrix = matrix
			# bpy.context.view_layer.update()

			# Compute and assign local matrix, using the new parent matrix
			if pbone.parent:
				pbone.matrix_basis = pbone.bone.convert_local_to_pose(
					matrix,
					pbone.bone.matrix_local,
					parent_matrix=parent_matrix,
					parent_matrix_local=pbone.parent.bone.matrix_local,
					invert=True
				)
				#print("matrix_map2:",matrix_map)
			else:
				pbone.matrix_basis = pbone.bone.convert_local_to_pose(
					matrix,
					pbone.bone.matrix_local,
					invert=True
				)
				#print("matrix_map3:",matrix_map)
		else:
			# Compute the updated pose matrix from local and new parent matrix
			if pbone.parent:
				matrix = pbone.bone.convert_local_to_pose(
					pbone.matrix_basis,
					pbone.bone.matrix_local,
					parent_matrix=parent_matrix,
					parent_matrix_local=pbone.parent.bone.matrix_local,
				)
				#print("matrix_map4:",matrix_map)
			else:
				matrix = pbone.bone.convert_local_to_pose(
					pbone.matrix_basis,
					pbone.bone.matrix_local,
					)
				#print("matrix_map5:",matrix_map)

		# Recursively process children, passing the new matrix through
		for child in pbone.children:
			rec(child, matrix)
			#print("matrix_map6:",matrix_map)

		# Scan all bone trees from their roots
		for pbone in obj.pose.bones:
			if not pbone.parent:
				rec(pbone, None)
				#print("matrix_map7:",matrix_map)


def matrixinvert(matrix):
	minv = matrix.copy()
	minv.invert()
	return minv


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


def circledraw(context,target_point_world,wheeldepth,event):
	#print("circledrawhead")
	#xx = event.mouse_x * wheeldepth
	region, space = get_region_and_space(
		context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
	)
	if (region is None) or (space is None):
		return

	vec = view3d_utils.location_3d_to_region_2d(
		region,
		space.region_3d,
		Vector(target_point_world)
	)

	color = [1,1,1,1]
	#print("circledraw22")
	gpu_extras.presets.draw_circle_2d(Vector((20,20)),color,100)#vec,color,50)#wheeldepth)

	
	context.area.tag_redraw()



def textdraw(context,event,target_point_world):
	j = 1
	print("textdraw")
	'''
	blf.size(0, 100, 72)
	blf.position(0,100,100,0)
	blf.draw(0, "hhhhhhhhhh")
	'''
	
	if not(dammy22.wacthvalue1 is None):
		for k1,k2 in dammy22.wacthvalue1.items():
			
			blf.size(0, 40, 72)
			blf.position(0,100,j*100,0)
			blf.draw(0, "("+str(k1)+"\n"+str(k2)+")")
			j = j +1
	

#ハンドルには一つの関数しか入れられないので一つにまとめる。
def drawhandlefunc(context,target_point_world,wheeldepth,event):
	#circledraw(context,target_point_world,wheeldepth)
	circledraw(context,target_point_world,wheeldepth,event)
	textdraw(context,event,target_point_world)

# TODO: #マウスの位置にボーンを回転させる。
def active_posebone_head_go_by_mouse(context,event,wheelvalue,wheelvaluescale):

	wacthvalue1 = {}

	print("active_posebone_head_go_by_mouse is head")
	active_obj = bpy.context.active_object
	region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
	target_point_vecter_region = Vector((event.mouse_region_x,event.mouse_region_y))
	target_point_vecter_world  = view3d_utils.region_2d_to_location_3d(region,space.region_3d,target_point_vecter_region,Vector((wheelvalue*wheelvaluescale,0,0)))
	
	# TODO: テスト用に変更する（2023/05/27)
	test_target_point_vecter_world  = bpy.data.objects['球'].location.copy()
	wtl = active_obj.matrix_world.copy()
	wtl.invert()
	test_target_point_vecter_local = wtl @ test_target_point_vecter_world
	
	world_to_local_matrix  = active_obj.matrix_world.copy()
	world_to_local_matrix.invert()
	#local_to_world_matrix = active_obj.matrix_world.copy()
	#world_to_local_matrix  = local_to_world_matrix.invert()
	target_point_vecter_local = world_to_local_matrix @ target_point_vecter_world

	if active_obj.type == 'ARMATURE':
		#アクティブボーンとアクティブポーズボーンを取得
		abone  =  bpy.context.active_bone
		aposebone =  bpy.context.active_pose_bone

		#ローカル座標→ポーズ座標の変換行列
		local_to_pose_matrix = aposebone.matrix.copy()
		local_to_pose_matrix.invert()

		# TODO: 子ボーンのマトリックスはpose状態の親から取得しないといけない？#ローカル座標→レスト座標
		if not (aposebone.parent is None):
			#第一案
			#local_to_edit = aposebone.parent.matrix_basis.copy()
			#local_to_edit.invert()

			#第二案
			'''
			M = aposebone.bone.convert_local_to_pose(
				matrix = aposebone.matrix, #matrix = aposebone.matrix_basis,
				matrix_local = aposebone.bone.matrix_local,
				parent_matrix = aposebone.parent.matrix,
				parent_matrix_local = aposebone.parent.bone.matrix_local,
				invert = True
			)
			M2 = aposebone.matrix_basis.copy()
			local_to_edit =  M2 @ M 
			'''
			
			#第三案ポーズのマトリックスそのまま
			
			#local_to_edit = aposebone.matrix.copy()
			#local_to_edit.invert()

			#第四案Editのマトリックスそのまま
			#local_to_edit = abone.matrix_local.copy()
			#local_to_edit.invert()

			#第五案 Editに親ボーンのローテーションを作用させる
			'''
			local_to_edit = abone.matrix_local.copy()
			local_to_edit.invert()

			for ap in aposebone.parent_recursive :
				ap 

			'''
			#第六案matrixとmatrixbasisの組み合わせ
			NP = aposebone.matrix.copy()
			NP.invert()

			local_to_edit = aposebone.matrix_basis @ NP

		else:
			local_to_edit = abone.matrix_local.copy()
			local_to_edit.invert()
		
		#convertを使ったlocal座標→parentrestbone変換行列
		#if not (aposebone.parent is None ):
		'''
		m1 = aposebone.matrix_basis
		m2 = aposebone.bone.matrix_local
		m3 = aposebone.parent.matrix_basis
		m4 = aposebone.parent.bone.matrix_local
		M = abone.convert_local_to_pose(m1,m2,parent_matrix=m3,parent_matrix_local=m4,invert=True)

		posebonehead_to_target_vector_pose =    M @ posebonehead_to_target_vector_local
		active_bone_vector_pose =  M @ active_bone_vector_lacal
		'''

		#else :
			#posebonehead_to_target_vector_pose = local_to_edit @ posebonehead_to_target_vector_local
			#active_bone_vector_pose = local_to_edit @ active_bone_vector_lacal

		#posebonehead_to_target_vector_pose = local_to_edit @ posebonehead_to_target_vector_local
		#active_bone_vector_pose = local_to_edit @ active_bone_vector_lacal

		#ローカル座標でのヘッドターゲットboneとrestボーンVector
		posebonehead_to_target_vector_local = target_point_vecter_local - aposebone.head #abone.tail
		active_bone_vector_lacal = abone.vector
		eeee = local_to_edit @ test_target_point_vecter_local 
		if not (aposebone.parent is None ):
			# TODO: testのために球の位置をターゲットにする。
			posebonehead_to_target_vector_pose = local_to_edit @ test_target_point_vecter_local - local_to_edit @ aposebone.head 
			#posebonehead_to_target_vector_pose = local_to_edit @ target_point_vecter_local - local_to_edit @ aposebone.head
			active_bone_vector_pose = local_to_edit @ aposebone.tail - local_to_edit @ aposebone.head
		else:
			posebonehead_to_target_vector_pose = local_to_edit @ target_point_vecter_local - local_to_edit @ aposebone.head
			active_bone_vector_pose = local_to_edit @ abone.tail_local - local_to_edit @ abone.head_local
		
		#q = active_bone_vector_pose.rotation_difference(Vector((0,2,3)))
		q = active_bone_vector_pose.rotation_difference(posebonehead_to_target_vector_pose)

		#q = active_bone_vector_lacal.rotation_difference(posebonehead_to_target_vector_local)
		#q = posebonehead_to_target_vector_local.rotation_difference(active_bone_vector_lacal)
		#q = active_bone_vector_lacal.rotation_difference(target_point_vecter_world)
		#q = active_bone_vector_pose.rotation_difference(posebonehead_to_target_vector_pose)
		#q_pose = local_to_pose_matrix @ q.to_matrix().to_4x4()

		#aposebone.matrix = q_pose @ aposebone.matrix
		bpy.context.active_pose_bone.rotation_quaternion = q #@ bpy.context.active_pose_bone.rotation_quaternion
		#bpy.context.active_pose_bone.scale.y = abs(posebonehead_to_target_vector_local.length)/abs(abone.length)
		
		
		debuglis = [target_point_vecter_region,
	 			target_point_vecter_world,
				target_point_vecter_local,
				posebonehead_to_target_vector_local,
				posebonehead_to_target_vector_pose,
				active_bone_vector_pose
				]
		'''
		i = 0
		for k1 in  debuglis :
			
			rounded_vec = Vector((round(x, 1) for x in k1))
			#wacthvalue1[str(i)] = rounded_vec
			wacthvalue1.update({str(i):rounded_vec})#debuglis.index(k1)):rounded_vec})
			i = i +1
		'''

		
		wacthvalue1.update({
			"target_point_vecter_region":target_point_vecter_region,
			"target_point_vecter_world" :target_point_vecter_world,
			"target_point_vecter_local":target_point_vecter_local,
			"posebonehead_to_target_vector_local":posebonehead_to_target_vector_local,
			"posebonehead_to_target_vector_pose":posebonehead_to_target_vector_pose,
			"active_bone_vector_pose":active_bone_vector_pose
				})
		
		
		

	#ロケーションプロパティを持たないオブジェクトを除去できていない？
	elif active_obj.get("location") is not None:
		active_obj.location = target_point_vecter_world

	else:
		print("this object has not locaiton propaty,please select locationable object")
	print("wacthvalue1",wacthvalue1)
	return wacthvalue1

		




class dammy22(bpy.types.Operator):
	print("dammy22classhead******************************************")

	bl_idname = "test.dammy22"
	bl_label = "transform to born depth"
	bl_description = "transform of born to  depth  direction by mouse wheel"
	#bl_options = {'REGISTER','UNDO'}

	__modalrunning = False
	__countmodal = 0
	__select_location = [0,0,0]
	__drawhandle = None
	#でバグ用
	wacthvalue1 = {}
	__ddvec = Vector((0,0,0))

	wheelvalue = 0

	
	

	#target_point_worldは位置ベクトル、target_point_worldに設定された点に進む
	def active_posebone_head_go_by_3Dpoint(self,context,target_point_world):
		#print("active_posebone_head_go",target_point_world)


		active_obj = context.active_object
		region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
		#vec = view3d_utils.location_3d_to_region_2d(region,space.region_3d,Vector(target_point_world))
		#target_vecter_world = view3d_utils.region_2d_to_vector_3d(region, space.region_3d, mv)


		if isinstance(target_point_world, (Vector,tuple,list)):
			if isinstance(target_point_world,(tuple,list)):
				target_point_world = Vector(target_point_world)
		else:
			#print("target_point_worldの型がおかしいです",target_point_world)
			pass
		#print(target_point_world)
		
		if active_obj.type == 'ARMATURE' :
						
			#print("active_obj.type =='bone'\n")
			active_pbone =  bpy.context.active_pose_bone
			active_bone  =  bpy.context.active_bone

			#vec_tworld = Vector(target_point_world)#4

			#実験済み座標変換
			#w：ワールド座標、l:ローカル座標系、r:レストボーン座標、pr:ルートポーズボーン座標
			w_to_l = bpy.context.active_object.matrix_world.copy()
			w_to_l.invert()

			l_to_r = bpy.context.active_bone.matrix_local.copy()
			l_to_r.invert()

			r_to_pr = bpy.context.active_pose_bone.matrix_basis.copy()
			r_to_pr.invert()

			w_to_pr =r_to_pr @ l_to_r @ w_to_l 

			tvec_pr = w_to_pr @ target_point_world
			vec_posebone_psys =r_to_pr @ l_to_r @ bpy.context.active_pose_bone.tail - r_to_pr @ l_to_r @ bpy.context.active_pose_bone.head
			q = vec_posebone_psys.rotation_difference(tvec_pr)

			#回転
			bpy.context.active_pose_bone.rotation_quaternion = q
			#実験済み座標変換ここまで
			
			#スケールの変更
			bpy.context.active_pose_bone.scale.y = target_point_world.length/vec_posebone_psys.length
		
		else:
			#print("else:")
			active_obj.scale = active_obj.scale * 2
			active_obj.location = active_obj.location + self.select_location

		
			#active_obj.location = select_location

			
		#print("FINISHED-----------------------------------------------------------")
		#return {'FINISHED'}

	def active_posebone_head_go_by_event(self,context,event):
		key_x = event.mouse_x
		key_y = event.mouse_y
		active_obj = context.active_object
		region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
		#vec = view3d_utils.location_3d_to_region_2d(region,	space.region_3d,Vector(target_point_world))
		target_vecter_world = view3d_utils.region_2d_to_vector_3d(region, space.region_3d,Vector((event.mouse_x,event.mouse_y)))
		self.active_posebone_head_go_by_3Dpoint(context,target_vecter_world)
		

	#dammy22インスタンスに帰属するプロパティなのでオペレータが完了されたら解放される？
	select_location:FloatVectorProperty( 
		
		name = "select_location",
		description = "",
		default = [1,1,1],
		subtype = 'XYZ',
		unit = 'LENGTH',
		#update = testmonono
	)

	@classmethod
	def is_modalrunning(cls):
		return cls.__modalrunning


	@classmethod
	def __drawhandle_add(cls,context,target_point_world,wheeldepth,event):
		if cls.__drawhandle is None:
			cls.__drawhandle = bpy.types.SpaceView3D.draw_handler_add(
				drawhandlefunc, (context,target_point_world,wheeldepth,event), 'WINDOW', 'POST_PIXEL'
				)
		print("drawhandleadd***********************************")

	@classmethod
	def __drawhandle_remove(cls, context):
		if not(cls.__drawhandle is  None):
		
			bpy.types.SpaceView3D.draw_handler_remove(
				cls.__drawhandle, 'WINDOW'
			)
			cls.__drawhandle = None
			print("drawhandleremove**************************************")


	
	

	def execute(self,context):
		print("excutestart*******************************************************")
		
		#self.active_posebone_head_go_by_3Dpoint(context,self.select_location)

		return {'FINISHED'}




	def modal(self,context,event):
		print("modalhead*********************************************")
	
		if context.area:
			#print("redraw")
			
			context.area.tag_redraw()

		#print("self.select_location on modalhead",self.select_location)
		
		
		if not self.is_modalrunning():
			print("cancellmodal*************************************")
			return{'CANCELLED'}

		if event.type == 'ESC':
			print("Pushesc*****************************************")
			#self.active_posebone_head_go_by_3Dpoint(context,self.select_location)

			context.area.tag_redraw()
			#print("select_location[2]on finish",self.select_location[2])
			#__select_locationは廃止、パススルーにして直接プロパティを動かす。
			#self.select_location = self.__select_location
			#print("select_location on modalfinish",self.select_location)

			#モーダルモードステータスオフ、ハンドラの解除ポーズモードになるはず。
			dammy22.__modalrunning = False
			print("callmodalremovefunc************************************************")
			self.__drawhandle_remove(context)
			self.__drawhandle = None
			#context.area.tag_redraw()

			print("ESC MODAL FINISH*************************************")
			return {'FINISHED'}
		if event.value == 'PRESS':
			if event.type == 'WHEELUPMOUSE':
				self.wheelvalue = self.wheelvalue + 1
				return {'RUNNING_MODAL'}
			
			if event.type == 'WHEELDOWNMOUSE':
				self.wheelvalue = self.wheelvalue - 1
				return {'RUNNING_MODAL'}
			
			if event.type == 'MIDDLEMOUSE': 
				self.wheelvalue = 0
				return {'RUNNING_MODAL'}
			if event.type == 'Y':
				return {'PASS_THROUGH'}
		
		#if event.type == 'MOUSEMOVE':
			#return {'PASS_THROUGH'}


		dc = active_posebone_head_go_by_mouse(context,event,self.wheelvalue,1)
		dammy22.wacthvalue1.update(dc)
		dammy22.__ddvec = dc
		print("updatewacthvalue1",dammy22.wacthvalue1)


		'''
		region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
		#マウスの操作をプロパティに渡してボーンを動かす関数を呼び出す。
		##print("eventtype:",event.type,"event.value",event.value)

		key_x = event.mouse_x
		key_y = event.mouse_y
		self.report({'INFO'}, "Mouse coords are %d %d" % (key_x, key_y))
		vec_mouse_3D = Vector((0,0,0))
		#三次元に直す。
		mouse_vec_3d = view3d_utils.region_2d_to_vector_3d(
                region,
                space.region_3d,
                Vector((event.mouse_x,event.mouse_y))
            )
		print("mouse_vec_3d",mouse_vec_3d)
		#リージョンとスペースの取得
		#3Dに変換
		self.select_location = mouse_vec_3d

		if event.type == 'WHEELUPMOUSE' and event.value == 'PRESS' :
			self.select_location[2] = self.select_location[2] + 1
			#print("wheelupcount",self.select_location)
		
		if event.type == 'WHEELDOWNMOUSE' and event.value == 'PRESS' :
			self.select_location[2] = self.select_location[2] - 1
			#print("wheeldowncount",self.select_location)
		
		if event.type == 'MIDDLEMOUSE' and event.value == 'PRESS' :
			self.select_location = [0,0,0]
			#print("wheelMIDDLEMOUSEcount",self.select_location)

		if event.type == 'MOUSEMOVE' :
			#工１　後でマウスを置換する。
			mouse_vec_3d = view3d_utils.region_2d_to_vector_3d(
                region,
                space.region_3d,
                Vector((event.mouse_x,event.mouse_y))
            )
			self.select_location[0] = mouse_vec_3d[0]
			self.select_location[1] = mouse_vec_3d[1]

		#self.select_location = self.__select_location
		#print("select_location[2]modalfutter",self.select_location)
		self.active_posebone_head_go_by_3Dpoint(context,self.select_location)
		'''


		context.area.tag_redraw()
		#パススルーだとカスタムプロパティは動くが、ボーンを動かす関数がは動かない。→プロパティのアップデートに入れないとだめ？
		return {'PASS_THROUGH'}

		#モーダルモードだとシェーダしか動かない。おわってから処理をする。
		#return {'RUNNING_MODAL'}

	def invoke(self, context, event):
		key_x = event.mouse_x
		key_y = event.mouse_y
		self.report({'INFO'}, "Mouse coords are %d %d" % (key_x, key_y))
		print("invoke")

		if context.area.type == 'VIEW_3D':
			# パネル [Delete Faces] のボタン [Start] が押されたときの処理
			if not self.is_modalrunning():
				dammy22.__modalrunning = True

				# モーダルモードを開始
				print("invokemodalhandleadd***********************************************************************")
				mh = context.window_manager.modal_handler_add(self)
				#print("Sample 2-5: Start modal mode ","(Delete faces by right mouse click)")
				#print("modalstar__select_location",self.select_location)
				#self.select_location = self.__select_location

				if self.__drawhandle is None:
					print("invokeCalladddrawhandle*****************************************************")
					self.__drawhandle_add(context,self.select_location,self.select_location[2],event)
				elif not(self.__drawhandle is None):
					#print("invokeCallremove************************************************************")
					self.__drawhandle_remove(context)

				return {'RUNNING_MODAL'}

			# パネル [Delete Faces] のボタン [Stop] が押されたときの処理
			else:
				dammy22.__modalrunning = False
				print("modal invoke finish********************************************************")
			return {'FINISHED'}
		else:
			return {'CANCELLED'}
		
		return {'FINISHED'}


class DAMMY22_PT_PaneleObject(bpy.types.Panel):
	bl_label = "dammy22"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "dammy22"
	bl_context = "posemode"
	
	def draw(self,context):
		#print("draw on DAMMYpanel")
		mylayout = self.layout
		#props = mylayout.operator(dammy22.bl_idname)
		if not dammy22.is_modalrunning():
			mylayout.operator(dammy22.bl_idname, text="Start", icon='PLAY')

		else:
			mylayout.operator(dammy22.bl_idname, text="Stop", icon='PAUSE')
	


def menu_fn(self,context):
	self.layout.separator()
	self.layout.operator(dammy22.bl_idname)


classes = [
	dammy22,
	DAMMY22_PT_PaneleObject,

]


def register():
	for c in classes:
		bpy.utils.register_class(c)
	bpy.types.VIEW3D_MT_pose.append(menu_fn)

def unregister():
	bpy.types.VIEW3D_MT_pose.remove(menu_fn)
	for c in classes:
		bpy.utils.unregister_class(c)

if __name__ == "__main__":
	register()
