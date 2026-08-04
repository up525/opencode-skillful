---
name: glm-vision
description: 为 DeepSeek 等纯文本模型补充视觉理解能力。用户提供或引用截图、照片、UI 设计、报错界面、技术图、图表或多张待对比图片，且回答依赖画面细节时，调用 GLM-4.6V-Flash 获取视觉观察，再由主模型继续推理、读代码和完成任务。
license: MIT
compatibility: opencode
metadata:
  provider: zhipu
  model: glm-4.6v-flash
---

# GLM Vision Bridge

本 Skill 将 GLM-4.6V-Flash 作为 DeepSeek 的“眼睛”。DeepSeek 仍是主模型，负责规划、推理、代码修改和最终回答；GLM 只负责读取图片并返回视觉观察。

## 核心原则

不要凭空猜测图片内容。必须先调用视觉能力获取观察结果，再继续主任务。GLM 的输出属于工具观察，不应未经核验直接当成最终结论。

## 后端选择

### 1. 优先使用官方视觉 MCP

若当前工具列表中存在 `zai-mcp-server` 的工具，选择最具体的工具：

- `extract_text_from_screenshot`：截图 OCR、代码、日志、终端输出、文档文字。
- `diagnose_error_screenshot`：报错弹窗、堆栈、失败界面。
- `understand_technical_diagram`：架构图、流程图、UML、ER 图、电路图。
- `analyze_data_visualization`：图表、仪表盘、统计图。
- `ui_to_artifact`：UI 还原、设计规范提取、前端实现。
- `ui_diff_check`：两张 UI 截图差异检查。
- `image_analysis`：其他通用图片。

### 2. MCP 不可用时使用免费模型直连脚本

全局安装后的默认命令：

```bash
python3 ~/.config/opencode/skills/glm-vision/scripts/glm_vision.py \
  --image "/absolute/path/to/image.png" \
  --prompt "只描述完成用户任务所需的可见事实，不要猜测。"
```

如果 Skill 安装在项目的 `.opencode/skills/glm-vision/` 下，则从该目录调用 `scripts/glm_vision.py`。

## 不同任务的提示词

### 截图与 OCR

要求逐字转录可见文字；尽量保留换行；把不确定字符单独标记；明确区分“原文转录”和“解释”。

### 报错诊断

先提取准确报错、文件名、行号、状态码和界面状态，再给出可能原因。随后必须结合真实代码、日志或配置验证，不能只根据截图直接修改。

### UI 实现

要求输出页面层级、布局、间距、字号、颜色、组件、交互状态和响应式线索，重点提供可落地到代码的信息，而不是泛泛描述画面。

### 技术图

要求识别实体、标签、箭头、方向、数据流、控制流、接口和约束。看不清或图中没有的连接必须标注为未知。

### 图表与仪表盘

要求读取标题、坐标轴、单位、图例、近似数值、趋势和异常。标签无法辨认时，不得伪造精确数字。

### 图片对比

一次传入两张或多张图片，要求按位置列出确认差异与不确定差异，并保持位置描述一致。

## 结果处理

- 将 GLM 返回内容作为视觉观察，再由 DeepSeek 结合上下文完成答案。
- 命令、标识符、数字、文件名和行号等 OCR 敏感信息应尽量二次核对。
- 涉及代码修改时，必须检查真实仓库，不能只按截图猜代码。
- 最终回答使用用户语言。
- 图片模糊、裁切、遮挡或分辨率不足时，明确说明不确定性。

## 隐私与安全

直连脚本和官方 MCP 都会把图片发送给智谱服务。遇到 API Key、密码、Cookie、私人聊天、个人资料、医疗或财务记录等敏感内容时，优先裁剪或打码；未经用户明确选择，不要上传敏感截图。

## 环境变量

直连脚本优先读取 `ZHIPU_API_KEY`，也兼容 `Z_AI_API_KEY`，默认模型固定为 `glm-4.6v-flash`。
