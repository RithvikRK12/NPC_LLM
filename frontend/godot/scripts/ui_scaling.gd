extends RefCounted
# UI uses logical units; simulation and world-camera magnification stay separate.
static func factor(window: Vector2) -> float:
	return maxf(1.0,minf(window.x / 1280.0,window.y / 720.0))
