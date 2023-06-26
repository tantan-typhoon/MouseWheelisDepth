import typing
import bpy
from bpy.props import IntProperty,FloatVectorProperty, EnumProperty,FloatProperty
from bpy.types import Context, Event
from mathutils import *
import math
import gpu
import gpu_extras.presets
from bpy.props import BoolProperty
from bpy_extras import view3d_utils
import bgl
import blf


bl_info = {
	"name":"borntransformbywheel_ver02",
	"author":"tanatan",
	"version":(0.1),
	"blender":(3,0,0),
	"locaton":"Rigging",
	"description":" transform of born to  depth  direction by mouse wheel",
	"warnig":"",
	"support":'COMMUNITY',
	"wiki_url":"",
	"tracker_url":"",
	"category":"pose"
}


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

#逆変換を求める関数
def matrixinvert(matrix):
	minv = matrix.copy()
	minv.invert()
	return minv

#動作チェック済み（正常）
#マウスをリージョン座標に変換する。
def vector_rigion_by_mouse(context,event):
	vm = Vector((event.mouse_region_x,event.mouse_region_y))
	return vm

#動作チェック済み（正常）
#リージョン座標ベクトルををローカル座標ベクトルに変換する。
#第一引数リージョン座標上の位置ベクトル、第二引数ローカル座標に対応するオブジェクト、第三引数深さベクトル(Vector((x,0,0))でxの値のみ有効になる）戻り値ローカル座標上のベクトル。
def convert_region_to_local(context,vector_region,obj_local,depth):
	region, space  = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
	vector_world = view3d_utils.region_2d_to_location_3d(region,space.region_3d,vector_region,Vector((depth,0,0)))
	matrix_world_to_local = matrixinvert(obj_local.matrix_world)
	return (matrix_world_to_local @ vector_world)

# TODO: #動作不具合:matrix_basisが回転してしまうのでできない。
def convert_region_to_restlocal(context,vector_region,obj_local,depth):
	region, space  = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
	vector_world = view3d_utils.region_2d_to_location_3d(region,space.region_3d,vector_region,Vector((depth,0,0)))
	matrix_world_to_restlocal = matrixinvert(obj_local.matrix_basis)
	return matrix_world_to_restlocal @ vector_world 

#動作チェック済み
#親のcostumposeに依存した子のrestposebone座標（親カスタム子レスト）とlocal座標の位置ベクトルをrestpose座標変換する。
#第一引数pose座標に当たるposeボーンオブジェクト,第二引数変換したいローカル座標のベクトル
def convert_local_to_custumrestpose(aposebone,local_vector):
	local_to_custumpose = matrixinvert(aposebone.matrix)
	local_to_restpose = aposebone.matrix_basis @ local_to_custumpose
	return local_to_restpose @ local_vector

#動作チェック済み
#二つのベクトルのローテーションをクオータニオンで取得。
def vector_rotaion_quaternion(v1,v2):
	q = v1.rotation_difference(v2)
	return q

# TODO: 動作未チェック
#オブジェクトをクオータニオンで回転させる
def rotation_object_quaternion(quaternion,obj):
	obj.rotation_mode = 'QUATERNION'
	obj.rotation_quaternion = quaternion

# TODO: 動作未チェック
#matrix_basisを単位行列でリセットしてからベクトルとローテーションを得る関数
#第一引数は回転したい方向ベクトル（ローカル座標）、第二引数はオブジェクトの基準方向（ローカル）、第三引数は回転させるオブジェクト
def restrotation(target_vector_local,obj_vector_local,obj):
	(l,q,s) = obj.matrix_basis.decompose()
	Matrix_rotation_reset = Matrix.LocRotScale(l,Quaternion((1.0,0.0,0.0,0.0)),s)
	obj.matrix_basis = Matrix_rotation_reset
	obj.rotation_mode = 'QUATERNION'
	q = obj_vector_local.rotation_difference(target_vector_local)
	obj.rotation_quaternion = q



# TODO: #座標変換がなに座標から何座標への変換なのかしらべる。終点だけ固定して始点を動かす（逆ベクトルを使う）。v1 = M @ v2
#必要な情報：最初の座標行列、後の座標行列、変換行列。あるオブジェクトの位置座標を変換して
def check_convert_system():
	#ある座標（farst system)に存在していることがわかっているオブジェクト
	#
	return

