extends Node
# VibeCore: Global Event Bus
# Decouples game systems (e.g., combat doesn't need to know about the HUD).

signal game_started
signal game_over(success: bool)
signal level_completed(level_name: String)

signal player_spawned(player: Node)
signal player_died

signal score_changed(new_score: int)
signal health_changed(target: Node, current: float, max_health: float)

signal item_collected(item_name: String, amount: int)
signal notification_posted(message: String, type: String)

func emit_notification(msg: String, type: String = "info"):
	notification_posted.emit(msg, type)
	print("[VibeNotification] ", msg)
