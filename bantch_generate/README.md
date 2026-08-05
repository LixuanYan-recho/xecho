# YCC-Edit

多人使用的 Flask 图片编辑服务。用户登录后使用绑定到账号的本机 API Key 环境变量请求图片接口，任务和结果写入 MySQL，结果图片按月保存到本地。

## 目录结构

```text
.
├─ app.py                       # 服务主入口
├─ webapp/
│  ├─ config.py                 # 所有可调服务、MySQL、API、存储配置
│  ├─ database/                 # MySQL 连接与表结构初始化
│  ├─ repositories/             # 用户、任务、结果数据访问
│  ├─ routes/                   # 登录、生图、管理、结果下载路由
│  ├─ services/                 # 上游图片 API 与本地结果存储
│  └─ utils/                    # 权限与统一响应
├─ templates/                   # 登录、生图、设置、用量页面
├─ static/js/                   # 生图页面前端模块
└─ generated_results/YYYY-MM/   # 默认结果图片目录
```

## 安装和启动

```powershell
python -m pip install -r requirements.txt
python app.py
```

浏览器访问 `http://127.0.0.1:5002`。

首次启动会自动创建 `bantch_generate` 数据库和以下三张表：

- `users`：账号、密码哈希、身份、绑定的密钥环境变量、创建时间
- `tasks`：每次请求、模型、提示词、开始/完成时间、成功状态和失败原因
- `results`：提示词、本地结果路径、原始 JSON、时间、模型和来源 URL

默认超级管理员为 `yan / 123456`。生产使用前请登录后规划账号，并通过 `DEFAULT_SUPERADMIN_PASSWORD` 环境变量设置更强的首次密码。

## 权限

- 用户：只显示生图页面，只能下载自己的结果
- 管理员：生图，并查看所有账号的成功请求用量
- 超级管理员：管理员权限，并可创建用户或管理员账号

超级管理员创建账号时填写的是环境变量名，不是密钥值。服务端根据当前登录用户从数据库读取变量名，再从本机环境变量读取真正的密钥；前端不能选择或覆盖密钥。

Windows 下会依次读取当前进程、当前用户和系统环境变量。服务启动后新建的用户变量或系统变量也可以被识别。

## 配置

默认值集中在 `webapp/config.py`，均可通过对应环境变量覆盖：

- MySQL：`MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE`
- Flask：`APP_HOST`、`APP_PORT`、`APP_DEBUG`、`FLASK_SECRET_KEY`
- 结果目录：`RESULT_STORAGE_DIR`
- 初始管理员：`DEFAULT_SUPERADMIN_USERNAME`、`DEFAULT_SUPERADMIN_PASSWORD`、`DEFAULT_SUPERADMIN_KEY_ENV`

账号绑定的 API Key 环境变量需提前在启动服务的系统环境中配置。例如账号绑定 `v`，服务进程必须能读取环境变量 `v`。

## 并发隔离

- 每次请求生成独立 `request_id`
- 每个请求依据 session 中的用户 ID 重新查库，密钥不会来自前端
- 每次数据库操作使用独立连接，不共享游标或事务
- 文件名由 `request_id + 结果序号` 组成，并按 `YYYY-MM` 独立归档
- Flask 本地入口启用多线程，可同时处理多个用户的请求
- 页面切换或刷新后，会从数据库恢复当前用户最近 10 个任务，并自动刷新进行中的任务

## Windows 内网部署建议

约 10 人使用时不建议长期直接运行 Flask 自带开发服务器。可以安装 Waitress，并预留足够线程处理耗时较长的生图请求：

```powershell
python -m pip install waitress
waitress-serve --listen=0.0.0.0:5002 --threads=20 --channel-timeout=1800 app:app
```

也可以直接双击项目根目录中的：

- `start_waitress.bat`：隐藏窗口后台启动，并将 PID 写入 `.waitress.pid`
- `stop_waitress.bat`：只停止 PID 文件对应的本项目 Waitress 进程

运行日志保存在 `logs/waitress.out.log` 和 `logs/waitress.error.log`。关闭启动脚本的终端窗口不会停止服务。

同时建议：

- Windows 防火墙仅允许办公内网网段访问 5002 端口，不要直接暴露到公网
- 设置强随机 `FLASK_SECRET_KEY`，并修改默认超级管理员密码
- 定期备份 MySQL 的 `bantch_generate` 数据库和 `generated_results` 目录
- 关闭 Windows 自动睡眠，给 Python 服务配置开机自启和失败后自动重启
- 如果以后并发请求经常超过 10 个，改用后台任务队列，让 Web 请求只负责提交任务和查询状态

## 生图接口

`POST /api/generate`，请求类型为 `multipart/form-data`：

- `model`：`nano-banana-pro`、`nano-banana-pro-2k`、`gpt-image-2`、`gpt-image-2-c`
- `prompt`：可选，为空时使用默认提示词
- `image_size`：`1k`、`2k`、`4k`；`gpt-image-2-c` 不传
- `aspect_ratio`：可选
- `images[]`：至少一张图片

### 封装模式

- `generation_mode=outfit_single`：整体换装，按“模特图、参考图”顺序上传 2 张图片，服务端使用固定整体换装提示词
- `generation_mode=outfit_multi`：多件换装，按“模特图、上装、下装”顺序上传 3 张图片，服务端使用固定精确换装提示词
- `generation_mode=white_background`：AI 白底图，上传 1 张产品图，服务端使用固定白底图提示词
- `generation_mode=custom`：必须填写自定义提示词并至少上传一张图片

所有模式均限制每张上传图片不超过 5 MB，前后端都会校验。

接口不再接受 `api_key` 字段，也不再包含云雾 `generateContent` 分支，只请求 `https://api.gpt.ge/v1/images/edits`。