# TODO: #マウスの位置にボーンを回転させる。
def active_posebone_head_go_by_mouse(context,event,wheelvalue,wheelvaluescale):

	wacthvalue1 = {}

	print("active_posebone_head_go_by_mouse is head")
	active_obj = bpy.context.active_object
	region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
	target_point_vecter_region = Vector((event.mouse_region_x,event.mouse_region_y))
	target_point_vecter_world  = view3d_utils.region_2d_to_location_3d(region,space.region_3d,target_point_vecter_region,Vector((wheelvalue*wheelvaluescale,0,0)))
	world_to_local_matrix  = active_obj.matrix_world.copy()
	world_to_local_matrix.invert()
	#local_to_world_matrix = active_obj.matrix_world.copy()
	#world_to_local_matrix  = local_to_world_matrix.invert()
	target_point_vecter_local = world_to_local_matrix @ target_point_vecter_world

	if active_obj.type == 'ARMATURE':
		abone  =  bpy.context.active_bone
		apbone =  bpy.context.active_pose_bone
		local_to_pose_matrix = apbone.matrix.copy()
		local_to_pose_matrix.invert()
		
		posebonehead_to_target_vector_local = target_point_vecter_local - apbone.head 
		active_bone_vector_lacal = abone.vector

		q = active_bone_vector_lacal.rotation_difference(posebonehead_to_target_vector_local)
		
		q_pose = local_to_pose_matrix @ q.to_matrix().to_4x4()

		bpy.context.active_pose_bone.rotation_quaternion = q 
		bpy.context.active_pose_bone.scale.y = abs(posebonehead_to_target_vector_local.length)/abs(abone.length)
		
		
		debuglis = [target_point_vecter_region,
	 			target_point_vecter_world,
				target_point_vecter_local,
				posebonehead_to_target_vector_local,
				#posebonehead_to_target_vector_pose,
				#active_bone_vector_pose,
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
			#"posebonehead_to_target_vector_pose":posebonehead_to_target_vector_pose,
			#"active_bone_vector_pose":active_bone_vector_pose
				})
		
		
		

	#ロケーションプロパティを持たないオブジェクトを除去できていない？
	elif active_obj.get("location") is not None:
		active_obj.location = target_point_vecter_world

	else:
		print("this object has not locaiton propaty,please select locationable object")
	print("wacthvalue1",wacthvalue1)
	return wacthvalue1

# TODO: 動作未チェック
#ホイールのeventからdepthに加減する数値を割り出す。
def wheeleventpulse(event,depth):#最初は０が入る
	if event.value == 'PRESS':
			if event.type == 'WHEELUPMOUSE':				
				return depth - 1			
			if event.type == 'WHEELDOWNMOUSE':
				return depth + 1
			if event.type == 'MIDDLEMOUSE': 
				return 0 
			
	return depth


#オブジェクトを使ってテストをするためのクラス。
class testdammy22(bpy.types.Operator):
	bl_idname = "test.testdammy22ver02"
	bl_label = "testdammy22ver02"
	bl_description = ""
	#bl_options = {'REGISTER','UNDO'}

	__modalrunning = False
	obj_sphere = None
	mvec= Vector((0,0,0))
	init_matrix_basis = None
	
	r_point:FloatVectorProperty( 
		
		name = "r_point",
		description = "",
		default = (0,0,0),
		subtype = 'XYZ',
		unit = 'LENGTH',
		#update = execute
	)

	@classmethod
	def is_modalrunning(cls):
		return cls.__modalrunning
	
	def execute(self,context):

		print("hello testdammy22")
		
		radius = 0.5
		location = Vector((0,0,5))
		#r_point = Vector((0,5,0))
		self.r_point =Vector((0,-5,0))
		
		bpy.ops.mesh.primitive_uv_sphere_add(radius= radius,location = location,align='CURSOR')
		obj_sphere = bpy.context.active_object
		obj_sphere.rotation_mode = 'QUATERNION'
		q = vector_rotaion_quaternion(location,self.r_point)
		obj_sphere.rotation_quaternion = q


		return {'FINISHED'}
	
	
	#モーダルモードの呼び出し
	def modal(self,context,event):
		print("run modal")

		region, space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')

		#escキーで終了
		if event.type == 'ESC':
			print("Pushesc")
			dammy22.__modalrunning = False
			return {'FINISHED'}
		
		#イベントからマウスのリージョン座標を取得
		mouseregion = vector_rigion_by_mouse(context,event)
		print(mouseregion)

		#このあたりが何かおかしい,ローテーションの位置
		#マウスの位置のローカル座標ベクトルを取得(これはあっている確認済)
		vector_world = view3d_utils.region_2d_to_location_3d(region,space.region_3d,mouseregion,Vector((0,0,0)))
	
		mvec_local = self.init_matrix_basis @ vector_world
		#print(mvec)
		self.obj_sphere.show_axis = True
		
		
		#restrotation(mvec,Vector((0,0,1)),self.obj_sphere)

		#第一引数が定数ベクトルだと上手く言っている。
		#restrotation(Vector((0,1,0)),Vector((0,0,1)),self.obj_sphere)
		restrotation(mvec_local,Vector((0,0,1)),self.obj_sphere)

		

		return {'RUNNING_MODAL'}
	
	# TODO: ここでrestの座標変換を変数に格納する。
	#最初の呼び出し
	def invoke(self, context, event):
		if context.area.type == 'VIEW_3D':
			
			if not self.is_modalrunning():
				
				# モーダルモードを開始
				dammy22.__modalrunning = True
				mh = context.window_manager.modal_handler_add(self)

				bpy.ops.mesh.primitive_uv_sphere_add(radius= 1,location = Vector((0,0,0)),align='CURSOR')
				self.obj_sphere = bpy.context.active_object
				self.obj_sphere.rotation_mode = 'QUATERNION'
				
				self.init_matrix_basis = self.obj_sphere.matrix_world.copy()

				return {'RUNNING_MODAL'}
				#return {'PASS_THROUGH'}
			
			else:
				#__modalrunningがtrueなら終了
				dammy22.__modalrunning = False				
				return {'FINISHED'}
		
	
		
