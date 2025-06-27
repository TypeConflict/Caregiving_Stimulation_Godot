extends Node

func _ready():
	print("🔍 開始列出場景物件...\n")
	list_scene_objects()

func list_scene_objects():
	var root = get_tree().get_root()
	for node in root.get_children():
		explore_node(node)

func explore_node(node):
	if node is Node:
		var info = {
			"name": node.name,
			"type": node.get_class(),
			"position": node.global_position if node.has_method("global_position") else null,
			"tags": node.get_meta("tags") if node.has_meta("tags") else []
		}
		print(JSON.stringify(info))  # ← 這邊已修正！

		for child in node.get_children():
			explore_node(child)
