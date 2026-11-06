extends SceneTree
func _initialize() -> void: call_deferred("run")
func label(at: Vector2,text: String,size: int=18) -> void:
	var l:=Label.new(); l.text=text; l.position=at; l.add_theme_font_size_override("font_size",size); root.add_child(l)
func run() -> void:
	root.size=Vector2i(1280,900)
	var background:=ColorRect.new(); background.color=Color("254b61"); background.size=Vector2(1280,900); root.add_child(background)
	var layout=load("res://resources/island_layout.tres")
	var map:=Node2D.new(); map.position=Vector2(620,440); map.scale=Vector2(.06,.06); root.add_child(map)
	var land:=Polygon2D.new(); land.polygon=layout.polygon(); land.color=Color("72934f"); map.add_child(land)
	for x in range(-8192,8193,1024):
		var line:=Line2D.new(); line.points=PackedVector2Array([Vector2(x,-6144),Vector2(x,6144)]); line.width=12; line.default_color=Color(1,1,1,.1); map.add_child(line)
	for y in range(-6144,6145,1024):
		var line:=Line2D.new(); line.points=PackedVector2Array([Vector2(-8192,y),Vector2(8192,y)]); line.width=12; line.default_color=Color(1,1,1,.1); map.add_child(line)
	for region in layout.data().regions:
		if region.id=="perimeter": continue
		var b: Array=region.bounds
		var box:=Polygon2D.new(); box.polygon=PackedVector2Array([Vector2(b[0],b[1]),Vector2(b[0]+b[2],b[1]),Vector2(b[0]+b[2],b[1]+b[3]),Vector2(b[0],b[1]+b[3])]); box.color=Color(.5,.7,.9,.25) if region.status=="reserved" else Color(1,.8,.3,.22); map.add_child(box)
		label(Vector2(620,440)+Vector2(b[0]+80,b[1]+100)*.06,region.id.to_upper()+" · "+region.status)
	for route in layout.data().routes:
		var line:=Line2D.new(); line.width=36; line.default_color=Color("edce8b")
		for p in route: line.add_point(Vector2(p[0],p[1]))
		map.add_child(line)
	for entry in JSON.parse_string(FileAccess.get_file_as_string("res://resources/village_layout.json")):
		var at: Array=entry.at
		var mark:=Polygon2D.new(); var p:=Vector2(at[0],at[1]); mark.polygon=PackedVector2Array([p-Vector2(24,24),p+Vector2(24,-24),p+Vector2(24,24),p+Vector2(-24,24)]); mark.color=Color("f7dfaf"); map.add_child(mark)
	label(Vector2(24,16),"ISLAND CAPACITY BLOCKOUT · map v2 · 16,384 × 12,288 world units",26)
	label(Vector2(24,54),"32-unit terrain grid · 1,024-unit chunks · closed irregular coast · ≥1,024-unit ocean margins")
	label(Vector2(24,800),"Usable land: 106,363,904 wu² after 64-unit coast exclusion\nCurrent region budgets: 34,051,840 wu² · uncommitted reserve: 67.99% (minimum 35%)\nGold: launch content / routes · blue: future reservations · pale marks: existing village props",19)
	label(Vector2(650,740),"WRECK / ARRIVAL (0,3840)\nNorth → Willowbrook: 3,662.307 wu / 20.346 s",18)
	await process_frame; await process_frame; await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(ProjectSettings.globalize_path("res://../../docs/evidence/starting-cutscene/second-pass/island-overview.png"))
	quit()