# TODO: #bone用テストクラス
class testdammy22_bone(bpy.types.Operator):
	bl_idname = "test.testdammy22_bonever02"
	bl_label = "testdammy22_bonever02"
	bl_description = ""
	#bl_options = {'REGISTER','UNDO'}

	__modalrunning = False
	obj_sphere = None
	mvec_bone= Vector((0,0,0))
	
	depth = 0
	
	init_matrix_basis = None
	apbone = None
	#M:matrix,c:custum,r:rest,l:local,p:pose,larm:localarmature
	M_l_to_cpbone = None
	M_l_to_rpbone = None
	M_w_to_larm = None

	@classmethod
	def is_modalrunning(cls):
		return cls.__modalrunning

	def execute(self,context):
	
		
		ap = bpy.data.objects["アーマチュア"].pose.bones[2]
		
		local_vector = Vector((0,0,3))

		cdv = convert_local_to_custumrestpose(aposebone=ap,local_vector=local_vector)
		bpy.ops.mesh.primitive_cube_add(location=cdv)
		
	
	def modal(self,context,event):
		
		region,space = get_region_and_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
		#カスタムプロパティのためのsceneオブジェクトの取得
		scene = context.scene

		#escキーで終了
		if (event.type == 'ESC') or (event.type == 'LEFTMOUSE'):
			print("Pushesc")
			dammy22.__modalrunning = False
			return {'FINISHED'}
		
		#ホイールのイベントからデプス値を設定
		self.depth =  wheeleventpulse(event,self.depth)
		
		#解像度を掛け算
		d = scene.depthresolution * self.depth
		
		
		print("depth",scene.depthresolution)
		print("d",d)

		#イベントからマウスのリージョン座標を取得
		mouseregion = vector_rigion_by_mouse(context,event)
		#マウスの位置のローカル座標ベクトルを取得(これはあっている確認済)
		vector_mouse_world = view3d_utils.region_2d_to_location_3d(region,space.region_3d,mouseregion,Vector((d,0,0)))
		#ボーン座標上のy向き単位ベクトル
		vector_y = Vector((0,1,0))
		
		#ワールド座標からレストポーズ座標への変換行列を取得
		M_w_to_rpbone = self.M_l_to_rpbone @ self.M_w_to_larm

		#マウスのワールド座標ベクトルをレストポーズ座標へ変換
		V_m_rpbone = M_w_to_rpbone @ vector_mouse_world
		
		#ボーン座標のY軸方向ベクトルとマウスの座標ベクトルの回転を取得し回転。
		self.apbone.rotation_mode = 'QUATERNION'
		q = vector_y.rotation_difference(V_m_rpbone)
		self.apbone.rotation_quaternion = q

		#長さのスケールを変更
		if scene.LengthOption :
			self.apbone.scale.y = V_m_rpbone.length/vector_y.length
		

		print("rummodeal",mouseregion)
		return {'RUNNING_MODAL'}

	def invoke(self, context, event):

		if not self.is_modalrunning():
			# TODO: ここでレスト関数を取得				
			# モーダルモードを開始

			#初期化
			self.depth = 0
			

			dammy22.__modalrunning = True
			mh = context.window_manager.modal_handler_add(self)

			self.apbone = bpy.context.active_pose_bone
			self.M_l_to_cpbone = matrixinvert(self.apbone.matrix)
			self.M_l_to_rpbone = self.apbone.matrix_basis @ self.M_l_to_cpbone
			self.M_w_to_larm = matrixinvert(bpy.context.active_object.matrix_world)

		
			
			return {'RUNNING_MODAL'}

		else:
			dammy22.__modalrunning = False				
			return {'FINISHED'}


