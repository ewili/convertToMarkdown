import requests
import json
import streamlit as st # 导入 streamlit
import uuid # 导入 uuid 库
from collections import Counter

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

# --- Session State 初始化 ---
# 检查 session_id 是否已存在，如果不存在则创建一个新的
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.conversation_history = []  # 初始化对话历史
    st.session_state.raw_responses = []  # 存储原始响应
    # 可以在这里添加一个标记，表示是新会话开始，用于可能的清理操作
    # st.session_state.new_conversation = True
elif 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []  # 确保对话历史存在
if 'raw_responses' not in st.session_state:
    st.session_state.raw_responses = []  # 确保原始响应存储存在

# --- API 调用函数 ---
def call_notion_ai(user_query: str, session_id: str, conversation_history=None): # 增加 conversation_history 参数
    """调用 Notion AI API 并处理响应"""
    data = BASE_DATA.copy() # 复制基础数据结构
    
    # 如果有对话历史，则使用完整的历史记录
    if conversation_history:
        # 先保留原始的context条目
        context_entry = data["transcript"][0]
        # 然后用历史记录替换transcript
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

# --- Streamlit 应用界面 ---
st.title("Notion AI 助手")

# 显示当前的 Session ID
st.sidebar.write(f"当前 Session ID: {st.session_state.session_id}")

