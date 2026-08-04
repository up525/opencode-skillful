---
name: glm-vision
description: 为 DeepSeek 等纯文本模型补充图片理解能力。用户提供截图、照片、UI、报错界面、技术图、图表或多张待对比图片，且任务依赖画面细节时，调用 GLM-4.6V-Flash 获取视觉观察，再由主模型继续推理、检查代码并完成任务。
license: MIT
compatibility: opencode
metadata:
  provider: zhipu
  model: glm-4.6v-flash
---

# GLM Vision Bridge

将 GLM-4.6V-Flash 作为 DeepSeek 等纯文本主模型的“眼睛”。主模型继续负责规划、推理、代码修改和最终回答；GLM 只负责读取图片并返回视觉观察。

## 何时使用

当用户任务依赖以下内容时，必须先使用视觉能力，不能凭文件名或上下文猜图：

- 截图中的文字、代码、日志或报错
- UI 布局、样式、交互状态或多图差异
- 架构图、流程图、UML、ER 图、电路图
- 图表、仪表盘、照片或其他画面细节

纯文本任务、图片内容与答案无关、或已有可靠文字转录时，不要调用。

## 后端选择

### 优先：官方视觉 MCP

若工具列表中存在智谱视觉 MCP，选择最具体的工具：

- OCR、代码、日志：`extract_text_from_screenshot`
- 报错界面：`diagnose_error_screenshot`
- 架构图和流程图：`understand_technical_diagram`
- 图表和仪表盘：`analyze_data_visualization`
- UI 还原：`ui_to_artifact`
- UI 对比：`ui_diff_check`
- 其他图片：`image_analysis`

### 回退：直接调用 GLM-4.6V-Flash API

仅在没有视觉 MCP、但允许执行 Shell/Python 时使用。环境变量优先读取 `ZHIPU_API_KEY`，兼容 `Z_AI_API_KEY`。不要在命令、日志或最终回答中输出 API Key。

把提示词作为第一个参数，后面传一张或多张本地图片路径或 HTTP(S) 图片 URL：

```bash
python3 - '只描述完成用户任务所需的可见事实，不要猜测。' /absolute/path/image.png <<'PY'
import base64
import json
import os
import pathlib
import sys
import urllib.request

prompt, *images = sys.argv[1:]
key = os.getenv('ZHIPU_API_KEY') or os.getenv('Z_AI_API_KEY')
if not key:
    raise SystemExit('缺少 ZHIPU_API_KEY 或 Z_AI_API_KEY')
if not images:
    raise SystemExit('至少需要一张图片')

content = []
for source in images:
    if source.startswith(('http://', 'https://')):
        value = source
    else:
        path = pathlib.Path(source).expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f'图片不存在：{path}')
        value = base64.b64encode(path.read_bytes()).decode('ascii')
    content.append({'type': 'image_url', 'image_url': {'url': value}})

content.append({'type': 'text', 'text': prompt})
payload = {
    'model': 'glm-4.6v-flash',
    'messages': [{'role': 'user', 'content': content}],
    'thinking': {'type': 'enabled'},
    'stream': False,
}
request = urllib.request.Request(
    'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
    method='POST',
    headers={
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
)
with urllib.request.urlopen(request, timeout=120) as response:
    result = json.loads(response.read().decode('utf-8'))
print(result['choices'][0]['message']['content'])
PY
```

多图对比时，把所有图片路径依次放在命令末尾，并在提示中明确每张图的顺序和角色。

## 视觉提示要求

### OCR 和报错

先逐字提取可见文字，尽量保留换行；单独标记不确定字符。报错诊断应先提取错误类型、文件名、行号、状态码和界面状态，再结合真实代码、日志或配置验证，不能只凭截图修改代码。

### UI

提取页面层级、布局、间距、尺寸、字体、颜色、组件、交互状态和响应式线索。描述必须可落实到代码，避免“比较现代”“看起来简洁”等空泛表述。

### 技术图

识别实体、标签、箭头方向、数据流、控制流、接口和约束。看不清或图中没有的连接必须标记为未知。

### 图表

读取标题、坐标轴、单位、图例、趋势、异常和能确认的数值。无法辨认时只给范围或趋势，不得伪造精确数字。

### 图片对比

按固定区域或坐标顺序列出确认差异和不确定差异，区分内容变化与渲染误差。

## 结果处理

- GLM 输出只是视觉观察，由主模型结合用户问题和真实上下文继续推理。
- 命令、标识符、数字、文件名和行号等 OCR 敏感信息应二次核对。
- 涉及代码修改时必须检查真实仓库，不能仅根据截图猜代码。
- 图片模糊、裁切、遮挡或分辨率不足时明确说明不确定性。
- 最终回答使用用户当前语言，不必暴露内部视觉调用过程。

## 隐私

调用 MCP 或 API 都会把图片发送给外部视觉服务。遇到 API Key、密码、Cookie、私人聊天、身份资料、医疗或财务记录等敏感内容时，优先裁剪或打码；未经用户明确选择，不要上传敏感截图。
