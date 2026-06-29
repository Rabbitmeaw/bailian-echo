---
name: bailian-echo
metadata:
  version: "1.1.0"
  requires:
    - Python 3.8+ / openpyxl
    - 至少一个 ASR 后端:
      - bailian-cli (>= 1.4.0, 已鉴权) 或
      - @volcengine/ark-cli (已鉴权)
description: >-
  Batch video/audio speech-to-text with dual backend: Aliyun Bailian fun-asr + Volcengine Ark doubao-seed-asr.
  Processes a folder of video files and outputs structured Excel (.xlsx) or CSV.
  Handles file upload, ASR, timing, error tracking — end to end.
  Trigger when user says: "批量转写", "语音转文字", "ASR", "视频转文字",
  "字幕提取", "转写这个文件夹", "transcribe videos", "batch ASR",
  or provides a folder path with video files and mentions transcription.
  Backends: 百炼 fun-asr (bl) and 火山方舟 doubao-seed-asr (ark).
  Treat both backends equally. If user doesn't specify, ask which one.
---

# 批量视频 ASR 转写 (bailian-echo)

双后端批量语音转文字工具，平权对待：
- **bl**：阿里云百炼 `fun-asr`
- **ark**：火山引擎方舟 `doubao-seed-asr`

遍历视频文件夹，逐文件转写，输出结构化 Excel / CSV。

## 后端选择

Agent 按以下规则确定后端：

| 用户说法 | → 后端 |
|----------|--------|
| "百炼"、"bailian"、"bl" | `bl` |
| "火山"、"ark"、"arkcli"、"方舟"、"豆包" | `ark` |
| 未指定 | **主动询问用户选择哪个**（列出两个选项，不默认偏袒） |

---

## Phase 0：环境自举（Agent 必须逐项完成，失败则停止并告知用户）

**原则**：Agent 应主动在本机终端内完成所有安装和配置，仅在无权限或环境无法自动化时，向用户说明原因并请其配合。

### 0.1 Node.js

```bash
node -v
```

要求 **≥ 22.12.0**。未安装或版本不足：Agent 自行安装或升级 Node（macOS: `brew install node`；Linux: 使用 nvm 安装）。

### 0.2 npm

```bash
npm -v
```

未安装或不可用：Agent 安装或修复 npm。**禁止**用 pnpm / yarn 安装 bailian-cli。

### 0.3 后端 CLI

根据用户选择，安装对应的 CLI：

```bash
# bl 后端
bl --version || npm install -g bailian-cli

# ark 后端
arkcli --version || npm install -g @volcengine/ark-cli@latest
```

校验：
```bash
<cli> --version
which <cli>        # Windows: where <cli>
```

### 0.4 后端 Skills

```bash
# bl 后端
npx skills add modelstudioai/cli --all -g

# ark 后端
arkcli +connect
```

### 0.5 鉴权

ASR 转写的本质依赖是 **API Key**。两个后端的鉴权路径独立。

#### bl 后端鉴权

读取优先级：`--api-key` > `DASHSCOPE_API_KEY` > `~/.bailian/config.json`

| Step | 操作 |
|------|------|
| 1. 检查 | `bl auth status --output json` → `api_key.configured: true` 则跳过 |
| 2. 浏览器 | `bl auth login --console`（30s 超时 → Step 3） |
| 3. API Key | 引导用户从 [百炼控制台](https://bailian.console.aliyun.com/cn-beijing/?tab=app#/api-key) 获取 Key → `bl auth login --api-key <Key>` |
| 4. 校验 | `bl auth status --output json` |

#### ark 后端鉴权

读取优先级：`--api-key` > `ARK_API_KEY` > 本地 credential 文件

| Step | 操作 |
|------|------|
| 1. 检查 | `arkcli auth status --format json` → 已登录则跳过 |
| 2. 浏览器 | `arkcli auth login`（30s 超时 → Step 3） |
| 3. API Key | 引导用户从 [火山方舟控制台](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) 获取 Key → 告知用户设置 `ARK_API_KEY` 环境变量 |
| 4. 校验 | `arkcli auth status --format json` |

> **禁止**把 Key 写进回复正文、日志或文件。向用户汇报时仅展示 `masked` 字段。

#### 进阶提示（Agent 完成鉴权后告知用户，非强制）

如果用户希望凭证不落盘，可改为环境变量：
```bash
# bl
export DASHSCOPE_API_KEY="<Key>"
# ark
export ARK_API_KEY="<Key>"
```
写入 `~/.zshrc` 持久化。设置后 CLI 优先读环境变量。

### 0.6 Python openpyxl

```bash
python3 -c "import openpyxl; print(openpyxl.__version__)"
```

未安装：
```bash
pip3 install openpyxl
```

### 0.7 最小功能验证（全部通过后方可进入 Phase 1）

```bash
bl auth status --output json | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['authenticated'] and d['api_key']['configured'], 'AUTH FAILED'"
python3 -c "import openpyxl"
echo "ALL CHECKS PASSED"
```

验证项：鉴权通过 + API Key 已配置 + openpyxl 可导入。

---

## Phase 1：确定参数 & 执行转写

环境就绪后，从用户输入中提取参数：

| 参数 | 来源 | 默认值 |
|------|------|--------|
| `--folder` | 用户提供的文件夹路径 | **必填** |
| `--backend` | 用户指定，未指定则询问 | **必问** |
| `--format` | 用户明确说 "csv" → csv，否则 | xlsx |
| `--output` | 用户指定的输出路径 | 自动生成（源文件夹内） |

若用户只说「转写」但没给路径，主动询问文件夹路径。
若用户提供的是单个文件，同样运行脚本。

执行：

```bash
python3 <skill_dir>/assets/batch_asr.py \
  --folder "<用户提供的文件夹路径>" \
  --backend <bl|ark> \
  --format <xlsx|csv> \
  [--output "<用户指定路径>"]
```

Agent 应在终端中执行此命令，等待完成，检查退出码。

---

## Phase 2：汇报结果

| 汇报项 | 说明 |
|--------|------|
| 成功 / 失败计数 | 总数、成功数、失败数 |
| 总耗时 | 含上传 + 转写 |
| 输出文件完整路径 | 用户可直接打开 |
| 失败文件清单 | 如有：文件名 + 错误原因 |

**不要**逐字复制所有转写文本到对话中（可能非常长）。给出概要 + 文件路径即可。

---

## 输出规范

| 项目 | 规则 |
|------|------|
| 文件名 | `ASR转写结果_{文件夹名}_{时间戳}.xlsx` (或 `.csv`) |
| 位置 | 默认在源文件夹中（除非 `--output` 指定） |

### 8 列输出

| 列名 | 来源 |
|------|------|
| 文件名 | 原始文件名 |
| 文件路径 | 绝对路径 |
| 时长(秒) | ASR 返回的 `original_duration_in_milliseconds` |
| 文件大小(MB) | os.stat |
| 完整文本 | fun-asr 转写 |
| 处理状态 | 成功 / 失败 |
| 处理耗时(秒) | 计时 |
| 错误信息 | 失败时 |

Excel 样式：蓝底白字表头、冻结首行、自动筛选。

### 支持的视频格式

`.mp4` `.mov` `.mkv` `.avi` `.webm` `.flv` `.wmv` `.m4v` `.ts` `.mts` `.m2ts` `.3gp` `.ogv` `.mpg` `.mpeg` `.rmvb` `.asf` `.vob`

仅处理文件夹**顶级**文件（不递归子目录）。

---

## 脚本路径

```
assets/batch_asr.py
```

Agent 应使用 skill 目录下的绝对路径调用。
