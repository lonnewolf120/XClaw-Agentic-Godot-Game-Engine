extends Node
# VibeCore Trait Applier
# Safely attaches modular logic (Traits) to existing nodes at runtime.

static func add(target: Node, trait_name: String) -> Node:
	if not target:
		print("[VibeTraits] Error: Target node is null")
		return null
		
	var path = "res://vibe_core/traits/" + trait_name + "Trait.gd"
	if not FileAccess.file_exists(path):
		# Fallback to local scripts if not in core
		path = "res://scripts/traits/" + trait_name + "Trait.gd"
		
	if not FileAccess.file_exists(path):
		print("[VibeTraits] Error: Trait not found at ", path)
		return null
		
	var trait_script = load(path)
	var trait_node = Node.new()
	trait_node.name = trait_name + "Trait"
	trait_node.set_script(trait_script)
	
	target.add_child(trait_node)
	print("[VibeTraits] Applied ", trait_name, " to ", target.name)
	return trait_node

static func has_trait(target: Node, trait_name: String) -> bool:
	return target.has_node(trait_name + "Trait")
