extends Node
const T = preload("res://scenes/cutscenes/opening/opening_times.gd")
var ambience_owner: Node
var ambience: AudioStreamPlayer
var wind: AudioStreamPlayer
var voices: Array[AudioStreamPlayer] = []
var fired: Array[StringName] = []
var silent := false
func _ready() -> void:
	ambience=_voice("surf",true,ambience_owner)
	wind=_voice("wind",true)
func _voice(id: String,loop: bool=false,owner_node: Node=null) -> AudioStreamPlayer:
	var player:=AudioStreamPlayer.new()
	var path: String="res://assets/cutscene/opening/%s.wav" % id
	if ResourceLoader.exists(path):
		player.stream=load(path)
		if loop and player.stream is AudioStreamWAV:
			player.stream.loop_begin=0
			player.stream.loop_end=int(player.stream.get_length()*player.stream.mix_rate)
			player.stream.loop_mode=AudioStreamWAV.LOOP_FORWARD
	else: push_warning("Optional opening sound unavailable: "+path)
	player.volume_db=-18 if loop else -10
	if owner_node!=null: owner_node.add_child(player)
	else: add_child(player)
	voices.append(player)
	return player
func trigger(id: StringName) -> void:
	if fired.has(id): return
	fired.append(id)
	var sounds={&"keel_contact":"impact",&"splinters":"crack",&"mast_break":"mast",&"deck_wash":"splash",&"player_fall":"cloth"}
	var text:=String(id)
	for prefix in ["creak","bird","cloth","step"]:
		if text.begins_with(prefix+"_"): sounds[id]=prefix
	if sounds.has(id):
		var voice:=_voice(sounds[id])
		if voice.stream: voice.play()
func sample_mix(t: float) -> void:
	silent=t>=T.SILENCE and t<T.SURF_RETURN
	for voice in voices:
		if silent: voice.stop()
	if silent: return
	if not ambience.playing and ambience.stream: ambience.play()
	ambience.volume_db=-22 if t<T.REVEAL else -17
	if t<T.BLACKOUT:
		if not wind.playing and wind.stream: wind.play()
		wind.volume_db=-18 if t<T.UNEASE else (-27 if t>=T.SUSPENSE and t<T.REVEAL else -14)
	else: wind.stop()
func set_paused(value: bool) -> void:
	for voice in voices: voice.stream_paused=value
func reset() -> void:
	for voice in voices.duplicate():
		voice.stop()
		if voice!=wind and voice!=ambience: voices.erase(voice); voice.queue_free()
	fired.clear()
func finish() -> void:
	# Calm surf persists seamlessly after the one-shot voices stop.
	for voice in voices:
		if voice!=ambience: voice.stop()

func _exit_tree() -> void:
	for voice in voices:
		if not is_instance_valid(voice): continue
		voice.stop()
		voice.stream=null
		if voice.get_parent()!=self: voice.queue_free()

func take_ambience() -> AudioStreamPlayer:
	var voice:=ambience
	voices.erase(voice)
	ambience=null
	return voice
