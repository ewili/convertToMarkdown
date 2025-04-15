import json
import streamlit as st # 导入 streamlit
import uuid # 导入 uuid 库
from collections import Counter
import time

# API URL
url = "https://www.notion.so/api/v3/runAssistantV2"

# --- 常量定义 ---
# 将 headers, cookies 和 data 的通用部分提取出来作为常量
HEADERS = {
    "x-notion-active-user-header": "e63761a2-52de-4e41-af11-64e08edb8797", 
    "x-notion-space-id": "65492b2e-2341-40df-8dd9-40cdfd3314cf"
}

COOKIES = {
    "token_v2": "v03%3AeyJhbGciOiJkaXIiLCJraWQiOiJwcm9kdWN0aW9uOnRva2VuLXYzOjIwMjQtMTEtMDciLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIn0..PGsBAMQM4lmKJlREfOE4Sg.0nYw4LT7Pyxb3S3CkbdUbCDdXhLj512F5JuPfgRz7LtwWofpF-Br1_8TcN0tSpDKParWP38t2TEwDGQIWdemSbCCZWcQsalflpupR5DTf4cIy8IqM6MdHMCHBEBDrJ1UhOU5IyuY-LNaQGoG9kLaQyhwNvlulf7Ye1OyyCEnMvL1pRPvlRjnYkaDUmxEFJHQljqym1-kzg9liYoGNciSPYbw8o_PP5N1nWfhQwrardbsDmiQzDDOwumwvSiKnb0mHVJ8OTbQOSQwSxMZJ2JnwwujBzc77cU_FX2g6kutV-c0MKnF7Q3jsQCiwGNI1Nradz21iR-fG5rujUJQ_sdYVPzqikeoCqTB-Pr063NwZmCrwWF6x0yegVFvhkKo-TrroKSRk6jihhfcTT61MlEY8OThHB0BKRkLRGLAUhjGSgSMj4TjawKwwNPkJYTc7hyA.0g0eorISfe90dJgB1_8rRZQpt6llXiB6qSCVeg4IhEA" # 请替换成你自己的 token_v2
}

BASE_DATA = {
    "version": 1,
    "state": {
        "version": 16,
        "context": {
            "mode": "direct",
            "available-commands": [
                "load-database", "load-page", "load", "query-database", "search",
                "chat", "search-databases", "load-slack",
            ],
            "current-page-name": "",
            "current-person-name": "ewili", # 可以修改成你的名字
            "current-space-name": "V40/2", # 可以修改成你的空间名
            "current-person-id": "e63761a2-52de-4e41-af11-64e08edb8797" # 请替换成你自己的 person-id
        },
        "loadedPageIds": [],
        "schemaIdMap": {},
        "blockIdMap": {},
        "peopleIdMap": {},
        "collectionIdMap": {},
        "universalIdMap": {},
        "universalSearchResultPayloadMap": {},
        "loadedUniversalIds": [],
        "loadedDatabaseIds": [],
        "loadedAttachmentIds": []
    },
    "transcript": [
        {
            "type": "context",
            "context": {
                "mode": "direct",
                "available-commands": [
                    "load-database", "load-page", "load", "query-database", "search",
                    "chat", "search-databases", "load-slack",
                ],
                "current-page-name": "",
                "current-person-name": "ewili", # 同上
                "current-space-name": "V40/2", # 同上
                "current-person-id": "e63761a2-52de-4e41-af11-64e08edb8797" # 同上
            }
        },
        # 人类输入的部分将在函数中动态添加
    ],
    "spaceId": "65492b2e-2341-40df-8dd9-40cdfd3314cf", # 请替换成你自己的 space-id
    "analytics": {
        "sessionId": "390c811a-ac99-468f-8f35-e8c953d10bcd", # 可以考虑每次生成新的 UUID
        "assistantSurface": "fullPage",
        "openedFrom": "sidebar"
    },
    "searchScope": {
        "type": "notion"
    },
    "userTimeZone": "Asia/Shanghai",
    "useUncited": True,
    "useLangXmlTag": True,
    "useMarkdown": True # 注意这里是 False，如果希望返回 Markdown 可以改成 True
}

