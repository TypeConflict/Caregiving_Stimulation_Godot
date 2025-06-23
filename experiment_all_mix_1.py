import openai
import time
import json
from datetime import datetime
import os
import socket
import asyncio
import random
import glob # 導入 glob 模組來查找文件

# 導入 Google Generative AI 函式庫
import google.generativeai as genai

# Godot UDP connection settings
UDP_IP = "127.0.0.1"
UDP_PORT = 8080
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Interactive objects recognized by the simulation environment (Godot)
INTERACTIVE_OBJECTS = {
   "廚房檯面", "收納櫃", "洗衣機", "餐桌組合", "沙發", "床",
   "浴缸", "浴室洗手槽", "馬桶", "小茶几", "衣櫃", "書桌", "Home"
}

# 要有拆開言語、動作到Godot的機制
# 照護員的模組是同一的，主要讓阿嬤扮演的背景有區別
# 然後做3*3*2種實驗

# 👉請填入你的 API 金鑰
# OpenAI API 金鑰 (用於 GPT 模型)
openai_client = openai.OpenAI(api_key="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")

# Google Gemini API 金鑰 (用於 Gemini 模型)
# 請務必替換為您自己的 Gemini API 金鑰
genai.configure(api_key="AIzaSyBanoiYsXV_7k15Q1q8K2dgJ71G7Kv4uUo") # <<< 在這裡填入您的 Gemini API 金鑰

EMOTIONS = ["Forgetful", "Confused", "Angry", "Disengaged", "Calm"]
EMOTION_LABELS_ZH = {
    "Forgetful": "健忘",
    "Confused": "困惑",
    "Angry": "生氣",
    "Disengaged": "抽離",
    "Calm": "安穩"
}
BASE_PROB_INITIAL = { # 使用 BASE_PROB_INITIAL 來保留初始機率，每次模擬開始時重置 BASE_PROB
    "Forgetful": 0.3,
    "Confused": 0.3,
    "Angry": 0.05,
    "Disengaged": 0.2,
    "Calm": 0.0 # 初始不可能是 Calm
}
# 定義一個可變動的 BASE_PROB，用於在模擬中更新
BASE_PROB = BASE_PROB_INITIAL.copy()


TRANSITION_MATRIX = {
    "Forgetful": [
        ("Forgetful", 0.99), ("Confused", 0.05), ("Angry", 0.06), ("Disengaged", 0.02), ("Calm", 0.0)
    ],
    "Confused": [
        ("Forgetful", 0.07), ("Confused", 0.99), ("Angry", 0.08), ("Disengaged", 0.02), ("Calm", 0.0)
    ],
    "Angry": [
        ("Forgetful", 0.07), ("Confused", 0.08), ("Angry", 1.0), ("Disengaged", 0.10), ("Calm", 0.0)
    ],
    "Disengaged": [
        ("Forgetful", 0.07), ("Confused", 0.10), ("Angry", 0.20), ("Disengaged", 0.99), ("Calm", 0.0)
    ],
    "Calm": [
        ("Forgetful", 0.05), ("Confused", 0.05), ("Angry", 0.02), ("Disengaged", 0.05), ("Calm", 0.99)
    ],
}

