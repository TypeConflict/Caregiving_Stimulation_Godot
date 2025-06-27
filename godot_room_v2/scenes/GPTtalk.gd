extends Control

@onready var label = $GPTtalk/Label

func show_message(message: String):
	label.text = message
	visible = true
	# 可以選擇用 Tween 做打字動畫或 fade in/out
