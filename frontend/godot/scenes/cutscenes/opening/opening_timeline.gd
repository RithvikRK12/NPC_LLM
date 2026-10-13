extends Resource
const T = preload("res://scenes/cutscenes/opening/opening_times.gd")
@export var boundaries: PackedFloat32Array = [0,6,22,28,30,33,39,43,49,57,60]
@export var cue_times: PackedFloat32Array = [1,13,20,33,33.3,34.2,35,35.4,39,45,48,51,53,54.5,56,57,58,59.5,60]
@export var cue_ids: PackedStringArray = ["creak_3","creak_4","creak_5","keel_contact","splinters","mast_break","deck_wash","player_fall","blackout","bird_1","bird_2","cloth_1","step_1","step_2","step_3","checkpoint","step_4","step_5","complete"]
func valid() -> bool:
	if boundaries.size()<2 or boundaries[0]!=0 or boundaries[-1]!=T.END or cue_times.size()!=cue_ids.size(): return false
	for i in range(boundaries.size()-1):
		if boundaries[i]>=boundaries[i+1]: return false
	for i in range(cue_times.size()):
		if cue_times[i]<=0 or cue_times[i]>T.END or (i>0 and cue_times[i]<=cue_times[i-1]): return false
	return true
func shot_at(t: float) -> int:
	for i in range(boundaries.size()-1):
		if t<boundaries[i+1]: return i
	return boundaries.size()-2