# --- 样式设置 ---
# 移除复杂的CSS样式，只保留基本的消息样式
st.markdown("""
<style>
.user-message {
    background-color: #e6f7ff;
    border-radius: 15px;
    padding: 10px 15px;
    margin: 5px 0;
    text-align: right;
    margin-left: 20%;
}
.assistant-message {
    background-color: #f0f0f0;
    border-radius: 15px;
    padding: 10px 15px;
    margin: 5px 0;
    text-align: left;
    margin-right: 20%;
}
.message-header {
    margin-bottom: 5px;
}
.role-badge {
    font-size: 0.8em;
    padding: 2px 8px;
    border-radius: 10px;
    display: inline-block;
}
.user-badge {
    background-color: #1890ff;
    color: white;
}
.assistant-badge {
    background-color: #52c41a;
    color: white;
}
.message-time {
    font-size: 0.7em;
    color: #888;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# --- Session State 初始化 ---
# 检查 session_id 是否已存在，如果不存在则创建一个新的
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.conversation_history = []  # 初始化对话历史
    st.session_state.raw_responses = []  # 存储原始响应
    st.session_state.messages = []  # 用于存储格式化消息
    st.session_state.thinking = False
    # 可以在这里添加一个标记，表示是新会话开始，用于可能的清理操作
    # st.session_state.new_conversation = True
elif 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []  # 确保对话历史存在
if 'raw_responses' not in st.session_state:
    st.session_state.raw_responses = []  # 确保原始响应存储存在
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'thinking' not in st.session_state:
    st.session_state.thinking = False

# --- API 调用函数 ---
def call_notion_ai(user_query: str, session_id: str, conversation_history=None, search_scope="notion"):
    """调用 Notion AI API 并处理响应"""
    data = BASE_DATA.copy()
    
    # 更新搜索范围
    data["searchScope"]["type"] = search_scope
    
    if conversation_history:
        context_entry = data["transcript"][0]
        data["transcript"] = [context_entry] + conversation_history
    
    # 更新 transcript 加入当前用户输入
    data["transcript"].append({
        "type": "human",
        "value": user_query
    })

    # 更新 analytics 中的 sessionId
    data["analytics"]["sessionId"] = session_id

    # 打印请求内容（调试用）
    st.sidebar.text("请求sessionID: " + session_id)
    st.sidebar.text(f"对话历史长度: {len(data['transcript']) - 1}")  # 减去context条目
    
    try:
        response = requests.post(url, headers=HEADERS, cookies=COOKIES, json=data, stream=True) # 使用 stream=True
        response.raise_for_status() # 检查请求是否成功
        
        # 打印响应状态（调试用）
        st.sidebar.text(f"API响应状态码: {response.status_code}")
        
        results = []
        response_content = ""  # 用于存储完整的响应内容(调试用)
        
        # 按行处理流式响应
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                response_content += decoded_line + "\n"
                try:
                    line_data = json.loads(decoded_line)
                    # 打印每行响应类型（调试用）
                    line_type = line_data.get("type", "unknown")
                    if len(results) < 5:  # 只打印前几条，避免过多输出
                        st.sidebar.text(f"响应类型: {line_type}")
                    
                    results.append(line_data) # 收集所有解析后的行数据
                except json.JSONDecodeError as e:
                    print(f"无法解析行: {decoded_line}, 错误: {e}") # 打印错误信息，但不中断处理
                    st.sidebar.text(f"JSON解析错误: {str(e)[:50]}...")
                    results.append({"type": "error", "value": f"无法解析行: {decoded_line}"})
        
        # 调试信息：打印收集到的结果数量
        st.sidebar.text(f"共收集到 {len(results)} 条响应数据")
        
        # 如果没有结果，并且有响应内容，则打印部分内容以便调试
        if len(results) == 0 and response_content:
            st.sidebar.text("原始响应内容(前200字符):")
            st.sidebar.text(response_content[:200])
        
        # 保存原始响应内容到会话状态
        if 'raw_responses' in st.session_state:
            # 限制存储的响应数量，避免占用过多内存
            while len(st.session_state.raw_responses) > 5:
                st.session_state.raw_responses.pop(0)
            st.session_state.raw_responses.append({
                'query': user_query,
                'response': response_content,
                'parsed': results
            })
        
        return results

    except requests.exceptions.RequestException as e:
        st.error(f"API 请求失败: {e}")
        st.sidebar.text(f"请求异常: {str(e)}")
        return None
    except Exception as e:
        st.error(f"发生未知错误: {e}")
        st.sidebar.text(f"未知错误: {str(e)}")
        return None

# --- 处理API响应函数 ---
def process_api_response(api_responses):
    """处理API响应并提取助手回复"""
    assistant_response = ""
    search_results_md = ""
    
    # 处理状态标记
    is_searching = False
    has_search_results = False
    
    # 检查搜索状态
    for data in api_responses:
        response_type = data.get("type")
        if response_type == "search" and not is_searching:
            is_searching = True
        elif response_type == "search_results" and not has_search_results:
            has_search_results = True
    
    # 处理流式响应片段
    partial_responses = []
    for data in api_responses:
        if data.get("type") == "partial_assistant_step":
            value = data.get("value", "")
            if value:
                partial_responses.append(value)
    
    # 如果有流式响应片段，合并它们
    if partial_responses:
        combined_partial = "".join(partial_responses)
        st.sidebar.text(f"合并流式响应片段，长度: {len(combined_partial)}")
        assistant_response = combined_partial
    
    # 处理其他响应类型
    for data in api_responses:
        response_type = data.get("type")

        if response_type == "search_results":
            value = data.get("value", {})
            results = value.get("results", [])
            
            if results:
                # 检查结果中是否包含path字段
                has_path = any("path" in result for result in results)
                
                search_results_md += "**相关搜索结果:**\n\n"
                
                if has_path:
                    # 按path分组
                    grouped_results = {}
                    for result in results:
                        path = result.get('path', '未知路径')
                        if path not in grouped_results:
                            grouped_results[path] = []
                        grouped_results[path].append(result)
                    
                    # 按分组显示结果，使用小字体格式
                    for path, path_results in grouped_results.items():
                        # 使用h3标签，但是格式更轻量
                        search_results_md += f"### `{path}`\n\n"
                        for result in path_results:
                            title = result.get('title', '无标题')
                            page_id = result.get('id', '')
                            score = result.get('score', 0)
                            notion_link = f"https://www.notion.so/{page_id.replace('-', '')}" if page_id else "#"
                            search_results_md += f"- [{title}]({notion_link}) (相关度: {score:.2f})\n"
                        search_results_md += "\n"
                else:
                    # 原来的显示方式
                    for result in results:
                        title = result.get('title', '无标题')
                        page_id = result.get('id', '')
                        score = result.get('score', 0)
                        notion_link = f"https://www.notion.so/{page_id.replace('-', '')}" if page_id else "#"
                        search_results_md += f"- [{title}]({notion_link}) (相关度: {score:.2f})\n"
                    search_results_md += "\n"

        # 如果没有从流式响应获取内容，尝试从其他类型获取
        elif len(assistant_response) == 0:
            if response_type == "assistant_step" and data.get("namespace") == "chat":
                value = data.get("value", "")
                if value:
                    assistant_response = value
            
            elif response_type in ["assistant", "message"]:
                value = data.get("value", "")
                if value:
                    assistant_response = value

    # 添加搜索结果（如果有）
    if search_results_md and assistant_response:
        assistant_response += "\n\n---\n\n" + search_results_md
    
    return assistant_response or "抱歉，我无法生成回答。请重试或换一个问题。"

# --- 展示聊天记录的函数 ---
def display_chat():
    """展示聊天历史记录"""
    if not st.session_state.messages:
        st.info("开始新的对话吧！")
        return
    
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <div class="message-header">
                    <span class="role-badge user-badge">👤 用户</span>
                </div>
                <div class="message-content">{message["content"]}</div>
                <div class="message-time">{message["time"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="assistant-message">
                <div class="message-header">
                    <span class="role-badge assistant-badge">🤖 AI助手</span>
                </div>
                <div class="message-content">{message["content"]}</div>
                <div class="message-time">{message["time"]}</div>
            </div>
            """, unsafe_allow_html=True)

