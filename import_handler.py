import os

def import_file(file_name):
    # 修复路径拼接逻辑
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'temp_import', file_name)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件未找到: {file_path}")

    # 执行文件导入逻辑
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        print("文件内容导入成功:", content)

# 示例调用
if __name__ == "__main__":
    try:
        import_file("application.json")
    except Exception as e:
        print("导入失败:", e)