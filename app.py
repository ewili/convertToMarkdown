import streamlit as st
import requests
import json
import uuid # 导入 uuid 库

# API URL (从 notionai.py 复制)
url = "https://www.notion.so/api/v3/runAssistantV2"

# 请求头 (从 notionai.py 复制)
# 注意：敏感信息如 token 通常不应硬编码，后续可以考虑使用 Streamlit secrets 管理
headers = {
    #"x-notion-active-user-header": "YOUR_ACTIVE_USER_HEADER", # 替换为你自己的值
    #"x-notion-space-id": "YOUR_SPACE_ID" # 替换为你自己的值
}

# Cookie (从 notionai.py 复制)
# 注意：敏感信息如 token 通常不应硬编码，后续可以考虑使用 Streamlit secrets 管理
cookies = {
    "token_v2": "v03%3AeyJhbGciOiJkaXIiLCJraWQiOiJwcm9kdWN0aW9uOnRva2VuLXYzOjIwMjQtMTEtMDciLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIn0..PGsBAMQM4lmKJlREfOE4Sg.0nYw4LT7Pyxb3S3CkbdUbCDdXhLj512F5JuPfgRz7LtwWofpF-Br1_8TcN0tSpDKParWP38t2TEwDGQIWdemSbCCZWcQsalflpupR5DTf4cIy8IqM6MdHMCHBEBDrJ1UhOU5IyuY-LNaQGoG9kLaQyhwNvlulf7Ye1OyyCEnMvL1pRPvlRjnYkaDUmxEFJHQljqym1-kzg9liYoGNciSPYbw8o_PP5N1nWfhQwrardbsDmiQzDDOwumwvSiKnb0mHVJ8OTbQOSQwSxMZJ2JnwwujBzc77cU_FX2g6kutV-c0MKnF7Q3jsQCiwGNI1Nradz21iR-fG5rujUJQ_sdYVPzqikeoCqTB-Pr063NwZmCrwWF6x0yegVFvhkKo-TrroKSRk6jihhfcTT61MlEY8OThHB0BKRkLRGLAUhjGSgSMj4TjawKwwNPkJYTc7hyA.0g0eorISfe90dJgB1_8rRZQpt6llXiB6qSCVeg4IhEA"
} # 替换为你自己的值


# 封装 Notion AI 请求逻辑
def get_notion_ai_response(user_query: str, session_id: str):
    """
    向 Notion AI API 发送请求并处理响应。

    Args:
        user_query: 用户输入的问题。
        session_id: 当前会话的 ID。

    Returns:
        一个包含助手回复和原始搜索结果列表（如果有）的元组 (assistant_response, search_results_list)。
        如果发生错误，则返回 (None, None)。
    """
    # --- 测试：硬编码查询以匹配 notionai.py (注释掉) ---
    # hardcoded_query = "如何使用xtdata判断一只股票是否涨停"
    # -----------------------------------------

    # 请求数据 (基于 notionai.py 修改)
    data = {
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
                "current-person-name": "ewili", # 可以考虑从环境变量或配置中读取
                "current-space-name": "V40/2", # 可以考虑从环境变量或配置中读取
                "current-person-id": "0" # 改回 "0"，以匹配原始 notionai.py 的工作配置
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
                    "current-person-name": "ewili",
                    "current-space-name": "V40/2",
                    "current-person-id": "0" # 改回 "0"，以匹配原始 notionai.py 的工作配置
                }
            },
            {
                "type": "human",
                "value": user_query # 恢复使用函数参数传递的 user_query
                # "value": hardcoded_query # 注释掉硬编码的值
            }
        ],
        "spaceId": "65492b2e-2341-40df-8dd9-40cdfd3314cf", # 替换为你自己的 spaceId
        "analytics": {
            "sessionId": session_id,
            "assistantSurface": "fullPage",
            "openedFrom": "sidebar"
        },
        "searchScope": {
            "type": "notion"
        },
        "userTimeZone": "Asia/Shanghai",
        "useUncited": True,
        "useLangXmlTag": True,
        "useMarkdown": True # 改回 False，以匹配原始脚本和避免潜在的 400 错误
    }

    assistant_response = ""
    search_results_list = [] # 初始化为空列表，用于存储原始搜索结果

    try:
        response = requests.post(url, headers=headers, cookies=cookies, json=data)
        response.raise_for_status() # 检查请求是否成功
        # 按行分割响应文本
        lines = response.text.strip().split('\n')
        for i, line in enumerate(lines):
            if not line: # 跳过空行
                continue
            try:
                parsed_line = json.loads(line)

                if parsed_line.get("type") == "assistant_step" and parsed_line.get("namespace") == "chat_markdown":
                    assistant_response = parsed_line.get("value")
                if parsed_line.get("type") == "search_results":
                    value = parsed_line.get("value", {})
                    # 将结果列表直接添加到 search_results_list
                    search_results_list.extend(value.get("results", []))

            except json.JSONDecodeError as e:
                st.warning(f"无法解析行 {i+1}: {line}, 错误: {e}")
            except Exception as e:
                st.error(f"处理行 {i+1} 时发生未知错误: {line}, 错误: {e}")

        # 返回助手回复和原始搜索结果列表
        return assistant_response, search_results_list

    except requests.exceptions.RequestException as e:
        st.error(f"请求 Notion API 时出错: {e}")
        # --- 调试：打印错误时的响应（如果可能）---
        if 'response' in locals() and response is not None:
             st.text("发生错误时的响应内容:")
             st.text_area("Error Response Text", response.text, height=200)
        # --- 调试结束 ---
        return None, None
    except Exception as e:
        st.error(f"处理 Notion AI 响应时发生未知错误: {e}")
        return None, None