class dammy22(bpy.types.Operator):
	print("dammy22classhead******************************************")

	bl_idname = "test.dammy22ver02"
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

			context.area.tag_redraw()

			#モーダルモードステータスオフ、ハンドラの解除ポーズモードになるはず。
			dammy22.__modalrunning = False
			print("callmodalremovefunc************************************************")
			self.__drawhandle_remove(context)
			self.__drawhandle = None

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


		dc = active_posebone_head_go_by_mouse(context,event,self.wheelvalue,1)
		dammy22.wacthvalue1.update(dc)
		dammy22.__ddvec = dc
		print("updatewacthvalue1",dammy22.wacthvalue1)


		context.area.tag_redraw()
		#パススルーだとカスタムプロパティは動くが、ボーンを動かす関数がは動かない。→プロパティのアップデートに入れないとだめ？
		return {'PASS_THROUGH'}

		#モーダルモードだとシェーダしか動かない。おわってから処理をする。
		#return {'RUNNING_MODAL'}

	def invoke(self, context, event):
		print("invokehead")

		if context.area.type == 'VIEW_3D':
			# パネル [Delete Faces] のボタン [Start] が押されたときの処理
			if not self.is_modalrunning():
				dammy22.__modalrunning = True

				# モーダルモードを開始
				print("invokemodalhandleadd***********************************************************************")
				mh = context.window_manager.modal_handler_add(self)

				if self.__drawhandle is None:
					print("invokeCalladddrawhandle*****************************************************")
					self.__drawhandle_add(context,self.select_location,self.select_location[2],event)
				elif not(self.__drawhandle is None):
					
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


class DAMMY22VER2_PT_PaneleObject(bpy.types.Panel):
	bl_label = "dammy22ver2"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "dammy22"
	bl_context = "posemode"


	def draw(self,context):
		
		layout = self.layout

		#カスタムプロパティをシーンオブジェクトに格納しているのでシーンオブジェクトの読み込み
		scene = context.scene

		layout.operator(testdammy22_bone.bl_idname, text="WLD")
		layout.prop(scene,"depthresolution",text = "depthresolution")
		layout.prop(scene,"LengthOption",text = "scale change")
		
def init_props():
    scene = bpy.types.Scene
    scene.depthresolution = FloatProperty(
        name="depthresolution",
        description="Distance moved in one wheel revolution",
        default=1,
        min=0,
        #max=500
    )

	#ボーンの長さを変えるかどうかのオプション、Falseにすると向きだけが変わるようになる。
    scene.LengthOption = BoolProperty(
        name="LengthOption",
        description="Whether to change the length",
        default=True
    )

def clear_props():
    scene = bpy.types.Scene
    del scene.depthresolution
    del scene.LengthOption

addon_keymaps = []

def register_shortcut():
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        if kc:
            km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
            kmi = km.keymap_items.new(
            idname=testdammy22_bone.bl_idname,
            type='Q',
            value='PRESS',
            shift=True,
            ctrl=False,
            alt=False,
            )
        # ショートカットキー一覧に登録
        addon_keymaps.append((km, kmi))

def unregister_shortcut():
    for km, kmi in addon_keymaps:
    # ショートカットキーの登録解除
    # 引数
    #   第1引数: km.keymap_items.newで作成したショートカットキー
    #            [bpy.types.KeyMapItem]
        km.keymap_items.remove(kmi)
    # ショートカットキー一覧をクリア
    addon_keymaps.clear()
	


def menu_fn_pose(self,context):
	self.layout.separator()
	self.layout.operator(dammy22.bl_idname)
	self.layout.operator(testdammy22_bone.bl_idname)

def menu_fn_object(self,context):
	self.layout.separator()
	self.layout.operator(testdammy22.bl_idname)


classes = [
	dammy22,
	testdammy22,
	DAMMY22VER2_PT_PaneleObject,
	testdammy22_bone,

]


def register():
	for c in classes:
		bpy.utils.register_class(c)

	init_props()
	register_shortcut()
	bpy.types.VIEW3D_MT_pose.append(menu_fn_pose)
	bpy.types.VIEW3D_MT_object.append(menu_fn_object)


def unregister():
	unregister_shortcut()
	bpy.types.VIEW3D_MT_pose.remove(menu_fn_pose)
	bpy.types.VIEW3D_MT_object.remove(menu_fn_object)

	clear_props()
	for c in classes:
		bpy.utils.unregister_class(c)

if __name__ == "__main__":
	register()
