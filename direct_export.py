import requests
import json
import time
import sys
import os
import zipfile
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NotionConfig:
    """Notion导出配置"""
    token: str
    file_token: str
    block_id: str
    space_id: str
    export_format: str = "markdown"
    output_dir: str = "./output"
    extract_dir: str = "./extracted"
    timezone: str = "Asia/Shanghai"
    locale: str = "zh-CN"

class NotionExporter:
    """Notion内容导出工具"""
    
    def __init__(self, config: NotionConfig):
        self.config = config
        self.headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "notion-audit-log-platform": "web",
            "notion-client-version": "23.13.0.2360",
            "origin": "https://www.notion.so",
            "referer": "https://www.notion.so/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "x-notion-active-user-header": "e63761a2-52de-4e41-af11-64e08edb8797",
            "x-notion-space-id": config.space_id
        }
        self.cookies = {
            "token_v2": config.token
        }
        
        # 确保输出目录存在
        os.makedirs(config.output_dir, exist_ok=True)
        os.makedirs(config.extract_dir, exist_ok=True)
    
    def create_export_task(self) -> Optional[str]:
        """创建导出任务并返回任务ID"""
        url = "https://www.notion.so/api/v3/enqueueTask"
        
        payload = {
            "task": {
                "eventName": "exportBlock",
                "request": {
                    "block": {
                        "id": self.config.block_id,
                        "spaceId": self.config.space_id
                    },
                    "recursive": True,
                    "exportOptions": {
                        "exportType": self.config.export_format,
                        "timeZone": self.config.timezone,
                        "locale": self.config.locale,
                        "flattenExportFiletree": True,
                        "collectionViewExportType": "currentView",
                    },
                    "shouldExportComments": False
                }
            }
        }
        
        logger.info(f"发送导出请求... Block ID: {self.config.block_id}, 导出格式: {self.config.export_format}")
        
        try:
            response = requests.post(url, headers=self.headers, cookies=self.cookies, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "taskId" in result:
                task_id = result["taskId"]
                logger.info(f"成功创建导出任务，任务ID: {task_id}")
                return task_id
            else:
                logger.error(f"API响应中没有taskId: {result}")
                return None
        except Exception as e:
            logger.error(f"创建导出任务失败: {str(e)}")
            self._log_response_error(e)
            return None
    
    def check_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """检查任务状态"""
        url = "https://www.notion.so/api/v3/getTasks"
        payload = {"taskIds": [task_id]}
        
        try:
            response = requests.post(url, headers=self.headers, cookies=self.cookies, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "results" in result and result["results"]:
                task = next((t for t in result["results"] if t.get("id") == task_id), None)
                if task:
                    return task
                else:
                    logger.error(f"在响应中找不到任务ID {task_id}")
                    return None
            else:
                logger.error("API响应中没有results字段或结果为空")
                return None
        except Exception as e:
            logger.error(f"检查任务状态失败: {str(e)}")
            self._log_response_error(e)
            return None
    
    def download_file(self, url: str, output_path: str) -> bool:
        """尝试多种方式下载文件"""
        methods = [
            self._download_with_requests,
            self._download_with_curl,
            self._download_with_wget
        ]
        
        for i, method in enumerate(methods):
            logger.info(f"尝试使用方法 {i+1}/{len(methods)} 下载文件...")
            if method(url, output_path):
                return True
        
        logger.error("所有下载方法都失败")
        return False
    
    def _download_with_requests(self, url: str, output_path: str) -> bool:
        """使用requests库下载文件"""
        try:
            logger.info(f"使用requests下载文件: {url}")
            session = requests.Session()
            
            download_headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "referer": "https://www.notion.so/",
                "sec-ch-ua": "\"Microsoft Edge\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-site",
                "upgrade-insecure-requests": "1",
                "priority": "u=0, i"
            }
            
            extended_cookies = {
                "token_v2": self.config.token,
                "file_token": self.config.file_token
            }
            
            session.cookies.update(extended_cookies)
            session.headers.update(download_headers)
            
            response = session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"文件已保存到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"使用requests下载文件失败: {str(e)}")
            self._log_response_error(e)
            return False
    
    def _download_with_curl(self, url: str, output_path: str) -> bool:
        """使用curl命令下载文件"""
        try:
            logger.info(f"使用curl命令下载文件: {url}")
            curl_cmd = f'curl "{url}" ' \
                      f'-H "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7" ' \
                      f'-H "accept-language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6" ' \
                      f'-H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36" ' \
                      f'-H "referer: https://www.notion.so/" ' \
                      f'-H "sec-ch-ua: \\"Microsoft Edge\\";v=\\"135\\", \\"Not-A.Brand\\";v=\\"8\\", \\"Chromium\\";v=\\"135\\"" ' \
                      f'-H "sec-ch-ua-mobile: ?0" ' \
                      f'-H "sec-ch-ua-platform: \\"Windows\\"" ' \
                      f'-H "sec-fetch-dest: document" ' \
                      f'-H "sec-fetch-mode: navigate" ' \
                      f'-H "sec-fetch-site: same-site" ' \
                      f'-H "upgrade-insecure-requests: 1" ' \
                      f'-b "token_v2={self.config.token};file_token={self.config.file_token}" ' \
                      f'-o "{output_path}"'
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result = os.system(curl_cmd)
            
            if result == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"文件已使用curl保存到: {output_path}")
                return True
            else:
                logger.error(f"使用curl下载失败，返回码: {result}")
                return False
        except Exception as e:
            logger.error(f"curl下载过程中出错: {str(e)}")
            return False
    
    def _download_with_wget(self, url: str, output_path: str) -> bool:
        """使用wget命令下载文件"""
        try:
            logger.info(f"使用wget命令下载文件: {url}")
            wget_cmd = f'wget "{url}" ' \
                      f'--header="accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7" ' \
                      f'--header="accept-language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6" ' \
                      f'--header="user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36" ' \
                      f'--header="referer: https://www.notion.so/" ' \
                      f'--header="sec-ch-ua: \\"Microsoft Edge\\";v=\\"135\\", \\"Not-A.Brand\\";v=\\"8\\", \\"Chromium\\";v=\\"135\\"" ' \
                      f'--header="sec-fetch-dest: document" ' \
                      f'--header="sec-fetch-mode: navigate" ' \
                      f'--header="sec-fetch-site: same-site" ' \
                      f'--header="upgrade-insecure-requests: 1" ' \
                      f'--header="cookie: token_v2={self.config.token};file_token={self.config.file_token}" ' \
                      f'-O "{output_path}" --no-check-certificate'
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result = os.system(wget_cmd)
            
            if result == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"文件已使用wget保存到: {output_path}")
                return True
            else:
                logger.error(f"使用wget下载失败，返回码: {result}")
                return False
        except Exception as e:
            logger.error(f"wget下载过程中出错: {str(e)}")
            return False
    
    def extract_zip_file(self, zip_path: str, extract_dir: str) -> bool:
        """解压ZIP文件到指定目录"""
        try:
            logger.info(f"正在解压文件: {zip_path} 到 {extract_dir}")
            
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            logger.info(f"文件已成功解压到: {extract_dir}")
            return True
        except Exception as e:
            logger.error(f"解压文件失败: {str(e)}")
            return False
    
    def _log_response_error(self, e: Exception) -> None:
        """记录请求错误的详细信息"""
        if hasattr(e, 'response') and e.response:
            logger.error(f"响应状态码: {e.response.status_code}")
            logger.error(f"响应内容: {e.response.text}")
    
    def export_and_download(self) -> bool:
        """执行完整的导出和下载流程"""
        # 创建导出任务
        task_id = self.create_export_task()
        if not task_id:
            logger.error("无法创建导出任务，退出")
            return False
        
        # 轮询任务状态
        max_attempts = 100000000
        attempt = 0
        wait_time = 15  # 初始等待时间(秒)
        
        logger.info(f"开始轮询任务状态，最多尝试{max_attempts}次...")
        
        while attempt < max_attempts:
            attempt += 1
            logger.info(f"尝试 {attempt}/{max_attempts}...")
            
            task = self.check_task_status(task_id)
            if not task:
                logger.warning(f"无法获取任务状态，等待{wait_time}秒后重试...")
                time.sleep(wait_time)
                continue
            
            state = task.get("state")
            logger.info(f"任务状态: {state}")
            
            if state == "success":
                if "status" in task and "exportURL" in task["status"]:
                    export_url = task["status"]["exportURL"]
                    output_path = os.path.join(self.config.output_dir, f"notion_export_{task_id}.zip")
                    
                    if self.download_file(export_url, output_path):
                        # 下载成功后解压文件
                        extract_dir = self.config.extract_dir
                        if self.extract_zip_file(output_path, extract_dir):
                            # 解压成功后删除ZIP文件
                            try:
                                os.remove(output_path)
                                logger.info(f"已删除压缩包: {output_path}")
                            except Exception as e:
                                logger.warning(f"删除压缩包失败: {str(e)}")
                                
                            logger.info("下载和解压全部完成!")
                            return True
                        else:
                            logger.error("下载成功但解压失败")
                            return False
                    else:
                        logger.error("所有下载方法都失败")
                        return False
                else:
                    logger.error("任务成功但无导出URL")
                    return False
            elif state == "failure":
                error = "未知错误"
                if "error" in task:
                    if isinstance(task["error"], dict):
                        error = task["error"].get("message", str(task["error"]))
                    else:
                        error = str(task["error"])
                logger.error(f"任务失败: {error}")
                return False
            elif state in ["in_progress", "not_started"]:
                logger.info(f"任务正在进行中，等待{wait_time}秒后再次检查...")
                time.sleep(wait_time)
                # 增加等待时间，但最多不超过15秒
                wait_time = min(wait_time * 1.5, 15)
            else:
                logger.warning(f"未知任务状态: {state}")
                time.sleep(wait_time)
        
        logger.error(f"达到最大尝试次数({max_attempts})，任务未完成")
        return False