# Streamlit 应用界面
st.title("Notion AI Streamlit 应用")

# --- Session State 初始化 ---
# 检查 session_state 中是否已有 sessionId，如果没有则初始化
if 'sessionId' not in st.session_state:
    st.session_state.sessionId = str(uuid.uuid4())
    # 改为初始化 interactions 列表
    st.session_state.interactions = []

# --- UI 元素 ---
# "新会话" 按钮
if st.button("✨ 新会话"):
    st.session_state.sessionId = str(uuid.uuid4()) # 生成新的 sessionId
    # 清空 interactions 列表
    st.session_state.interactions = []
    st.rerun() # 重新运行应用以应用更改并清空输入框

# 显示当前 sessionId (可选，用于调试)
# st.caption(f"当前 Session ID: {st.session_state.sessionId}")

# 用户输入区域
user_input = st.text_area("请输入你的问题：", key="user_input") # 使用 key 保证 reru 后内容清空

# 发送按钮
if st.button("发送请求"):
    if user_input:
        # 准备当前交互的数据结构
        current_interaction = {"user": user_input}

        with st.spinner("正在向 Notion AI 发送请求..."):
            # 使用当前 session_state 中的 sessionId 调用 API
            # 接收原始搜索结果列表
            assistant_response, search_results_list = get_notion_ai_response(user_input, st.session_state.sessionId)

        if assistant_response is not None:
            # 将 AI 回复添加到当前交互
            current_interaction["assistant"] = assistant_response
            # 如果有搜索结果，将原始列表添加到当前交互
            if search_results_list:
                 current_interaction["search_results"] = search_results_list
            # 将完整的交互记录添加到列表中
            st.session_state.interactions.append(current_interaction)
        else:
            st.error("未能获取 AI 回复。")
            # 可以考虑也将错误信息记录到 interactions 中，或者单独处理
            current_interaction["error"] = "未能获取 AI 回复。"
            st.session_state.interactions.append(current_interaction)


        # 清空输入框 (通过 rerun 实现)
        st.rerun()

    else:
        st.warning("请输入问题！")

# --- 显示聊天记录 ---
if not st.session_state.interactions:
    st.info("开始提问吧！")
else:
    # 反转 interactions 列表来实现由近到远排序
    for interaction in reversed(st.session_state.interactions):
        # 1. 显示用户消息
        with st.chat_message("user"):
            st.markdown(interaction["user"])

        # 2. 显示 AI 回复 (如果存在)
        if "assistant" in interaction:
            with st.chat_message("assistant"):
                st.markdown(interaction["assistant"])

        # 3. 按路径分组显示搜索结果 (如果存在)
        if "search_results" in interaction and interaction["search_results"]:
             results_list = interaction["search_results"]
             # 按 'path' 分组
             grouped_results = {}
             for result in results_list:
                 path = result.get('path', '未知路径')
                 if path not in grouped_results:
                     grouped_results[path] = []
                 grouped_results[path].append(result)

             # 在助手的消息框内显示分组后的搜索结果
             with st.chat_message("assistant"):
                 st.markdown("### 搜索结果：")
                 if not grouped_results:
                     st.markdown("没有找到相关的搜索结果。")
                 else:
                     # 遍历分组后的结果并使用 expander 显示
                     for path, results_in_path in grouped_results.items():
                         with st.expander(f"**路径:** {path} ({len(results_in_path)} 个结果)", expanded=False): # 默认不展开
                             for result in results_in_path:
                                 st.markdown(f"- **标题:** {result.get('title', 'N/A')}")
                                 # 可以选择性显示 ID 和分数
                                 # st.markdown(f"  - ID: {result.get('id', 'N/A')}")
                                 st.markdown(f"  - **分数:** {result.get('score', 'N/A'):.4f}") # 格式化分数显示
                                 st.markdown("---") # 添加分隔线


        # 处理可能记录的错误信息
        if "error" in interaction:
             # 如果只有错误信息，没有AI回复，则显示错误
             if "assistant" not in interaction:
                 with st.chat_message("error"): # 使用 error 角色
                     st.error(interaction["error"])
             # 如果AI回复和错误信息都有（例如API调用失败），可以在AI回复后附加错误提示
             # else:
             #     with st.chat_message("assistant"):
             #         st.warning(f"提示：{interaction['error']}") # 或者用其他方式显示错误