# --- 主界面 ---
# 使用两列布局，将聊天历史和输入区域分开
st.title("Notion AI 聊天助手")

# 使用Streamlit内置的边栏功能提供操作按钮
with st.sidebar:
    st.subheader("会话管理")
    if st.button("开始新会话"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.conversation_history = []
        st.session_state.raw_responses = []
        st.session_state.messages = []
        st.session_state.thinking = False
        st.success(f"已创建新会话，ID: {st.session_state.session_id}")
    
    st.text(f"当前 Session ID: {st.session_state.session_id}")
    st.text(f"当前对话轮次: {len(st.session_state.conversation_history) // 2}")

# 使用tabs分离聊天区域和设置区域
tab1, tab2 = st.tabs(["聊天", "设置"])

with tab1:
    # 聊天区域
    chat_container = st.container()
    with chat_container:
        display_chat()
        
        if st.session_state.thinking:
            st.markdown("""
            <div class="assistant-message" style="background-color: #f9f9f9;">
                <div class="message-header">
                    <span class="role-badge assistant-badge">🤖 AI助手</span>
                </div>
                <div class="message-content">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div class="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        思考中...
                    </div>
                </div>
            </div>
            <style>
            .typing-indicator {
                display: inline-flex;
                align-items: center;
            }
            .typing-indicator span {
                height: 8px;
                width: 8px;
                margin: 0 1px;
                background-color: #10a37f;
                border-radius: 50%;
                display: inline-block;
                opacity: 0.4;
                animation: typing 1.5s infinite ease-in-out;
            }
            .typing-indicator span:nth-child(1) { animation-delay: 0s; }
            .typing-indicator span:nth-child(2) { animation-delay: 0.3s; }
            .typing-indicator span:nth-child(3) { animation-delay: 0.6s; }
            @keyframes typing {
                0%, 100% { opacity: 0.4; transform: scale(1); }
                50% { opacity: 1; transform: scale(1.1); }
            }
            </style>
            """, unsafe_allow_html=True)
    
    # 为提问区域创建一个分隔线
    st.markdown("---")
    
    # 提问区域
    search_scope_type = st.radio(
        "搜索范围:",
        ["notion", "ai-knowledge"],
        horizontal=True,
        index=0
    )
    
    user_input = st.text_area(
        "输入问题:",
        height=80,
        placeholder="输入你的问题..."
    )
    
    send_col1, send_col2, send_col3 = st.columns([3, 2, 3])
    with send_col2:
        send_button = st.button("发送", use_container_width=True)

with tab2:
    st.subheader("设置")
    st.write("此处可添加其他设置选项")

# 处理用户输入
if send_button and user_input:
    # 添加用户消息到聊天记录
    current_time = time.strftime("%H:%M:%S")
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "time": current_time
    })
    
    # 清空输入框
    st.session_state.user_query = ""
    
    # 设置思考状态
    st.session_state.thinking = True
    st.rerun()