async def evaluate_caregiver_response_effectiveness(current_emotion, caregiver_response, elder_response, dialogue_context):
    """
    使用LLM評估照護者的回應對長者情緒狀態的影響效果。
    """
    prompt = f"""
    你是一個專業的照護效果評估專家。請評估照護者的回應對長者情緒狀態的影響效果。

    當前情境：
    - 長者當前情緒：{EMOTION_LABELS_ZH[current_emotion]} ({current_emotion})
    - 照護者說：{caregiver_response}
    - 長者回應：{elder_response}

    對話背景（最近幾輪）：
    {dialogue_context}

    請從以下角度評估照護者的有效性：
    1. 是否適當回應了長者的情緒需求
    2. 是否使用了合適的溝通技巧
    3. 長者的回應是否顯示情緒有所改善
    4. 是否有助於建立信任和安全感
    5. 是否避免了可能加劇負面情緒的行為

    如果你綜合評估認為適當，請回傳「是」，否則請回答「否」。只回傳一次「是」或「否」，不要添加其他文字。
    """

    try:
        response = openai_client.chat.completions.create( # 這裡仍然使用 openai_client
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一個專業的照護效果評估專家，負責分析照護者的回應是否有效。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
            print("無法獲取照護效果評估結果")
            return "無法評估"

        evaluation_result = response.choices[0].message.content.strip()
        print(f"📊 照護效果評估是否有效：{evaluation_result}")

        # 如果評估結果是「是」，增加 Calm 的機率
        if evaluation_result == "是":
            adjust_probabilities_for_calm()

        return evaluation_result

    except Exception as e:
        print(f"照護效果評估失敗：{e}")
        return "評估失敗"

def adjust_probabilities_for_calm():
    """
    累積增加 Calm 的機率 10%，並平均削弱其他情緒的機率。
    """
    global BASE_PROB # 聲明使用全域變數
    total_reduction = 0.1 # 每次增加 Calm 的機率
    num_other_emotions = len(BASE_PROB) - 1 # 除了 Calm 的情緒數量
    reduction_per_emotion = total_reduction / num_other_emotions

    for emotion in BASE_PROB:
        if emotion == "Calm":
            BASE_PROB[emotion] += total_reduction
        else:
            BASE_PROB[emotion] -= reduction_per_emotion

    # 確保所有機率仍然加總為 1
    normalization_factor = sum(BASE_PROB.values())
    for emotion in BASE_PROB:
        BASE_PROB[emotion] /= normalization_factor

    print(f"更新後的情緒機率：{BASE_PROB}")

def choose_initial_emotion():
    emotions = list(BASE_PROB.keys())
    weights = [BASE_PROB[e] for e in emotions]
    return random.choices(emotions, weights=weights, k=1)[0]

def next_emotion(current_emotion):
    """
    根據更新後的 BASE_PROB 機率抽選下一個情緒。
    """
    emotions = list(BASE_PROB.keys())
    weights = [BASE_PROB[e] for e in emotions]
    return random.choices(emotions, weights=weights, k=1)[0]

def send_to_godot(agent_type: str, object_name: str):
    """
    Sends a UDP message to Godot in the format 'AgentType:ObjectName'.
    agent_type should be '長者' or '照護員'.
    """
    message = f"{agent_type}:{object_name}"
    try:
        udp_socket.sendto(message.encode("utf-8"), (UDP_IP, UDP_PORT))
        print(f"📨 發送給 Godot：{message}")
    except Exception as e:
        print(f"❌ 發送給 Godot 時發生錯誤：{e}")


async def detect_and_send_object_interaction(agent_name: str, behavior_description: str):
    """
    Uses LLM to detect if the behavior description mentions an interactive object
    and sends a corresponding UDP message to Godot.
    """
    object_list_str = ", ".join(sorted(list(INTERACTIVE_OBJECTS)))
    prompt = f"""
    You are a module specialized in detecting interactive objects from behavior descriptions.
    Please analyze the following behavior description and identify any interactive objects mentioned.
    
    You can ONLY choose from this list of objects, no other objects are allowed:
    {object_list_str}
    
    If the behavior description involves multiple objects, list all relevant objects.
    Please output a JSON array containing all interactive objects mentioned in the behavior description.
    If no objects are mentioned, output an empty array: []
    Ensure the JSON format is valid with proper string escaping.

    Behavior description: "{behavior_description}"

    Example output (just the JSON array, no prefix):
    ["沙發", "小茶几"]

    If no objects are mentioned, output:
    []

    Important:
    1. Output must be a valid JSON array, not an object or dictionary.
    2. Only use items from the provided object list, no other object names allowed.
    3. Do not include any additional text, only output the JSON array.
    """

    try:
        response = openai_client.chat.completions.create( # 這裡仍然使用 openai_client
            model="gpt-3.5-turbo", # Using gpt-3.5-turbo for this simpler classification task
            messages=[
                {"role": "system", "content": "You are a precise object detector that must output a JSON array. You must only use items from the specified object list and format the response as a valid JSON array."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100, # Should be enough for a list of object names
            temperature=0.1, # Keep it low for deterministic output
            response_format={"type": "json_object"} # Request JSON object format
        )
        
        if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
            print("LLM 回傳空回應")
            return
            
        response_content = response.choices[0].message.content.strip()
        try:
            detected_objects = json.loads(response_content)
            # 如果回傳的是字典，轉換為陣列
            if isinstance(detected_objects, dict):
                detected_objects = list(detected_objects.keys())
            elif not isinstance(detected_objects, list):
                print(f"LLM 回傳非預期的物件偵測格式: {detected_objects}")
                detected_objects = []
                
            # 過濾掉不在 INTERACTIVE_OBJECTS 中的項目
            detected_objects = [obj for obj in detected_objects if obj in INTERACTIVE_OBJECTS]
            
        except json.JSONDecodeError:
            print(f"LLM 回傳的 JSON 格式無效: {response_content}")
            detected_objects = []

        agent_prefix = ""
        if agent_name == "Elder":
            agent_prefix = "長者"
        elif agent_name == "Caregiver":
            agent_prefix = "照護員"
        
        if detected_objects:
            for obj in detected_objects:
                send_to_godot(agent_prefix, obj)
        else:
            # 如果沒有偵測到物件，則不發送任何訊息
            pass

    except json.JSONDecodeError as e:
        print(f"LLM 物件偵測 JSON 解析失敗: {e}")
        print(f"原始LLM回應: {response_content}")
    except Exception as e:
        print(f"LLM 物件偵測失敗：{e}")

def judge_task_completion(dialogue_history, system_info, target_info):
    """
    遊戲裁判：分析對話歷史，判斷任務是否完成
    """
    # 將對話轉換為更自然的格式
    conversation = []
    for i in range(1, len(dialogue_history), 2): # 每次取兩條訊息（一輪對話）
        if i + 1 < len(dialogue_history):
            conversation.append(f"第{(i+1)//2}輪：")
            conversation.append(f"照護者：{dialogue_history[i]['content']}")
            conversation.append(f"阿嬤：{dialogue_history[i+1]['content']}")
            conversation.append("") # 空行分隔

    judge_prompt = f"""
你是一個遊戲裁判，負責判斷照護者是否完成了任務目標。

請特別注意：**你必須根據阿嬤的回應來判斷照護者的引導是否被接受**。只有當阿嬤明確表現出接受、配合、理解或實際行動時，才算任務完成。如果阿嬤仍然拒絕、困惑、抗拒或沒有行動，則任務未完成。

任務背景：{system_info}
任務目標：{target_info}

以下是對話過程：
{chr(10).join(conversation)}

請分析對話用以下格式回答：
任務完成狀態：[是/否]
判斷理由：[詳細說明]
下一步建議：[如果未完成，建議照護者如何改進]
"""

    response = openai_client.chat.completions.create( # 這裡仍然使用 openai_client
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一個嚴格的遊戲裁判，負責判斷任務完成狀態。"},
            {"role": "user", "content": judge_prompt}
        ],
        temperature=0.3
    )
    
    if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
        return "無法獲取裁判判斷"
        
    return response.choices[0].message.content.strip()

def save_experiment(dialogue_history, system_info, target_info, elder_role_info, judge_results, emotion_history, scenario_name, repetition):
    """
    將實驗結果保存到JSON檔案
    """
    # 創建experiments目錄（如果不存在）
    if not os.path.exists('experiments'):
        os.makedirs('experiments')
    
    # 生成檔案名（使用指定格式）
    # 移除 .json 副檔名以獲得 json名稱
    base_scenario_name = os.path.splitext(scenario_name)[0] 
    filename = f'experiments/Mix1-{base_scenario_name}-{repetition}.json'
    
    # 準備要保存的數據
    experiment_data = {
        "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S'),
        "scenario_name": scenario_name, # 添加情境檔案名稱
        "repetition_number": repetition, # 添加重複次數
        "system_info": system_info,
        "target_info": target_info,
        "elder_role_info": elder_role_info,
        "dialogue_history": dialogue_history,
        "judge_results": judge_results,
        "emotion_history": emotion_history, # 新增情緒記錄
        "total_turns": len(dialogue_history) // 2, # 每輪有兩條訊息
        "completed": any("任務完成狀態：是" in result for result in judge_results)
    }
    
    # 保存到檔案
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(experiment_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 實驗結果已保存至：{filename}")
    return filename

# 模擬起始指令與任務設定
# 這些變數現在在主循環內部設定，以便每次模擬都能重新載入
system_prompt_template = """
我們來玩角色扮演。我是一個患有輕中度失智症的、75歲的台灣阿嬤，你扮演我的照護者，名字叫熊熊。分析我的言語和行動，並預防我做出任何有害於自己的事。

你在這個情境中所知道的和阿嬤有關聯的背景是：{system_info}。 

請透過阿嬤的說話和行為判斷她的需求、需要協助的部分，並協助她完成日常任務，達成你的任務目標。

角色限制如下：
- 我的敘述使用小說體，一次一句。
- 你的回覆也要用第一人稱小說體，一次一句。
- 除了背景有提到的事情以外不能捏造
- 不要用系統語氣描述行為，僅透過角色視角自然展開。
- 請嚴格遵照你所知的背景扮演角色進行對話。
"""

# 遊戲控制參數
max_turns = 20

async def run_simulation(scenario_file_path, repetition_number):
    global BASE_PROB # 聲明使用全域變數

    print(f"\n--- 開始模擬： {os.path.basename(scenario_file_path)}，第 {repetition_number} 次 ---")

    # 重置 BASE_PROB 到初始狀態
    BASE_PROB = BASE_PROB_INITIAL.copy()

    # 從 JSON 檔案匯入情境設定
    with open(scenario_file_path, 'r', encoding='utf-8') as f:
        scenario = json.load(f)
        system_info = scenario['system_info']
        target_info = scenario['target_info']
        elder_role_info = scenario['elder_role_info']
        initial_dialogue_content = scenario['initial_dialogue']

    system_prompt = system_prompt_template.format(system_info=system_info)

    # 初始對話內容，每次模擬都重新初始化
    dialogue = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": initial_dialogue_content}
    ]

    turn = 1
    judge_results = [] # 用於存儲所有裁判判斷
    emotion_history = [] # 用於存儲每一輪的情緒

    # 初始化阿嬤的情緒
    current_emotion = choose_initial_emotion()
    print(f"🧓 初始情緒：{EMOTION_LABELS_ZH[current_emotion]} ({current_emotion})")
    emotion_history.append(current_emotion) # 記錄初始情緒

    while turn <= max_turns:
        # 📌 Step 1: ChatGPT生成照護者回覆
        # 如果是第二輪之後，加入裁判的判斷結果
        if turn > 1:
            judge_result = judge_task_completion(dialogue, system_info, target_info)
            judge_results.append(judge_result) # 保存裁判判斷
            print("\n🎯 任務狀態評估：")
            print(judge_result)
            print("-" * 50)
            
            # 更新系統提示，加入裁判的判斷
            updated_system_prompt = f"""
{system_prompt_template.format(system_info=system_info)}

上一輪的任務評估結果：
{judge_result}

請根據這個評估結果，調整你的照護策略。
"""
            # 更新對話中的系統提示
            dialogue[0]["content"] = updated_system_prompt

        response = openai_client.chat.completions.create( # 照護者使用 OpenAI 模型
            model="gpt-4o",
            messages=dialogue,
            temperature=0.7
        )

        if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
            print("無法獲取照護者回應")
            break
            
        reply = response.choices[0].message.content.strip()
        print(f"👩‍⚕️ 照護者：{reply}")

        # 檢測照護者的行為是否涉及互動物件
        await detect_and_send_object_interaction("Caregiver", reply)

        # 如果裁判判定任務完成，則結束對話
        if turn > 1 and "任務完成狀態：是" in judge_result:
            print("\n🎉 恭喜！任務已完成！")
            break

        # 📌 Step 2: 再由阿嬤生成下一句
        # 只取最近三輪的對話
        # 注意：Google Gemini API 的對話格式與 OpenAI 不同，需要轉換
        # Gemini 模型的 messages 參數期望的是 'parts' 列表，且 'role' 為 'user' 或 'model'
        gemini_dialogue_history = []
        for msg in dialogue[1:]: # 從第二個元素開始，因為第一個是 system prompt
            if msg['role'] == 'user':
                gemini_dialogue_history.append({'role': 'user', 'parts': [msg['content']]})
            elif msg['role'] == 'assistant':
                gemini_dialogue_history.append({'role': 'model', 'parts': [msg['content']]})


        # 獲取該輪照護者的最後一句話
        last_caregiver_reply = reply  # 使用當前輪次的照護者輸出

        elder_response_prompt_for_gemini = f"""
你正在和我進行角色扮演遊戲：
你扮演75歲、有中度失智表現的台灣阿嬤，當前情緒狀態是：{EMOTION_LABELS_ZH[current_emotion]}（{current_emotion}）。
我扮演你的照護者，名字叫熊熊。
你的扮演背景是：{elder_role_info}。

請特別參考照護者剛才對你的回應：
"{last_caregiver_reply}"

我們雙方都會以第一人稱進行。請你以阿嬤的身份，用第一人稱小說體自然地回應這句話：
"""
        try:
            # 初始化 Gemini 模型
            gemini_model = genai.GenerativeModel('gemini-2.5-pro')
            
            # 使用 Gemini 的 chat API
            # 先將歷史對話傳入，然後再傳入當前提示
            chat = gemini_model.start_chat(history=gemini_dialogue_history)
            
            gemini_response = await chat.send_message_async(elder_response_prompt_for_gemini) # 使用 await 呼叫
            
            # 確保回應內容存在
            if not gemini_response.candidates or not gemini_response.candidates[0].content or not gemini_response.candidates[0].content.parts:
                print("無法獲取阿嬤回應 (Gemini 回應為空)")
                break

            elder_response = gemini_response.candidates[0].content.parts[0].text.strip() # 從 parts 中取出文本
            print(f"🧓 阿嬤：{elder_response}")
            print("-" * 50)

        except Exception as e:
            print(f"阿嬤回應生成失敗 (Gemini)：{e}")
            break
            
        # 檢測阿嬤的行為是否涉及互動物件
        await detect_and_send_object_interaction("Elder", elder_response)

        # 新一輪對話加入上下文 (仍然使用 OpenAI 的格式以便裁判模型使用)
        dialogue.append({"role": "assistant", "content": reply})
        dialogue.append({"role": "user", "content": elder_response})

        # 判斷是否需要更新情緒比重
        await evaluate_caregiver_response_effectiveness(
            current_emotion, reply, elder_response, chr(10).join([f"{msg['role']}: {msg['content']}" for msg in dialogue[-6:] if msg['role'] != 'system']) # 傳入 OpenAI 格式的對話上下文
        )

        # 更新阿嬤的情緒（只抽選一次）
        prev_emotion = current_emotion
        current_emotion = next_emotion(current_emotion) # 根據更新後的 BASE_PROB 抽選情緒
        print(f"🧓 新情緒：{EMOTION_LABELS_ZH[current_emotion]} ({current_emotion}) [前一輪：{EMOTION_LABELS_ZH[prev_emotion]}]")
        emotion_history.append(current_emotion) # 記錄每一輪的情緒

        turn += 1
        time.sleep(1)

    if turn > max_turns:
        print("⚠️ 回合數達上限，任務未完成。")

    # 保存實驗結果
    save_experiment(dialogue, system_info, target_info, elder_role_info, judge_results, emotion_history, os.path.basename(scenario_file_path), repetition_number)


# 主執行區塊
async def main_runner():
    # 確保 scenarios 目錄存在，如果不存在則創建
    if not os.path.exists('scenarios'):
        print("錯誤：'scenarios' 資料夾不存在。請將情境檔案放入 'scenarios' 資料夾。")
        return

    scenario_files = sorted(glob.glob('scenarios/scenario_*.json'))
    if not scenario_files:
        print("在 'scenarios' 資料夾中沒有找到 'scenario_*.json' 檔案。")
        return

    for scenario_file in scenario_files:
        for i in range(1, 4): # 每個檔案跑3次 (1, 2, 3)
            await run_simulation(scenario_file, i)
            print(f"\n--- 模擬結束： {os.path.basename(scenario_file)}，第 {i} 次 ---")
            print("=" * 80) # 分隔線

# 運行主程序
if __name__ == "__main__":
    print("🎮 開始模擬照護互動...\n")
    asyncio.run(main_runner())