# 添加会话管理功能
st.sidebar.subheader("会话管理")
if st.sidebar.button("开始新会话"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.conversation_history = []
    st.session_state.raw_responses = []
    st.sidebar.success(f"已创建新会话，ID: {st.session_state.session_id}")

# 显示历史对话长度
if 'conversation_history' in st.session_state:
    st.sidebar.text(f"当前对话轮次: {len(st.session_state.conversation_history) // 2}")
    
    # 添加选项，查看历史对话
    if st.sidebar.checkbox("显示对话历史"):
        for i, entry in enumerate(st.session_state.conversation_history):
            role = "用户" if entry.get("type") == "human" else "AI助手"
            st.sidebar.text(f"{role}: {entry.get('value', '')[:50]}..." if len(entry.get('value', '')) > 50 else f"{role}: {entry.get('value', '')}")
            if i < len(st.session_state.conversation_history) - 1 and i % 2 == 0:
                st.sidebar.text("---")

# 添加API测试按钮
st.sidebar.subheader("调试工具")
if st.sidebar.button("测试API连接"):
    test_data = {
        "version": 1,
        "state": BASE_DATA["state"],
        "transcript": BASE_DATA["transcript"],
        "spaceId": BASE_DATA["spaceId"],
        "analytics": {
            "sessionId": st.session_state.session_id,
            "assistantSurface": "fullPage",
            "openedFrom": "sidebar"
        },
        "searchScope": {"type": "notion"},
        "userTimeZone": "Asia/Shanghai",
        "useUncited": True,
        "useLangXmlTag": True,
        "useMarkdown": True
    }
    test_data["transcript"].append({
        "type": "human",
        "value": "Hello"  # 简单的测试消息
    })
    
    try:
        st.sidebar.text("正在测试API连接...")
        test_response = requests.post(
            url, 
            headers=HEADERS, 
            cookies=COOKIES, 
            json=test_data,
            timeout=10  # 设置10秒超时
        )
        
        if test_response.status_code == 200:
            st.sidebar.success(f"API连接成功! 状态码: {test_response.status_code}")
            # 显示响应头信息
            st.sidebar.text("响应头信息:")
            for key, value in test_response.headers.items():
                if key.lower() in ['content-type', 'server', 'date']:
                    st.sidebar.text(f"{key}: {value}")
            
            # 尝试解析一小部分响应内容
            try:
                content_preview = test_response.text[:200] if test_response.text else "无内容"
                st.sidebar.text(f"响应内容预览: {content_preview}")
            except:
                st.sidebar.text("无法显示响应内容")
        else:
            st.sidebar.error(f"API连接失败! 状态码: {test_response.status_code}")
            st.sidebar.text(f"错误信息: {test_response.text[:200]}")
    except Exception as e:
        st.sidebar.error(f"连接测试出错: {e}")

# 查看原始响应功能
if 'raw_responses' in st.session_state and len(st.session_state.raw_responses) > 0:
    st.sidebar.subheader("查看原始响应")
    response_index = st.sidebar.selectbox(
        "选择要查看的响应", 
        range(len(st.session_state.raw_responses)),
        format_func=lambda i: f"响应 {i+1}: {st.session_state.raw_responses[i]['query'][:20]}..."
    )
    
    if st.sidebar.button("显示所选响应的详细信息"):
        selected_response = st.session_state.raw_responses[response_index]
        st.sidebar.text(f"查询: {selected_response['query']}")
        
        # 创建一个可展开区域显示解析后的类型
        if 'parsed' in selected_response and selected_response['parsed']:
            parsed_types = [item.get('type', 'unknown') for item in selected_response['parsed']]
            type_counts = Counter(parsed_types)
            st.sidebar.text(f"响应类型: {dict(type_counts)}")
            
            # 显示partial_assistant_step的内容
            partial_steps = [
                item.get('value', '') 
                for item in selected_response['parsed'] 
                if item.get('type') == 'partial_assistant_step'
            ]
            if partial_steps:
                combined = ''.join(partial_steps)
                st.sidebar.text(f"流式回复内容 (长度: {len(combined)})")
                if len(combined) > 100:
                    st.sidebar.text(f"{combined[:100]}...")
                else:
                    st.sidebar.text(combined)

# 添加更多调试信息显示
st.sidebar.subheader("认证信息")
if st.sidebar.checkbox("显示API凭证信息"):
    st.sidebar.text("API凭证信息（部分隐藏）:")
    token = COOKIES.get("token_v2", "")
    # 只显示token的前10个和后10个字符
    masked_token = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else token
    st.sidebar.text(f"token_v2: {masked_token}")
    st.sidebar.text(f"space_id: {BASE_DATA['spaceId']}")
    st.sidebar.text(f"person_id: {BASE_DATA['state']['context']['current-person-id']}")

# 用户输入
user_input = st.text_input("请输入你的问题：", key="user_query")

# 提交按钮
if st.button("提问"):
    if user_input:
        # 创建状态显示的placeholder
        status_placeholder = st.empty()
        status_placeholder.info("正在思考中...")
        
        # 从 session_state 获取 session_id 和对话历史并传递给 API 调用函数
        api_responses = call_notion_ai(
            user_input, 
            st.session_state.session_id,
            st.session_state.conversation_history
        )

        if api_responses:
            st.subheader("AI 回复：")
            assistant_response = ""
            search_results_md = ""
            
            # 创建动态内容显示的placeholder
            response_placeholder = st.empty()
            
            # 定义搜索状态标记
            is_searching = False
            has_search_results = False
            
            # 处理响应类型检测搜索状态
            for data in api_responses:
                response_type = data.get("type")
                
                # 检测到搜索相关响应类型时更新状态
                if response_type == "search" and not is_searching:
                    is_searching = True
                    status_placeholder.info("正在检索知识库...")
                
                # 检测到搜索结果时更新状态
                elif response_type == "search_results" and not has_search_results:
                    has_search_results = True
                    status_placeholder.info("找到相关搜索结果，正在生成回答...")
            
            # 单独处理所有partial_assistant_step，这是流式响应的关键
            partial_responses = []
            for data in api_responses:
                if data.get("type") == "partial_assistant_step":
                    value = data.get("value", "")
                    if value:
                        partial_responses.append(value)
                        # 当开始有回答内容时更新状态
                        if len(partial_responses) == 1:
                            status_placeholder.success("已开始生成回答")
            
            # 如果有流式响应片段，先合并它们
            if partial_responses:
                combined_partial = "".join(partial_responses)
                st.sidebar.text(f"合并流式响应片段，长度: {len(combined_partial)}")
                assistant_response = combined_partial
            
            # 调试信息：显示所有响应类型及其出现次数
            response_types = [data.get("type") for data in api_responses]
            type_counts = Counter(response_types)
            st.sidebar.text(f"响应类型计数: {dict(type_counts)}")

            # 如果从流式响应中已获取了内容，不需要再处理其他类型
            # 但仍然处理search_results和错误信息
            for data in api_responses:
                response_type = data.get("type")

                if response_type == "search":
                    # 记录到调试区域
                    st.sidebar.text(f"搜索查询: {data.get('value')}")

                elif response_type == "search_results":
                    value = data.get("value", {})
                    results = value.get("results", [])
                    if results:
                        search_results_md += "**相关搜索结果:**\n\n"
                        for result in results:
                            title = result.get('title', '无标题')
                            path = result.get('path', '')
                            page_id = result.get('id', '')
                            score = result.get('score', 0)
                            # 构建 Notion 页面链接
                            notion_link = f"https://www.notion.so/{page_id.replace('-', '')}" if page_id else "#"
                            search_results_md += f"- [{title}]({notion_link}) (相关度: {score:.2f})\n"
                        search_results_md += "\n"

                # 如果没有从流式响应获取内容，则尝试从其他类型获取
                elif len(assistant_response) == 0:
                    # 完整助手回复
                    if response_type == "assistant_step" and data.get("namespace") == "chat":
                        value = data.get("value", "")
                        if value:
                            assistant_response = value
                            st.sidebar.text(f"获取完整回复，长度: {len(value)}")
                            status_placeholder.success("回答生成完成")
                    
                    # 其他可能类型
                    elif response_type in ["assistant", "message"]:
                        value = data.get("value", "")
                        if value:
                            assistant_response = value
                            st.sidebar.text(f"从{response_type}获取回复，长度: {len(value)}")
                            status_placeholder.success("回答生成完成")

                # 始终处理错误消息
                elif response_type == "error":
                    error_msg = data.get("value")
                    st.warning(error_msg)
                    st.sidebar.text(f"错误: {error_msg[:50]}..." if len(error_msg) > 50 else error_msg)
                    status_placeholder.error("处理出错")

            # 显示最终拼接的助手回复
            if assistant_response:
                # 清除状态提示
                status_placeholder.empty()
                # 显示回答
                st.markdown(assistant_response)
                st.sidebar.text(f"助手回复总长度: {len(assistant_response)}")
                
                # 更新对话历史
                st.session_state.conversation_history.append({
                    "type": "human",
                    "value": user_input
                })
                st.session_state.conversation_history.append({
                    "type": "assistant",
                    "value": assistant_response
                })
            else:
                status_placeholder.warning("未获取到回答")
                # 调试：显示部分原始响应数据
                if api_responses:
                    st.sidebar.text("未找到可用的回复内容，显示部分原始数据：")
                    for i, resp in enumerate(api_responses[:3]):  # 只显示前3条
                        st.sidebar.text(f"响应 {i+1}: {str(resp)[:100]}...")
                
                # 如果没有 assistant_step，检查是否有其他类型的有效回复
                if not search_results_md and all(r.get('type') not in ['search', 'search_results'] for r in api_responses if r.get('type') != 'error'):
                    st.warning("未能从 Notion AI 获取有效回复。")
                    st.sidebar.text("未找到任何有效的助手回复")

            # 显示搜索结果（如果有）
            if search_results_md:
                 st.markdown("---") # 分隔线
                 st.markdown(search_results_md)
    else:
        st.warning("请输入问题后再提问。")

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
