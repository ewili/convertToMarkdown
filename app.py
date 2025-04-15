import streamlit as st
import requests
import json

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
def get_notion_ai_response(user_query: str):
    """
    向 Notion AI API 发送请求并处理响应。

    Args:
        user_query: 用户输入的问题。

    Returns:
        一个包含助手回复和搜索结果（如果有）的元组 (assistant_response, search_results_text)。
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
            "sessionId": "390c811a-ac99-468f-8f35-e8c953d10bcd", # 使用 notionai.py 中的 sessionId
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
    search_results_text = ""

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
                    results = value.get("results", [])
                    search_results_text += "### 搜索结果：\n"
                    for result in results:
                        search_results_text += f"- **ID:** {result.get('id', 'N/A')}\n"
                        search_results_text += f"- **标题:** {result.get('title', 'N/A')}\n"
                        search_results_text += f"- **路径:** {result.get('path', 'N/A')}\n"
                        search_results_text += f"- **分数:** {result.get('score', 'N/A')}\n\n"

            except json.JSONDecodeError as e:
                st.warning(f"无法解析行 {i+1}: {line}, 错误: {e}")
            except Exception as e:
                st.error(f"处理行 {i+1} 时发生未知错误: {line}, 错误: {e}")

        return assistant_response, search_results_text

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
user_input = st.text_area("请输入你的问题：")

if st.button("发送请求"):
    if user_input:
        with st.spinner("正在向 Notion AI 发送请求..."):
            assistant_response, search_results = get_notion_ai_response(user_input)

        if assistant_response is not None:
            st.subheader("AI 回复:")
            st.markdown(assistant_response) # 使用 markdown 显示回复
        else:
            st.error("未能获取 AI 回复。")

        if search_results:
            st.markdown(search_results)
    else:
        st.warning("请输入问题！")