def main():
    SHARED_TOKEN = "v03%3AeyJhbGciOiJkaXIiLCJraWQiOiJwcm9kdWN0aW9uOnRva2VuLXYzOjIwMjQtMTEtMDciLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIn0..Z6TJrA0B8xY2nizlT-KQIw.yomlQxqDRrFdnTfK1yBPl3XWdzuPR62pHBsuhT9W-wMfV4aTqiFHBIqMiBIQDl8nHKL5_6-H6KR0QiUMN4qH4aqQS1BUXnusZeTcmQ92OhOwlp4u-iqDDcmWldrY9mgtHDz60x8jgSGSo7gss4yoQ1WfGwrgPH-HLc4s-P4XAZe27Z1nc8ekXGMtmH5xQpd9spGQkHw5ukzuwoi4qyAYy9llnniCWRsTmUgnysoiCASewcN-Xm6YH6b6ivq2sqXJ9IOVIOHDu_mqdR5_BEPMzNPlzkYP2JoY0z6mPLk2hVlU2NYsbmESwWZllLwi4NVGWHF9FKP_qhsLb4ShXVb2d2pMHcWOBX_m5xaEWS5SE24T8iRYx0c9Pv-c2FHU6ImSHusyzMMWYfqJz8a-md24pr1w2I0VjxWh5hRMyEpYY2227Lnf-CrneNlfy0g1Rg2Q.GEnpbxVTSkEyBJtfvEdTz9ywBrAO5zZTQsGLmaoG-B8"
    SHARED_FILE_TOKEN = "v02%3Afile_token%3ATicG4_9V4NuV5eveNIa4hcPiWLX5mt0iAKI-vE9NK-oqq8L5lP87o8m6iArIoaMMR5LcEhOO6ttYtrPmefB4_eoespwM4cRC6lTjGk_IXw6-1SB1pnZmY1rOoUO3va4OT6UYDh6sobXMEbZonFMwGeDOHjE3"
    SHARED_SPACE_ID = "7c640ee1-6009-487c-ae07-bdf3b8fa24a0"
    SHARED_EXPORT_FORMAT = "markdown"
    # 创建多个配置对象
    configs = [
        NotionConfig(
            token=SHARED_TOKEN,
            file_token=SHARED_FILE_TOKEN,
            block_id="11d8089f-d0aa-819a-92fb-ce550a5bf0fe",
            space_id=SHARED_SPACE_ID,
            export_format=SHARED_EXPORT_FORMAT,
            output_dir="D:\\lab\\notion_export\\信息收集",
            extract_dir="D:\\lab\\notion_export\\信息收集"
        ),
        NotionConfig(
            token=SHARED_TOKEN,
            file_token=SHARED_FILE_TOKEN,
            block_id="11d8089f-d0aa-81ad-bbc8-f579fb10267c", # 第三个block_id (示例)
            space_id=SHARED_SPACE_ID,
            export_format=SHARED_EXPORT_FORMAT, # 使用共享的 markdown 格式
            output_dir="D:\\lab\\notion_export\\flomo",
            extract_dir="D:\\lab\\notion_export\\flomo"
        ),
                NotionConfig(
            token=SHARED_TOKEN,
            file_token=SHARED_FILE_TOKEN,
            block_id="11d8089f-d0aa-81c0-b77c-c845b0fb9976", # 第三个block_id (示例)
            space_id=SHARED_SPACE_ID,
            export_format=SHARED_EXPORT_FORMAT, # 使用共享的 markdown 格式
            output_dir="D:\\lab\\notion_export\\\问题解决方案",
            extract_dir="D:\\lab\\notion_export\\\问题解决方案"
        ),
        NotionConfig(
            token=SHARED_TOKEN,
            file_token=SHARED_FILE_TOKEN,
            block_id="11d8089f-d0aa-81e1-a870-eacd76c4d9ab", # 第三个block_id (示例)
            space_id=SHARED_SPACE_ID,
            export_format=SHARED_EXPORT_FORMAT, # 使用共享的 markdown 格式
            output_dir="D:\\lab\\notion_export\\整理",
            extract_dir="D:\\lab\\notion_export\\整理"
        )
    ]
    
    for config in configs:
        logger.info(f"开始处理 Block ID: {config.block_id} 的导出任务")
        # 创建导出器并执行导出
        exporter = NotionExporter(config)
        result = exporter.export_and_download()
        if result:
            logger.info(f"Block ID: {config.block_id} 导出成功")
        else:
            logger.error(f"Block ID: {config.block_id} 导出失败")
        # 可选：在两次导出之间添加延时
        time.sleep(5) # 例如，暂停5秒

def run_with_interval():
    """每隔30分钟执行一次main函数，形成无限循环"""
    try:
        while True:
            logger.info("开始执行导出任务...")
            main()
            logger.info("本轮导出任务完成，暂停30分钟后再次执行")
            time.sleep(1800)  # 暂停30分钟 (30*60=1800秒)
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    run_with_interval()