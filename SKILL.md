---
name: bailian-echo
metadata:
  version: "1.0.0"
  requires:
    - Python 3.8+ / openpyxl
    - bailian-cli (>= 1.4.0, 已鉴权)
description: >-
  Batch video/audio speech-to-text using Aliyun Bailian fun-asr.
  Processes a folder of video files and outputs structured Excel (.xlsx) or CSV.
  Handles file upload, ASR, timing, error tracking — end to end.
  Trigger when user says: "批量转写", "语音转文字", "ASR", "视频转文字",
  "字幕提取", "转写这个文件夹", "transcribe videos", "batch ASR",
  or provides a folder path with video files and mentions transcription.
---

# 批量视频 ASR 转写 (bailian-echo)

基于阿里云百炼 CLI `bl speech recognize` (fun-asr)，将视频文件夹批量转写为结构化 Excel / CSV。

---

## Phase 0：环境自举

Agent 主动在本机终端内完成所有安装和配置，仅在无权限时向用户说明。

### 0.1 Node.js

```bash
node -v   # ≥ 22.12.0
```

未安装或版本不足：Agent 自行安装（macOS: `brew install node`；Linux: nvm）。

### 0.2 npm

```bash
npm -v
```

**禁止**用 pnpm / yarn 安装 bailian-cli。

### 0.3 百炼 CLI

```bash
bl --version || npm install -g bailian-cli
which bl                     # Windows: where bl
```

### 0.4 百炼 Skills

```bash
npx skills add modelstudioai/cli --all -g
```

### 0.5 鉴权

API Key 读取优先级：`--api-key` > `DASHSCOPE_API_KEY` > `~/.bailian/config.json`

**Step 1 — 检查：**

```bash
bl auth status --output json
```
`api_key.configured: true` → 跳过鉴权。

**Step 2 — 浏览器登录（桌面环境，首选）：**

```bash
bl auth login --console
```
拉起浏览器 → 登录阿里云 → 自动写入 config。30s 超时 → Step 3。

百炼 `--console` 一键完成「登录 + 自动创建 API Key」，无需单独去控制台。

**Step 3 — API Key（无浏览器 / 超时回退）：**

1. 引导用户从 [百炼控制台](https://bailian.console.aliyun.com/cn-beijing/?tab=app#/api-key) 获取 API Key
2. Agent 执行：`bl auth login --api-key <Key>`（**禁止**把 Key 写入回复正文）

**Step 4 — 校验：**

```bash
bl auth status --output json   # api_key.configured: true
```

**进阶提示**（鉴权完成后告知，非强制）：

```bash
export DASHSCOPE_API_KEY="<Key>"   # 写入 ~/.zshrc，不落盘到 config.json
```

### 0.6 Python openpyxl

```bash
pip3 install openpyxl
```

### 0.7 全量验证

```bash
bl auth status --output json | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['authenticated'] and d['api_key']['configured']"
python3 -c "import openpyxl"
echo "ALL CHECKS PASSED"
```

---

## Phase 1：执行转写

| 参数 | 来源 | 默认值 |
|------|------|--------|
| `--folder` | 用户提供的文件夹路径 | **必填** |
| `--format` | 用户说 "csv" → csv | xlsx |
| `--output` | 用户指定 | 源文件夹内自动命名 |
| `--concurrency` | 用户说 "并行"/"加速"/"--concurrency N" | 3 |

```bash
python3 <skill_dir>/assets/batch_asr.py \
  --folder "<路径>" \
  --format <xlsx|csv> \
  [--output "<路径>"] \
  [--concurrency <N>]
```

---

## Phase 2：汇报

- 成功/失败计数 + 总耗时 + 输出文件路径
- **不要**逐字复制转写文本（可能很长），给出摘要 + 路径即可

---

## 输出

| 列名 | 来源 |
|------|------|
| 文件名 | 原始文件名 |
| 文件路径 | 绝对路径 |
| 时长(秒) | ASR JSON `original_duration_in_milliseconds` |
| 文件大小(MB) | os.stat |
| 完整文本 | fun-asr 转写全文 |
| 带时间码文本 | 句级时间戳 `[MM:SS.ms→MM:SS.ms] 文本` |
| 处理状态 | 成功 / 失败 |
| 处理耗时(秒) | 计时 |
| 错误信息 | 失败时 |

Excel 输出：蓝底白字表头、冻结首行、自动筛选。

文件命名：`ASR转写结果_{文件夹名}_{时间戳}.xlsx`（或 `.csv`），默认在源文件夹中。

### 支持格式

`.mp4` `.mov` `.mkv` `.avi` `.webm` `.flv` `.wmv` `.m4v` `.ts` `.mts` `.m2ts` `.3gp` `.ogv` `.mpg` `.mpeg` `.rmvb` `.asf` `.vob`

仅处理文件夹顶级文件。

## 脚本路径

```
assets/batch_asr.py
```
