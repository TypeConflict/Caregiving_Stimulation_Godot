extends CharacterBody2D

@onready var agent = $NavigationAgent2D
var speed = 20
var is_manual_mode = true

func _ready():
	# 初始設置
	agent.target_position = global_position  # 初始目標設為角色當前位置

func _physics_process(delta: float) -> void:
	handle_auto_movement()

func handle_auto_movement():
	if agent.is_navigation_finished():
		velocity = Vector2.ZERO
	else:
		var next_position = agent.get_next_path_position()
		if next_position != null:  # 確保有有效的導航位置
			var direction = (next_position - global_position).normalized()
			velocity = direction * speed
		else:
			velocity = Vector2.ZERO  # 如果沒有有效路徑，停下來
