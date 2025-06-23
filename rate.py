import os
import json
from collections import defaultdict
import pandas as pd

# 修改這裡：你的 JSON 檔案資料夾
folder_path = "./experiments"  # ← 依你的檔案實際路徑調整

# 初始化結果統計
results_summary = defaultdict(lambda: {"success": 0, "fail": 0})

# 處理每個 JSON 檔案
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 取得 scenario 名稱與模型名稱（從檔名拆解）
        scenario = data.get("scenario_name", "unknown")
        model = filename.split("-scenario_")[0]  # 例如 GPT-4 / Gemini2.5Pro

        # 根據 "completed" 欄位判斷任務是否成功
        if data.get("completed", False):
            results_summary[(scenario, model)]["success"] += 1
        else:
            results_summary[(scenario, model)]["fail"] += 1

# 整理為 DataFrame
records = []
for (scenario, model), result in results_summary.items():
    total = result["success"] + result["fail"]
    success_rate = result["success"] / total if total > 0 else 0
    records.append({
        "Scenario": scenario,
        "Model": model,
        "Success": result["success"],
        "Fail": result["fail"],
        "Success Rate": round(success_rate, 2)
    })

df = pd.DataFrame(records)
df = df.sort_values(by=["Scenario", "Model"])

# 顯示結果
print(df)

# 如果想存成 csv：
# df.to_csv("task_completion_summary.csv", index=False)
