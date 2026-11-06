extends Node2D
# The same surface scene is used by the stage and persistent beach.
const LAYOUT=preload("res://resources/island_layout.tres")
const BEACH=preload("res://resources/shipwreck_beach.tres")
var rock: Texture2D
var sand: Array[Texture2D] = []
var grass: Array[Texture2D] = []
var shallow: Array[Texture2D] = []
var wet: Array[Texture2D] = []
var paths: Array[Texture2D] = []
func _ready() -> void:
	rock=load("res://assets/cutscene/opening/coast-rock.svg")
	for i in range(4):
		sand.append(load("res://assets/cutscene/opening/sand-%s.svg" % i))
		grass.append(load("res://assets/world/grass-%s.svg" % i))
		shallow.append(load("res://assets/cutscene/opening/shallow-%s.svg" % i))
		wet.append(load("res://assets/cutscene/opening/wet-%s.svg" % i))
		paths.append(load("res://assets/world/path-%s.svg" % i))
func _draw() -> void:
	var coast_y: int=int(BEACH.data().coast_origin[1])
	for x in range(-70,71):
		var shore:=coast_y
		for y in range(coast_y/32-28,160):
			if LAYOUT.land_cell(Vector2i(x,y)): shore=(y+1)*32
		# Source-grid coastal water with several shallow shelves and broken foam.
		for depth in range(7,-1,-1):
			var tint: Color=[Color("8edbc3"),Color("71d2bd"),Color("59c7b5"),Color("45b6ab"),Color("39a49f"),Color("31928f"),Color("2d8286"),Color("2c7b82")][depth]
			draw_rect(Rect2(x*32,shore+depth*24,32,26),tint)
			if depth<3:
				draw_texture_rect(shallow[posmod(x+depth,4)],Rect2(x*32,shore+depth*24,32,32),false,Color.WHITE.darkened(depth*.07))
			for speck in range(3):
				var p:=Vector2(x*32+posmod(x*13+speck*11,15)*2,shore+depth*24+posmod(x*7+speck*3,10)*2)
				draw_rect(Rect2(p,Vector2(8,2)),tint.lightened(.06))
		for xx in range(0,32,4):
			var wave: float=round((sin((x*32+xx)*.018)+sin((x*32+xx)*.037))*3)*2
			for line in range(3):
				if line==1 and posmod(x*8+xx,7)==0: continue
				draw_rect(Rect2(x*32+xx,shore+10+line*26+wave,4,2 if line else 4),Color("e1eed0") if line!=1 else Color("b9e6cc"))
		for y in range(coast_y/32-28,mini(160,shore/32)):
			var cell:=Vector2i(x,y)
			if not LAYOUT.land_cell(cell): continue
			var margin: float=coast_y-320+sin(x*.29)*46+sin(x*.73)*18
			var textures: Array[Texture2D]=sand if y*32>margin else grass
			var variant:=posmod(x*7+y*13,4)
			draw_texture_rect(textures[variant],Rect2(x*32,y*32,32,32),false)
			if y*32>=shore-32: draw_texture_rect(wet[variant],Rect2(x*32,y*32+16,32,16),false)
			if absf(y*32-margin)<32:
				for i in range(7):
					var p:=Vector2(x*32+posmod(i*13+x,15)*2,y*32+posmod(x*7+i*11,15)*2)
					draw_rect(Rect2(p,Vector2(6,4)),Color("75944c")); draw_rect(Rect2(p+Vector2(2,-2),Vector2(2,4)),Color("9bb15e"))
			var at:=Vector2(cell*32)+Vector2(16,16)
			if preload("res://resources/south_scenery.tres").route_distance(at)<48 and y*32<coast_y-320:
				draw_texture_rect(paths[variant],Rect2(x*32,y*32,32,32),false)
	for offset in [Vector2(-280,-50),Vector2(320,-20)]:
		var at: Vector2=Vector2(0,coast_y)+offset
		draw_texture_rect(rock,Rect2(at-Vector2(48,88),Vector2(96,96)),false)
