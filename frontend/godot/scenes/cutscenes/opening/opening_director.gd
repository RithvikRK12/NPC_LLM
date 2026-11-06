extends Node
signal sampled(time: float)
signal cue(id: StringName)
signal shot_changed(id: StringName)
signal completed
const T = preload("res://scenes/cutscenes/opening/opening_times.gd")
const TIMING = preload("res://resources/cutscenes/opening_timing.tres")
var time := 0.0
var running := false
var paused := false
var focused := true
var fresh_hold := true
var checkpoint_ready := true
var waiting := false
var events: Array[String] = []
var generation := 0
var shot := -1
var rate := 1.0
func start() -> void:
	generation += 1
	time=0
	shot=-1
	events.clear()
	running=TIMING.valid()
	paused=false
	waiting=false
	fresh_hold=true
	_sample()
func set_paused(value: bool) -> void:
	paused=value
	if value: fresh_hold=false; rate=1
func set_focused(value: bool) -> void:
	focused=value
	fresh_hold=false
	rate=1
func cancel() -> void:
	generation+=1
	running=false
	waiting=false
	rate=1
	events.clear()
func preview_shot(id: StringName) -> void:
	start()
	seek(float(TIMING.boundaries[clampi(int(String(id).substr(1))-1,0,TIMING.boundaries.size()-2)]))
func seek(value: float) -> void:
	time=clampf(value,0,T.END)
	events.clear()
	_sample()
func _sample() -> void:
	var next: int = TIMING.shot_at(time)
	if next!=shot:
		shot=next
		shot_changed.emit(StringName("S%02d" % (shot+1)))
	sampled.emit(time)
func advance_clock(delta: float, held: bool) -> void:
	if not held: fresh_hold=true
	if not running or paused or not focused: rate=1; return
	rate=2 if held and fresh_hold else 1
	var target := minf(T.END,time+maxf(0,delta)*rate)
	if not checkpoint_ready: target=minf(target,T.BARRIER)
	waiting=not checkpoint_ready and target>=T.BARRIER
	# Split at every shot boundary and cue. No discarded remainder or method tracks.
	var stops: Array[float] = []
	for boundary in TIMING.boundaries:
		if boundary>time and boundary<=target: stops.append(boundary)
	for at in TIMING.cue_times:
		if at>time and at<=target and not stops.has(float(at)): stops.append(at)
	stops.sort()
	for at in stops:
		time=at
		_sample()
		for i in range(TIMING.cue_times.size()):
			if is_equal_approx(at,TIMING.cue_times[i]):
				var id: String = TIMING.cue_ids[i]
				if not events.has(id):
					events.append(id)
					cue.emit(StringName(id))
	time=target
	if T.END-time<0.00001 and checkpoint_ready: time=T.END
	_sample()
	if time==T.END:
		if not events.has("complete"): events.append("complete"); cue.emit(&"complete")
		running=false
		rate=1
		completed.emit()
