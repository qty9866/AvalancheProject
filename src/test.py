import time
import requests

# 腾讯云 COS 提供的 100MB 测试文件
test_url = "https://webcloud.tencentcloudapi.com/100MB.zip"

def test_download_speed():
    try:
        # 记录开始时间
        start_time = time.time()

        # 发起 GET 请求，获取文件流
        response = requests.get(test_url, stream=True)
        response.raise_for_status()  # 如果请求失败，将抛出异常

        # 获取文件的总大小
        total_size = int(response.headers.get("content-length", 0))

        # 下载文件并测量速度
        downloaded = 0
        for chunk in response.iter_content(chunk_size=1024 * 1024):  # 每次读取 1MB
            if chunk:
                downloaded += len(chunk)

        # 记录结束时间
        end_time = time.time()

        # 计算下载速度（MB/s）
        elapsed_time = end_time - start_time
        speed = (downloaded / (1024 * 1024)) / elapsed_time  # 转换为MB/s

        # 打印下载结果
        print(f"下载完成：{downloaded / (1024 * 1024):.2f} MB")
        print(f"下载时间：{elapsed_time:.2f} 秒")
        print(f"下载速度：{speed:.2f} MB/s")

    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")

if __name__ == "__main__":
    test_download_speed()