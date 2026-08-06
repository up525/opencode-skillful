---
name: mac-local-vision
description: 在 Apple Silicon Mac 上使用本地 Ollama 视觉模型读取截图、照片、UI、报错界面、技术图、图表和多张对比图片。默认使用 Qwen3.5-9B；主模型仍负责推理、读取仓库和修改代码，视觉模型只返回可验证的画面观察。
license: MIT
compatibility: opencode
metadata:
  provider: ollama
  model: qwen3.5:9b
  platform: macos-apple-silicon
---

# Mac Local Vision

本 Skill 将运行在 Mac 本机的 Ollama 视觉模型作为纯文本主模型的“眼睛”。默认模型为 `qwen3.5:9b`，适合 16GB 统一内存的 Apple Silicon Mac。图片默认只发送到本机 `127.0.0.1` 上的 Ollama，不上传到云端。

## 何时使用

当用户任务依赖以下画面信息时，必须先调用本地视觉模型，不能凭文件名、上下文或缩略图猜测：

- 截图中的报错、代码、日志、终端输出或文档文字
- UI 的布局、间距、颜色、组件和交互状态
- 架构图、流程图、UML、ER 图、电路图和数据流
- 图表、仪表盘、照片或其他画面细节
- 两张或多张图片之间的差异

纯文本任务、图片与答案无关、或已经有可靠完整的文字转录时，不要调用。

## 本机要求

使用前确认 Ollama 已安装并正在运行：

```bash
ollama --version
curl -fsS http://127.0.0.1:11434/api/tags >/dev/null
```

默认模型：

```bash
ollama pull qwen3.5:9b
```

如需手动测试：

```bash
ollama run qwen3.5:9b /absolute/path/to/image.png \
  "逐字提取图片中的可见文字；看不清的字符标记为不确定，不要猜测。"
```

可以通过环境变量覆盖模型和服务地址：

```bash
export LOCAL_VISION_MODEL='qwen3.5:9b'
export OLLAMA_HOST='http://127.0.0.1:11434'
```

不要自动下载数 GB 的模型。若模型未安装，应明确提示用户执行 `ollama pull qwen3.5:9b`。

## 调用方式

把任务提示作为第一个参数，后面放一张或多张本地图片路径或 HTTP(S) 图片 URL。默认关闭思考，限制输出长度，以降低首字延迟和内存占用。

```bash
python3 - '只描述完成用户任务所需的可见事实，不要猜测。' \
  /absolute/path/to/image.png <<'PY'
import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

prompt, *sources = sys.argv[1:]
if not prompt or not sources:
    raise SystemExit('用法：python3 - <提示词> <图片1> [图片2 ...]')

host = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434').strip().rstrip('/')
if not host.startswith(('http://', 'https://')):
    host = 'http://' + host
model = os.getenv('LOCAL_VISION_MODEL', 'qwen3.5:9b').strip()


def request_json(url, *, payload=None, timeout=10):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode('utf-8')
    request = urllib.request.Request(
        url,
        data=data,
        method='GET' if payload is None else 'POST',
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='replace')
        raise SystemExit(f'Ollama HTTP {exc.code}: {detail}') from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f'无法连接 Ollama：{host}；请确认 Ollama 已启动。原因：{exc.reason}') from exc


def read_image(source):
    if source.startswith(('http://', 'https://')):
        request = urllib.request.Request(source, headers={'User-Agent': 'mac-local-vision-skill/1.0'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.URLError as exc:
            raise SystemExit(f'无法下载图片：{source}；原因：{exc.reason}') from exc

    path = pathlib.Path(source).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f'图片不存在或不是文件：{path}')
    try:
        return path.read_bytes()
    except OSError as exc:
        raise SystemExit(f'无法读取图片：{path}；原因：{exc}') from exc


tags = request_json(f'{host}/api/tags')
installed = {
    item.get('name') or item.get('model')
    for item in tags.get('models', [])
    if isinstance(item, dict)
}
if model not in installed and f'{model}:latest' not in installed:
    raise SystemExit(f'本地未安装模型 {model}。请先执行：ollama pull {model}')

images = [base64.b64encode(read_image(source)).decode('ascii') for source in sources]
payload = {
    'model': model,
    'messages': [
        {
            'role': 'user',
            'content': prompt,
            'images': images,
        }
    ],
    'think': False,
    'stream': False,
    'keep_alive': '10m',
    'options': {
        'temperature': 0.1,
        'num_ctx': 4096,
        'num_predict': 256,
    },
}
result = request_json(f'{host}/api/chat', payload=payload, timeout=180)
message = result.get('message') or {}
content = message.get('content')
if not content:
    raise SystemExit(f'Ollama 未返回可用内容：{json.dumps(result, ensure_ascii=False)[:1000]}')
print(content)
PY
```

多图对比时，把图片按照“目标图、实际图”或“图 1、图 2”的顺序依次传入，并在提示词中明确每张图的角色。

## 低延迟策略

- 本地视觉模型只负责读取画面，不负责完整解决问题。
- OCR、报错提取和普通 UI 识别必须设置 `think: false`。
- 默认输出不超过 256 Token；只在复杂技术图确实需要时提高。
- 长截图先裁剪目标区域；超高分辨率图片先复制到临时目录并缩小，不能覆盖原图。
- 一次只传完成任务所需的图片；不要把无关页面、聊天记录或整套相册一并发送。
- 保持 `keep_alive`，连续调用时避免反复加载模型。
- 不要为了“更完整”要求视觉模型长篇分析，后续推理应交给主模型。

## 任务提示模板

### OCR、代码和报错

```text
逐字提取图片中的全部可见文字，尽量保留换行和标点。
单独列出错误类型、状态码、文件名、行号和命令。
看不清的字符标记为“不确定”，禁止根据语义补全。
不要分析解决方案。
```

### UI 实现

```text
分析这张 UI，只输出可落实到代码的信息：页面层级、布局方向、尺寸比例、间距、对齐、字体、颜色、边框、圆角、阴影、组件和交互状态。
区分明确可见事实与估计值，不要使用“现代”“简洁”等空泛描述。
```

### 技术图

```text
识别图中的实体、标签、箭头方向、数据流、控制流、接口和约束。
按连接关系输出；看不清或图中没有的连接标记为未知，禁止自行补全。
```

### 图表

```text
读取标题、坐标轴、单位、图例、趋势、异常和能够确认的数值。
无法辨认精确值时只给范围或趋势，不得伪造数字。
```

### 图片对比

```text
按从上到下、从左到右的固定顺序比较图片。
分别列出确认差异、不确定差异和仅由缩放或渲染造成的差异。
保持每条差异的位置描述一致。
```

## 结果处理

- Ollama 输出只是视觉观察，由主模型结合用户问题、代码、日志和配置继续推理。
- 命令、标识符、数字、文件名和行号等 OCR 敏感信息应尽量二次核对。
- 涉及代码修改时必须检查真实仓库，不能仅根据截图猜测代码。
- 图片模糊、裁切、遮挡或分辨率不足时，明确说明不确定性。
- 最终回答使用用户当前语言，不必暴露内部视觉调用过程。

## 隐私与网络边界

本地文件通过 `127.0.0.1` 发送给本机 Ollama，不需要 API Key。不要把 `OLLAMA_HOST` 配置成公网地址。传入 HTTP(S) 图片 URL 时会从对应网站下载图片，但模型推理仍在本地完成。遇到密码、Cookie、API Key、私人聊天、身份资料、医疗或财务记录时，只处理完成任务所必需的裁剪区域。
