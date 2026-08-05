import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent

# Flask service
HOST = os.environ.get("APP_HOST", "0.0.0.0")
PORT = int(os.environ.get("APP_PORT", "5002"))
DEBUG = os.environ.get("APP_DEBUG", "false").lower() in {"1", "true", "yes"}
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-image-edit-secret")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# MySQL
MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "bantch_generate")
MYSQL_CHARSET = "utf8mb4"

# Upstream image API
API_URL = "https://api.gpt.ge/v1/images/edits"
DEFAULT_PROMPT = "**精确换装**1. 将“图2”的上衣与“图3”的下装，完整、精确地转移到“图1”的模特身上。2. 必须严格保持图2与图3中服装的原始设计、纹理与所有细节，不允许添加或删减任何设计元素。3. 保持图1模特的姿势与体型。确保新服装完美贴合其身形，边缘清晰。【最终输出】生成一张高度逼真、光影统一的专业电商产品主图。人物突出，背景协调，画质8K高清，细节锐利，无任何合成痕迹。"
OUTFIT_SINGLE_PROMPT = """核心要求：
将“图2”中的服装完整、精确地转移到“图1”的模特身上，严格保持图2服装的版型、长度、设计细节与材质，不允许任何修改、添加或删减。
执行细则：
服装长度与版型完全固定，以“图2”中服装的实际长度与原有版型为准，直接适配到“图1”模特。禁止参考“图1”中任何服装的长度或版型，禁止因模特体型或姿势而改变服装原有形态。如服装在“图2”中为短款/长款/修身/宽松等，在“图1”中必须保持一致。
设计细节与纹理严格保留：
完全复制“图2”服装的图案、纹理、褶皱、装饰等所有细节，不允许有任何差异。如“图2”服装有特殊剪裁（如不对称下摆、开衩、卷边等），需在“图1”中精确还原。
贴合处理与身形适配：
保持“图1”模特的姿势与体型不变，将“图2”服装自然贴合其身形，确保服装边缘清晰、无穿模。服装与身体的接触部位（如肩线、腰线、袖口等）需过渡自然，但不得改变服装原有的尺寸比例。
光影与环境统一：
服装的光影效果需与“图1”的光源方向、强度及环境色调保持一致。保留“图1”的背景与构图，仅替换服装，确保画面整体协调、无合成痕迹。
输出要求：
生成一张高度逼真、光影统一的专业电商主图。人物突出，画质8K高清，服装细节锐利，无模糊、变形或人工修饰痕迹。最终效果需做到“服装完全来自图2，人物与背景完全来自图1”的无缝融合。"""
WHITE_BACKGROUND_PROMPT = "图1的专业服装平铺图，严格保持原图相同的背面/正面视角，俯拍视角。严禁镜像翻转，严禁左右反转。严格锁定服装轮廓与袖长，完全照搬原图版型，不更改任何剪裁比例，保持原始面料质感。纯白色背景（参考图2色值），无阴影，无渐变，无褶皱。移除所有吊牌与标签。8K高清，电商级质感。"
GENERATION_MODES = {
    "outfit_single": {"prompt": OUTFIT_SINGLE_PROMPT, "image_count": 2},
    "outfit_multi": {"prompt": DEFAULT_PROMPT, "image_count": 3},
    "white_background": {"prompt": WHITE_BACKGROUND_PROMPT, "image_count": 1},
    "custom": {"prompt": None, "image_count": None},
}
MAX_UPLOAD_IMAGE_BYTES = 5 * 1024 * 1024
VALID_MODELS = {"nano-banana-pro", "nano-banana-pro-2k", "gpt-image-2", "gpt-image-2-c"}
VALID_IMAGE_SIZES = {"1k", "2k", "4k"}
VIP_IMAGE_SIZE_MAP = {
    "1k": "1920x1920",
    "2k": "1920x2560",
    "4k": "2048x2048",
}
UPSTREAM_REQUEST_TIMEOUT_SECONDS = 1200
ASYNC_MAX_WAIT_SECONDS = 900
ASYNC_POLL_INTERVAL_SECONDS = 2

# Generated files are stored in YYYY-MM subfolders under this directory.
RESULT_STORAGE_DIR = Path(os.environ.get("RESULT_STORAGE_DIR", PROJECT_DIR / "generated_results")).resolve()
RESULT_DOWNLOAD_TIMEOUT_SECONDS = 180

# The initial super administrator is created only when it does not exist.
DEFAULT_SUPERADMIN_USERNAME = os.environ.get("DEFAULT_SUPERADMIN_USERNAME", "yan")
DEFAULT_SUPERADMIN_PASSWORD = os.environ.get("DEFAULT_SUPERADMIN_PASSWORD", "123456")
DEFAULT_SUPERADMIN_KEY_ENV = os.environ.get("DEFAULT_SUPERADMIN_KEY_ENV", "v_plus")

ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_SUPER_ADMIN = "super_admin"
VALID_ROLES = {ROLE_USER, ROLE_ADMIN, ROLE_SUPER_ADMIN}
CREATABLE_ROLES = {ROLE_USER, ROLE_ADMIN}
