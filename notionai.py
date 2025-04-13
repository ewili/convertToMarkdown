import requests
import json

# API URL
url = "https://www.notion.so/api/v3/runAssistantV2"

# 请求头
headers = {
 #"x-notion-active-user-header": "e63761a2-52de-4e41-af11-64e08edb8797",
    #"x-notion-space-id": "65492b2e-2341-40df-8dd9-40cdfd3314cf"
}

# Cookie
cookies = {
 "token_v2": "v03%3AeyJhbGciOiJkaXIiLCJraWQiOiJwcm9kdWN0aW9uOnRva2VuLXYzOjIwMjQtMTEtMDciLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIn0..PGsBAMQM4lmKJlREfOE4Sg.0nYw4LT7Pyxb3S3CkbdUbCDdXhLj512F5JuPfgRz7LtwWofpF-Br1_8TcN0tSpDKParWP38t2TEwDGQIWdemSbCCZWcQsalflpupR5DTf4cIy8IqM6MdHMCHBEBDrJ1UhOU5IyuY-LNaQGoG9kLaQyhwNvlulf7Ye1OyyCEnMvL1pRPvlRjnYkaDUmxEFJHQljqym1-kzg9liYoGNciSPYbw8o_PP5N1nWfhQwrardbsDmiQzDDOwumwvSiKnb0mHVJ8OTbQOSQwSxMZJ2JnwwujBzc77cU_FX2g6kutV-c0MKnF7Q3jsQCiwGNI1Nradz21iR-fG5rujUJQ_sdYVPzqikeoCqTB-Pr063NwZmCrwWF6x0yegVFvhkKo-TrroKSRk6jihhfcTT61MlEY8OThHB0BKRkLRGLAUhjGSgSMj4TjawKwwNPkJYTc7hyA.0g0eorISfe90dJgB1_8rRZQpt6llXiB6qSCVeg4IhEA"
}

# 请求数据
data = {
    "version": 1,
    "state": {
        "version": 16,
        "context": {
            "mode": "direct",
            "available-commands": [
                "load-database", "load-page", "load", "query-database", "search", 
                "chat", "search-databases", "load-slack",
                #"insert-before", "insert-after", "insert-inside", "delete", "set-title", 
               # "set-attribute", "set-tag-name", "set-property", "replace", "create-page", "replace"
            ],
            #"current-datetime": "2025-04-13T22:27:04.116+08:00",
            "current-page-name": "",
            "current-person-name": "ewili",
            "current-space-name": "V40/2",
            "current-person-id": "e63761a2-52de-4e41-af11-64e08edb8797"
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
                    #"insert-before", "insert-after", "insert-inside", "delete", "set-title", 
                    #"set-attribute", "set-tag-name", "set-property", "replace", "create-page", "replace"
                ],
                #"current-datetime": "2025-04-13T22:27:04.116+08:00",
                "current-page-name": "",
                "current-person-name": "ewili",
                "current-space-name": "V40/2",
                "current-person-id": "0"
            }
        },
        {
            "type": "human",
            "value": "如何使用xtdata判断一只股票是否涨停"
        }
    ],
    "spaceId": "65492b2e-2341-40df-8dd9-40cdfd3314cf",
    "analytics": {
        "sessionId": "390c811a-ac99-468f-8f35-e8c953d10bcd",
        #"inferenceId": "bee9ccf0-2c80-456e-bbb6-ea0166f49af7",
        "assistantSurface": "fullPage",
        "openedFrom": "sidebar"
    },
    "searchScope": {
        "type": "notion"
    },
    "userTimeZone": "Asia/Shanghai",
    "useUncited": True,
    "useLangXmlTag": True,
    "useMarkdown": False
}

# 发送请求
response = requests.post(url, headers=headers, cookies=cookies, json=data)

# 按行分割响应文本
lines = response.text.strip().split('\n')

# 逐行解析 JSON
for line in lines:
    try:
        data = json.loads(line)
        if data.get("type") == "search" :
            print(data.get("value"))
        
        if data.get("type") == "search_results" :
            value = data.get("value")
            results = value.get("results")
            for result in results:
                print(result.get("id"))
                print(result.get("title"))
                print(result.get("path"))
                print(result.get("score"))

        if data.get("type") == "assistant_step" and data.get("namespace") == "chat":
            print(data.get("value"))
    except json.JSONDecodeError as e:
        print(f"无法解析行: {line}, 错误: {e}")
