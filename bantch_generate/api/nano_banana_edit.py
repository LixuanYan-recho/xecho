import requests
import os

API_KEY = os.environ.get('blt')
API_URL = "http://api.bltcy.ai/v1/images/edits"
IMAGE_PATHS = [r"E:\YYC\搭配\模特\2026-01-22 185618.jpg",r"E:\YYC\搭配\90S20110772+90D5010685\2026-04-10 102712.jpg",r"E:\YYC\搭配\90S20110772+90D5010685\2026-04-10 102839.jpg"] 
PROMPT = "**精确换装**1. 将“图2”的上衣与“图3”的下装，完整、精确地转移到“图1”的模特身上。2. 必须严格保持图2与图3中服装的原始设计、纹理与所有细节，不允许添加或删减任何设计元素（如额外的口袋、装饰）。3. 保持图1模特的姿势与体型。确保新服装完美贴合其身形，边缘清晰。【最终输出】生成一张高度逼真、光影统一的专业电商产品主图。人物突出，背景协调，画质8K高清，细节锐利，无任何合成痕迹。"
n = 3  # 请求次数

def post_once():
    files = []
    try:
        for i, path in enumerate(IMAGE_PATHS):
            files.append((f'image[{i}]', (path, open(path, 'rb'), 'image/jpeg')))
        data = {'model': 'nano-banana-2', 'prompt': PROMPT, 'response_format': 'url','image_size':'2k'}#gpt-image-2-vip
        return requests.post(
            API_URL,
            headers={'Authorization': f'Bearer {API_KEY}'},
            data=data,
            files=files,
        )
    finally:
        for _, (_, f, _) in files:
            f.close()

for k in range(n):
    print(f"--- 第 {k + 1}/{n} 次请求 ---")
    response = post_once()
    if response.status_code == 200:
        result = response.json()
        for img in result.get('data', []):
            print("图片URL:", img.get('url'))
    else:
        print("失败:", response.text)
