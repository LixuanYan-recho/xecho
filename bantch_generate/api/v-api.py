import requests, pathlib

BASE_URL = "https://api.gpt.ge/v1"
API_KEY = "sk-FwfDEULzYLRgwI9b93F963Ea767846E2B5D8Dc79127eC637"
MODEL = "nano-banana-pro"
IMAGES = [
    r"E:\YYC\搭配\90S2010758+90J5010635\2025.04.03leshero10955.jpg",
    r"E:\YYC\搭配\90S2010758+90J5010635\2026-04-10 102810.jpg",
    r"E:\YYC\搭配\90S2010758+90J5010635\2026-04-10 102910.jpg",
]
PROMPT = "**精确换装**1. 将图2的上衣与图3的下装，完整、精确地转移到图1的模特身上。2. 严格保持图2、图3服装的原始设计、纹理与细节，不得增减任何元素。3. 保持图1模特的姿势与体型，服装完美贴合，边缘清晰。最终输出】一张高度逼真的电商主图，光影统一，8K 画质。"

files = [("image", (p.split("\\")[-1], open(p, "rb"))) for p in IMAGES]
data = {"prompt": PROMPT, "model": MODEL, "size": "2k", "response_format": "url"}

r = requests.post(
    f"{BASE_URL}/images/edits",
    headers={"Authorization": f"Bearer {API_KEY}"},
    files=files,
    data=data,
    timeout=180,
).json()

print(r)