import os
import json
import matplotlib.pyplot as plt
from collections import defaultdict

folder_path = "./experiments"  # ← 改成你自己的路徑

emotion_to_int = {
    "Forgetful": 0,
    "Confused": 1,
    "Angry": 2,
    "Disengaged": 3,
    "Calm": 4
}

# 色階設定（淺 → 深）
model_color_shades = {
    "GPT-4": ["#aec6cf", "#5b9bd5", "#1f4e79"],
    "gpt-4": ["#aec6cf", "#5b9bd5", "#1f4e79"],
    "GPT-4o": ["#b2e2b2", "#66cc66", "#267326"],
    "gpt-4o": ["#b2e2b2", "#66cc66", "#267326"],
    "Gemini2.5pro": ["#ffe0b2", "#ffb74d", "#f57c00"],
    "Gemini-2.5-Pro": ["#ffe0b2", "#ffb74d", "#f57c00"]
}

# 模型標記樣式
model_markers = {
    "GPT-4": "o",       # 圓形
    "gpt-4": "o",
    "GPT-4o": "^",      # 三角形
    "gpt-4o": "^",
    "Gemini2.5pro": "s",  # 方形
    "Gemini-2.5-Pro": "s"
}

scenario_dict = defaultdict(list)

for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            scenario_name = data.get("scenario_name", "unknown")
            emotion_history = data.get("emotion_history", [])
            model_name = filename.split("-scenario_")[0].strip()
            scenario_dict[scenario_name].append((model_name, emotion_history))

for scenario, model_emotions in scenario_dict.items():
    plt.figure(figsize=(10, 4))
    model_instance_counter = defaultdict(int)

    for model_name, emotions in model_emotions:
        count = model_instance_counter[model_name]
        color_list = model_color_shades.get(model_name, ["#d3d3d3", "#a9a9a9", "#696969"])
        marker = model_markers.get(model_name, "x")
        color = color_list[min(count, len(color_list) - 1)]
        model_instance_counter[model_name] += 1

        int_emotions = [emotion_to_int[e] for e in emotions]
        label = f"{model_name} run {count+1}"

        plt.plot(
            range(1, len(int_emotions) + 1),
            int_emotions,
            marker=marker,
            label=label,
            color=color,
            linewidth=2
        )

    plt.yticks(list(emotion_to_int.values()), list(emotion_to_int.keys()))
    plt.xlabel("Turn Number")
    plt.ylabel("Emotion State")
    plt.title(f"Emotion Comparison for {scenario}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    save_name = f"{scenario.replace('.json', '')}_emotion_comparison.png"
    plt.savefig(os.path.join(folder_path, save_name))
    plt.close()

print("✅ 完成圖表：使用色階 + 專屬標記樣式，清楚區分每個模型的多次實驗！")
