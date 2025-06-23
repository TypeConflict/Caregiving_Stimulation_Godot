import socket
import time

# 設定目標 IP 和 port，需與 Godot 中綁定的 port 一致
UDP_IP = "127.0.0.1"  # 如果是在同一台機器上
UDP_PORT = 8080

# 要傳送的訊息
messages = [
    "Bear:阿嬤，冰箱就在這裡。",
    "goto:廚房檯面"
]

# 初始化 UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 傳送訊息
for msg in messages:
    sock.sendto(msg.encode("utf-8"), (UDP_IP, UDP_PORT))
    print(f"✅ 傳送：{msg}")
    time.sleep(0.5)  # 稍微等一下，避免 Godot 來不及顯示
