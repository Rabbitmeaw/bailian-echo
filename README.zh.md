# bailian-echo（百炼·回声）

[**English**](README.md) | [**中文**](README.zh.md)

> 批量视频语音转文字 — 一个文件夹进，一份 Excel 出。

**bailian-echo** 是一个 Claude Code / Codex Skill，基于阿里云百炼 [fun-asr](https://help.aliyun.com/zh/model-studio/asr-model)，将视频文件夹批量转为结构化文字报表。上传、转写、计时、异常处理全链路自动化。

```
📁 ~/Videos/会议录屏/
   ├── 周会_20260701.mp4
   ├── 面试_候选人A.mov
   └── 项目复盘.mkv
          │
          ▼  "帮我把这个文件夹转成文字"
          │
   📄 ASR转写结果_会议录屏_20260701_143000.xlsx
      ┌────────────┬────────┬──────┬──────────────┐
      │ 文件名     │ 时长   │ 大小 │ 完整文本     │
      ├────────────┼────────┼──────┼──────────────┤
      │ 周会_...   │ 146s   │ 11MB │ "今天我们讨论 │
      │            │        │      │  了Q3的..."  │
      └────────────┴────────┴──────┴──────────────┘
```

## 快速开始

### 前置依赖

| 依赖 | 安装 |
|------|------|
| Node.js ≥ 22.12 | `brew install node` |
| 百炼 CLI | `npm install -g bailian-cli` |
| 百炼 Skills | `npx skills add modelstudioai/cli --all -g` |
| Python openpyxl | `pip3 install openpyxl` |

### 安装

```bash
npx skills add Rabbitmeaw/bailian-echo --all -g
```

### 鉴权

首次使用时 Skill Agent 自动引导鉴权：

```bash
# 桌面 — 浏览器一键登录（自动创建 API Key）
bl auth login --console

# 或从 https://bailian.console.aliyun.com 获取 Key
bl auth login --api-key sk-xxxxx

# 隐私建议：环境变量（不落盘）
export DASHSCOPE_API_KEY="sk-xxxxx"   # ~/.zshrc
```

百炼 `--console` 一步完成「登录 + 自动创建 API Key」，无需单独去控制台手动操作。

### 使用

#### 批量模式（文件夹 → Excel/CSV）

```
帮我把 ~/Downloads/会议录屏 里的视频全部转成文字 Excel
批量提取 ./视频素材 转文字，输出 csv，5 并发
transcribe all videos in /data/interviews to xlsx
```

```bash
python3 batch_asr.py --folder ~/Videos/会议录屏
python3 batch_asr.py --folder ~/Videos/会议录屏 --format csv
python3 batch_asr.py --folder ~/Videos/会议录屏 --concurrency 5
```

#### 单文件模式（视频 → 纯文本 / 带时间码）

```bash
# 纯文本输出到终端
python3 batch_asr.py --file 周会.mp4

# 带句级时间码输出
python3 batch_asr.py --file 周会.mp4 --timed

# 保存到文件
python3 batch_asr.py --file 周会.mp4 --timed -o 字幕.txt
```

## 输出格式

批量模式输出 9 列：

| 列名 | 来源 |
|------|------|
| 文件名 | 原始文件名 |
| 文件路径 | 绝对路径 |
| 时长(秒) | ASR JSON |
| 文件大小(MB) | 文件大小 |
| 完整文本 | fun-asr 转写全文 |
| 带时间码文本 | `[MM:SS.ms→MM:SS.ms] 句子` 逐句时间戳 |
| 处理状态 | 成功 / 失败 |
| 处理耗时(秒) | 单文件耗时 |
| 错误信息 | 失败原因 |

Excel 输出：蓝底白字表头、冻结首行、自动筛选。

每完成一个文件立即落盘，中途中断不丢已完成数据。

文件命名：`ASR转写结果_{文件夹名}_{时间戳}.xlsx`（或 `.csv`），默认在源文件夹中。

## 支持的格式

`.mp4` `.mov` `.mkv` `.avi` `.webm` `.flv` `.wmv` `.m4v` `.ts` `.mts` `.m2ts` `.3gp` `.ogv` `.mpg` `.mpeg` `.rmvb` `.asf` `.vob`

仅处理文件夹顶层文件。

## 工作原理

```
视频文件 → bl CLI 自动上传到临时 OSS（48h 过期）
  → fun-asr 转写 → Excel/CSV 写入源文件夹
```

无需 OSS 账号、无需手动上传、无需 ffmpeg。唯一依赖：`bl`。

## 常见问题

**Q: 需要先提取音频吗？**
A: 不需要。直接喂视频，内部自动处理音轨。

**Q: 能输出带时间码的字幕吗？**
A: 可以。批量 Excel 中「带时间码文本」列包含逐句 `[MM:SS.ms→MM:SS.ms]`。单文件用 `--timed` 直接输出。

**Q: 处理速度如何？**
A: 默认 3 并发。`--concurrency N` 可加速大批量处理。

**Q: 中途中断会丢数据吗？**
A: 不会。每完成一个文件立即写入 Excel/CSV，已完成部分保留。

**Q: 如何收费？**
A: fun-asr 有免费额度，超出按音频时长计费 → [定价](https://help.aliyun.com/zh/model-studio/model-pricing)。

**Q: 视频没有语音怎么办？**
A: 标记为"失败"，其余文件继续处理。

**Q: Windows 能用吗？**
A: 可以。Python `pathlib` 跨平台。

## 许可

MIT
