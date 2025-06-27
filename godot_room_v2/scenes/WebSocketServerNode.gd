extends Node

var udp := PacketPeerUDP.new()
var targets = {}
var bear
var gpt_talk
var user_talk

func _ready():
	bear = get_node("%Bear")
	gpt_talk = get_node("%GPTtalk")
	user_talk = get_node("%USERtalk")

	var result = udp.bind(8080)
	if result != OK:
		print("❌ 無法綁定 UDP port 8080")
	else:
		print("✅ 已綁定 port 8080，等待資料...")

	targets["廚房檯面"] = get_node("%廚房檯面")
	targets["收納櫃"] = get_node("%收納櫃")
	targets["洗衣機"] = get_node("%洗衣機")
	targets["餐桌組合"] = get_node("%餐桌組合")
	targets["沙發"] = get_node("%沙發")
	targets["床"] = get_node("%床")
	targets["廚房檯面"] = get_node("%廚房檯面")
	targets["浴缸"] = get_node("%浴缸")
	targets["浴室洗手槽"] = get_node("%浴室洗手槽")
	targets["馬桶"] = get_node("%馬桶")
	targets["小茶几"] = get_node("%小茶几")
	targets["衣櫃"] = get_node("%衣櫃")
	targets["書桌"] = get_node("%書桌")
	targets["Home"] = get_node("%Home")

	gpt_talk.visible = false
	user_talk.visible = false

func _process(_delta):
	while udp.get_available_packet_count() > 0:
		var data = udp.get_packet()
		var message = data.get_string_from_utf8().strip_edges()
		handle_command(message)

func handle_command(msg: String):
	var parts = msg.split(":", false, 2)
	var command = parts[0]
	var param = parts[1] if parts.size() > 1 else null

	if command == "goto" and param and targets.has(param):
		var target_pos = targets[param].global_position
		print("🎯 Bear 前往目標位置：", target_pos)
		bear.is_manual_mode = false
		bear.agent.target_position = target_pos

	elif command == "User" and param:
		show_user_then_gpt(param)

	elif command == "Bear" and param:
		show_talk_bubble(param)

func show_user_then_gpt(user_text: String):
	gpt_talk.visible = false  # 確保先關掉另一個
	user_talk.visible = true
	user_talk.get_node("Label").text = user_text
	user_talk.get_node("Label").add_theme_color_override("font_color", Color.BLACK)

func show_talk_bubble(text: String):
	user_talk.visible = false  # 確保先關掉另一個
	gpt_talk.visible = true
	gpt_talk.get_node("Label").text = text
	gpt_talk.get_node("Label").add_theme_color_override("font_color", Color.BLACK)