# 如果处于思考状态，处理API调用
if st.session_state.thinking:
    # 获取最近的用户输入
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        user_input = st.session_state.messages[-1]["content"]
        
        # 调用API
        with st.spinner("正在生成回答..."):
            api_responses = call_notion_ai(
                user_input, 
                st.session_state.session_id,
                st.session_state.conversation_history,
                search_scope=search_scope_type
            )
            
            # 处理API响应
            if api_responses:
                assistant_response = process_api_response(api_responses)
                
                # 更新对话历史
                st.session_state.conversation_history.append({
                    "type": "human",
                    "value": user_input
                })
                st.session_state.conversation_history.append({
                    "type": "assistant",
                    "value": assistant_response
                })
                
                # 添加助手消息到聊天记录
                current_time = time.strftime("%H:%M:%S")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_response,
                    "time": current_time
                })
            else:
                # 处理API调用失败
                current_time = time.strftime("%H:%M:%S")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "抱歉，API调用失败。请检查网络连接或稍后再试。",
                    "time": current_time
                })
        
        # 重置思考状态
        st.session_state.thinking = False
        st.rerun()

# --- 如何运行 ---
st.sidebar.info("""
**如何运行:**
1. 确保已安装 `streamlit`, `requests`, 和 `uuid`:
   ```bash
   pip install streamlit requests uuid
   ```
2. 将你的 `token_v2`, `spaceId`, `current-person-id` 填入脚本中的 `COOKIES` 和 `BASE_DATA`。
3. 在终端中运行:
   ```bash
   streamlit run test_notionai.py
   ```
""")

# (原始的直接执行部分被注释掉或删除，因为现在由 Streamlit 控制)
# # 发送请求
# response = requests.post(url, headers=headers, cookies=cookies, json=data)
# # ... 后续处理逻辑 ...
