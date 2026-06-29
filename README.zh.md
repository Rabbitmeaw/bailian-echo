# bailian-echo（百炼·回声）

> 批量视频语音转文字 — 双后端（百炼 + 火山方舟），一个文件夹进，一份 Excel 出。

**bailian-echo** 是一个 Claude Code / Codex Skill，支持阿里云百炼 [fun-asr](https://help.aliyun.com/zh/model-studio/asr-model) 与火山方舟 [doubao-seed-asr](https://www.volcengine.com/docs/6561/1354868) 双后端。将视频文件夹批量转为结构化文字报表，上传、转写、计时、异常处理全链路自动化。

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

| 依赖 | 安装命令 |
|------|----------|
| Node.js ≥ 22.12 | `brew install node` |
| Python openpyxl | `pip3 install openpyxl` |
| **百炼 CLI** (bl) | `npm install -g bailian-cli` |
| 百炼 Skills | `npx skills add modelstudioai/cli --all -g` |
| **火山方舟 CLI** (arkcli) | `npm install -g @volcengine/ark-cli@latest` |
| 方舟 Skills | `arkcli +connect` |

### 安装 Skill

```bash
npx skills add Rabbitmeaw/bailian-echo --all -g
```

### 鉴权

首次使用时，Skill 的 AI Agent 会自动引导你完成鉴权：

```bash
# 桌面环境（推荐，一键搞定）
bl auth login --console

# 或在 https://bailian.console.aliyun.com 获取 Key 后
bl auth login --api-key sk-xxxxx
```

### 使用

安装后在 Claude Code / Codex 中用自然语言触发：

```
帮我把 ~/Downloads/会议录屏 里的视频全部转成文字 Excel
```

```
批量提取 ./视频素材 里的语音转文字，输出 csv
```

```
transcribe all videos in /data/interviews to xlsx
```

## 输出格式

在源文件夹生成 Excel (`.xlsx`) 或 CSV 文件，包含 8 列：

| 列名 | 来源 |
|------|------|
| 文件名 | 原始文件名 |
| 文件路径 | 完整绝对路径 |
| 时长(秒) | ASR JSON |
| 文件大小(MB) | 文件大小 |
| 完整文本 | ASR 转写全文 |
| 处理状态 | 成功 / 失败 |
| 处理耗时(秒) | 单文件处理耗时 |
| 错误信息 | 失败时的错误详情 |

Excel 输出带有蓝底白字表头、冻结首行、自动筛选。

### 文件命名

```
ASR转写结果_{文件夹名}_{后端}_{时间戳}.xlsx
```

## 支持的视频格式

`.mp4` `.mov` `.mkv` `.avi` `.webm` `.flv` `.wmv` `.m4v` `.ts` `.mts` `.m2ts` `.3gp` `.ogv` `.mpg` `.mpeg` `.rmvb` `.asf` `.vob`

仅处理文件夹顶层文件，不递归子目录。

## 鉴权方式对比

Skill Agent 会按以下策略引导用户完成鉴权：

| 优先级 | 方式 | 用户体验 |
|--------|------|----------|
| 1 | `bl auth login --console` | 浏览器点一下确认 |
| 2 | `bl auth login --api-key` | 复制粘贴一次 Key |
| 3 | `DASHSCOPE_API_KEY` 环境变量 | 编辑 shell 配置（适合在意隐私的用户） |

### 环境变量（进阶）

希望凭证不落盘：

```bash
# 写入 ~/.zshrc（持久化）
export DASHSCOPE_API_KEY="sk-xxxxx"

# 或仅当前终端会话
export DASHSCOPE_API_KEY="sk-xxxxx"
```

`bl` CLI 优先读取环境变量，此时可安全删除 `~/.bailian/config.json` 中的 `api_key` 字段。

## 工作原理

```
你的视频文件
    │
    ▼
bl CLI 自动上传到 DashScope 临时 OSS（48h 后自动过期）
    │
    ▼
fun-asr 模型对音频进行语音识别
    │
    ▼
汇总结果 → 写入 Excel/CSV → 输出到源文件夹
```

无需自己开通 OSS，无需手动上传文件，临时文件 48 小时后自动清理。

## 常见问题

**Q: 需要先提取音频吗？**
A: 不需要。`bl speech recognize` 直接接受视频文件，内部自动处理音轨，无质量损失，费用与纯音频相同。

**Q: 如何收费？**
A: 两个后端均有免费额度，超出后按音频时长计费。详见 [百炼模型定价](https://help.aliyun.com/zh/model-studio/model-pricing)。

**Q: 支持子文件夹吗？**
A: 当前仅处理指定文件夹的顶层文件。嵌套文件夹请逐个运行。

**Q: 视频里没有语音怎么办？**
A: 标记为"失败"，错误信息为「ASR 返回了空结果」。其余文件不受影响，继续处理。

**Q: Windows 能用吗？**
A: 可以。Python 脚本使用跨平台的 `pathlib`，无需额外安装多媒体工具。

## 许可

MIT
