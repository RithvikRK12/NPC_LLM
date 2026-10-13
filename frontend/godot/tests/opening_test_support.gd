extends RefCounted
# Village regressions use the actual checkpoint endpoint on port 8001, then stage
# their existing village scenarios. Dedicated opening tests cover the full path.
static func arrive(scene: Node) -> bool:
	if not scene.cinematic:
		if scene.onboarding.owns_input(): scene.onboarding.dismiss(); scene.onboarding.advance(3.0)
		return true
	var session: Node=scene.opening
	session.set_process(false)
	session.director.advance_clock(59.8,false)
	var deadline:=Time.get_ticks_msec()+12000
	while not session.director.checkpoint_ready:
		await scene.get_tree().process_frame
		if Time.get_ticks_msec()>deadline:
			push_error("Disposable backend opening checkpoint timed out")
			scene.get_tree().quit(1)
			return false
	session.director.advance_clock(0.2,false)
	if scene.onboarding.owns_input(): scene.onboarding.dismiss(); scene.onboarding.advance(3.0)
	scene.player.position=Vector2.ZERO
	await scene.get_tree().process_frame
	return true
