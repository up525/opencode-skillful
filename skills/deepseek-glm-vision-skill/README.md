# DeepSeek + GLM 免费视觉 Skill

这个包用于给 OpenCode 中的 DeepSeek 等纯文本模型补充视觉理解能力。

## 工作方式

- **DeepSeek**：负责规划、推理、读取仓库、修改代码和最终回答。
- **GLM-4.6V-Flash**：负责看截图、照片、UI、技术图和图表。
- **Skill**：告诉 Agent 什么时候调用视觉，以及如何处理视觉结果。
- **可选官方 MCP**：在 OpenCode 中暴露 OCR、报错诊断、UI 对比等专业视觉工具。

它不会修改 DeepSeek 模型本身，也不会让 DeepSeek API 原生支持图片，而是在 Agent 运行时增加一个“视觉工具”。

## 两种后端的区别

### A. 直连免费 GLM-4.6V-Flash API

自带的 Python 脚本明确使用：

```text
glm-4.6v-flash
```

只需要普通智谱开放平台 API Key，不依赖第三方 Python 包。这是希望固定使用免费模型时更稳妥的方式。

### B. 智谱官方视觉 MCP

官方 MCP 集成更完整，提供截图 OCR、报错诊断、架构图分析、图表分析、UI 复刻、UI 对比、通用图片和视频理解等工具，但官方文档将它定位为 GLM Coding Plan 用户的本地 MCP。它是否消耗套餐额度，应以你的 Key 类型和控制台为准，不要默认它等同于免费 Flash API。

Skill 会优先使用 MCP；MCP 不存在时退回直连免费 API 脚本。

## 安装

克隆仓库后进入本目录：

```bash
git clone https://github.com/up525/opencode-skillful.git
cd opencode-skillful/skills/deepseek-glm-vision-skill
./install-global.sh
```

也可以手动复制：

```bash
mkdir -p ~/.config/opencode/skills
cp -R .opencode/skills/glm-vision ~/.config/opencode/skills/
```

安装位置：

```text
~/.config/opencode/skills/glm-vision/SKILL.md
```

OpenCode 也支持项目级位置：

```text
.opencode/skills/glm-vision/SKILL.md
```

## 配置免费 API Key

在智谱开放平台注册并创建 API Key，然后通过环境变量配置，不要把 Key 提交到 Git：

```bash
export ZHIPU_API_KEY='你的智谱API Key'
```

macOS 使用 zsh 时可以持久化：

```bash
echo "export ZHIPU_API_KEY='你的智谱API Key'" >> ~/.zshrc
source ~/.zshrc
```

## 测试直连视觉能力

```bash
python3 ~/.config/opencode/skills/glm-vision/scripts/glm_vision.py \
  --image ./screenshot.png \
  --prompt '先逐字提取报错，再说明截图中可见的界面状态。'
```

对比两张图片：

```bash
python3 ~/.config/opencode/skills/glm-vision/scripts/glm_vision.py \
  --image ./target.png \
  --image ./actual.png \
  --prompt '对比两张 UI，按区域列出确认存在的差异，不要猜测。'
```

简单任务关闭思考模式，可以更快：

```bash
python3 ~/.config/opencode/skills/glm-vision/scripts/glm_vision.py \
  --image ./screenshot.png \
  --prompt '提取截图里的全部文字。' \
  --no-thinking
```

## 可选：配置官方视觉 MCP

把 `opencode.example.jsonc` 中的 `mcp` 配置合并到你的全局配置或项目配置中，并设置：

```bash
export Z_AI_API_KEY='你的智谱或 Coding Plan Key'
```

重启 OpenCode 后检查：

```bash
opencode mcp list
```

## 在 DeepSeek 中使用

保持主模型为 DeepSeek，然后直接下达任务，例如：

```text
读取这张报错截图，提取准确报错，检查仓库代码并修复根因。先使用 glm-vision skill。
```

```text
对比目标 UI 和当前 UI，修改前端使实现尽量匹配。修改代码前先使用 glm-vision。
```

如果图片是本地文件，最好在提示中给出绝对路径，方便回退脚本读取。

## 隐私提醒

两种后端都会把图片发送给智谱处理。上传前应裁剪或打码 API Key、密码、Cookie、私人聊天、账号资料、个人记录等敏感内容。

## 文件结构

```text
.opencode/skills/glm-vision/SKILL.md
.opencode/skills/glm-vision/scripts/glm_vision.py
opencode.example.jsonc
install-global.sh
README.md
LICENSE
```
