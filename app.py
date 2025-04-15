import streamlit as st
import requests
import json
import uuid # 导入 uuid 库
import pandas as pd # 导入 pandas 库

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
def get_notion_ai_response(user_query: str, session_id: str, history: list):
    """
    向 Notion AI API 发送请求并处理响应。

    Args:
        user_query: 用户输入的问题。
        session_id: 当前会话的 ID。
        history: 包含历史交互记录的列表。

    Returns:
        一个包含助手回复和原始搜索结果列表（如果有）的元组 (assistant_response, search_results_list)。
        如果发生错误，则返回 (None, None)。
    """
    # --- 测试：硬编码查询以匹配 notionai.py (注释掉) ---
    # hardcoded_query = "如何使用xtdata判断一只股票是否涨停"
    # -----------------------------------------

    # 构建 transcript，先添加 context
    transcript = [
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
                "current-person-id": "e63761a2-52de-4e41-af11-64e08edb8797"
            }
        }
    ]

    # 添加历史对话到 transcript
    for interaction in history:
        if "user" in interaction:
            transcript.append({
                "type": "human",
                "value": interaction["user"]
            })
        if "assistant" in interaction:
             # 检查 assistant 回复是否为空，非空才添加
            if interaction["assistant"]:
                transcript.append({
                    "type": "assistant_step",
                    "namespace": "chat_markdown",
                    "value": interaction["assistant"]
                })
        # 注意：这里暂时不添加错误信息到 transcript

    # 添加当前用户输入到 transcript
    transcript.append({
        "type": "human",
        "value": user_query
    })


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
                "current-person-id": "e63761a2-52de-4e41-af11-64e08edb8797" # 改回 "0"，以匹配原始 notionai.py 的工作配置
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
        # 使用构建好的 transcript
        "transcript": transcript,
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
        "useMarkdown": True # 保持 True，以获取 Markdown 格式的回复
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

                # 仅累加 type 为 assistant_step 且 namespace 为 chat_markdown 的 value
                if parsed_line.get("type") == "assistant_step" and parsed_line.get("namespace") == "chat_markdown":
                    assistant_response += parsed_line.get("value", "") # 使用 += 进行累加
                if parsed_line.get("type") == "search_results":
                    value = parsed_line.get("value", {})
                    # 将结果列表直接添加到 search_results_list
                    search_results_list.extend(value.get("results", []))

            except json.JSONDecodeError as e:
                st.warning(f"无法解析行 {i+1}: {line}, 错误: {e}")
            except Exception as e:
                st.error(f"处理行 {i+1} 时发生未知错误: {line}, 错误: {e}")

        # 返回最终累加的助手回复和原始搜索结果列表
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
st.caption(f"当前 Session ID: {st.session_state.sessionId}")

# 用户输入区域
user_input = st.text_area("请输入你的问题：", key="user_input") # 使用 key 保证 reru 后内容清空

# 发送按钮
if st.button("发送请求"):
    if user_input:
        # 准备当前交互的数据结构
        current_interaction = {"user": user_input}

        with st.spinner("正在向 Notion AI 发送请求..."):
            # 使用当前 session_state 中的 sessionId 和 interactions 调用 API
            assistant_response, search_results_list = get_notion_ai_response(
                user_input,
                st.session_state.sessionId,
                st.session_state.interactions # 传递历史记录
            )

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

             # 直接在主聊天区域显示搜索结果
             st.markdown("### 🔍 搜索结果：") # 在标题前添加搜索图标
             if not grouped_results:
                 st.markdown("没有找到相关的搜索结果。")
             else:
                 # 遍历分组后的结果并使用 expander 显示
                 for path, results_in_path in grouped_results.items():
                     with st.expander(f" {path} ({len(results_in_path)} 个结果)", expanded=False): # 默认不展开
                         # 准备数据
                         table_data = []
                         for result in results_in_path:
                             title = result.get('title', 'N/A')
                             score = result.get('score', 0) # Default to 0 if score is missing
                             result_id = result.get('id')
                             # 构造 Notion 页面链接 (移除 ID 中的 '-')
                             url = f"https://www.notion.so/{result_id.replace('-', '')}" if result_id else None
                             # 不需要预先格式化为 Markdown，直接存储
                             table_data.append({"标题": title, "分数": score, "url": url})

                         # 按分数降序排序
                         sorted_table_data = sorted(table_data, key=lambda x: x.get('分数', 0), reverse=True)

                         if sorted_table_data: # 确保有数据再创建 HTML 表格
                             # 构建 HTML 表格字符串
                             html_table = "<table><thead><tr><th>标题</th><th>分数</th></tr></thead><tbody>"
                             for row in sorted_table_data:
                                 title = row.get('标题', 'N/A')
                                 score_str = f"{row.get('分数', 0):.4f}" # Format score
                                 url = row.get('url')
                                 # 如果有 URL，创建 <a> 标签，否则只显示标题
                                 title_cell = f'<a href="{url}" target="_blank">{title}</a>' if url else title
                                 html_table += f"<tr><td>{title_cell}</td><td>{score_str}</td></tr>"
                             html_table += "</tbody></table>"

                             # 使用 st.markdown 渲染 HTML 表格
                             st.markdown(html_table, unsafe_allow_html=True)

                         else:
                             st.markdown("此路径下无有效结果可展示。") # Handle case where results_in_path might be empty or lack necessary data


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