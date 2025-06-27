extends CharacterBody2D

@onready var agent = $NavigationAgent2D
var speed = 100
var is_manual_mode = true

func _ready():
	# 初始設置
	agent.target_position = global_position  # 初始目標設為角色當前位置

func _physics_process(delta):
	if is_manual_mode:
		handle_manual_movement()
	else:
		handle_auto_movement()
	move_and_slide()

func handle_manual_movement():
	var direction = Vector2.ZERO
	if Input.is_action_pressed("ui_up"):
		direction.y -= 1
	if Input.is_action_pressed("ui_down"):
		direction.y += 1
	if Input.is_action_pressed("ui_left"):
		direction.x -= 1
	if Input.is_action_pressed("ui_right"):
		direction.x += 1

	velocity = direction.normalized() * speed if direction != Vector2.ZERO else Vector2.ZERO

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
