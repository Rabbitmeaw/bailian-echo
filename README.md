# bailian-echo

> Batch speech-to-text for videos — dual backend (Bailian + Volcengine), one folder, structured Excel.

**bailian-echo** is a Claude Code / Codex skill that turns a folder of videos into a formatted Excel report using Aliyun Bailian's [fun-asr](https://help.aliyun.com/zh/model-studio/asr-model) or Volcengine Ark's [doubao-seed-asr](https://www.volcengine.com/docs/6561/1354868). Handles upload, transcription, timing, and error tracking end-to-end.

```
📁 ~/Videos/interviews/
   ├── interview_01.mp4
   ├── interview_02.mov
   └── panel_discussion.mkv
          │
          ▼  "transcribe this folder"
          │
   📄 ASR转写结果_interviews_20260701_143000.xlsx
      ┌──────────┬──────────┬──────┬─────────────┐
      │ Filename │ Duration │ Size │ Full Text   │
      ├──────────┼──────────┼──────┼─────────────┤
      │ int...   │ 146s     │ 11MB │ "In today's │
      │          │          │      │  episode..."│
      └──────────┴──────────┴──────┴─────────────┘
```

- [中文文档](README.zh.md)

## Quick Start

### Prerequisites

| Dependency | Install |
|------------|---------|
| Node.js ≥ 22.12 | `brew install node` |
| Python openpyxl | `pip3 install openpyxl` |
| **Bailian** (bl) | `npm install -g bailian-cli` |
| Bailian Skills | `npx skills add modelstudioai/cli --all -g` |
| **Volcengine** (ark) | `npm install -g @volcengine/ark-cli@latest` |
| Ark Skills | `arkcli +connect` |

> You only need **one** of the two CLI backends. Pick the one you have an account for.

### Install the Skill

```bash
npx skills add Rabbitmeaw/bailian-echo --all -g
```

### Authenticate

The skill agent guides you on first use. In short:

```bash
# Bailian (bl)
bl auth login --console                    # browser login
bl auth login --api-key sk-xxxxx           # or API key
export DASHSCOPE_API_KEY="sk-xxxxx"        # or env var

# Volcengine (ark)
arkcli auth login                          # browser login
export ARK_API_KEY="your-key"              # or env var
```

### Use

In Claude Code or Codex, specify the backend naturally:

```
Transcribe all videos in ~/Downloads/meetings to Excel
帮我把 ./视频素材 转成文字，用百炼                # use bl
帮我把 ./视频素材 转成文字，用火山引擎            # use ark
```

## Output

An Excel (`.xlsx`) or CSV file is generated in the source folder:

| Column | Source |
|--------|--------|
| Filename | Original filename |
| File Path | Absolute path |
| Duration (s) | ASR JSON |
| File Size (MB) | os.stat |
| Full Text | fun-asr transcription |
| Status | Success / Fail |
| Elapsed (s) | Per-file timing |
| Error | Failure details |

### Output Naming

```
ASR转写结果_{folder_name}_{backend}_{YYYYMMDD_HHMMSS}.xlsx
```

## Supported Video Formats

`.mp4` `.mov` `.mkv` `.avi` `.webm` `.flv` `.wmv` `.m4v` `.ts` `.mts` `.m2ts` `.3gp` `.ogv` `.mpg` `.mpeg` `.rmvb` `.asf` `.vob`

Non-recursive — processes only top-level files in the given folder.

## Backend Comparison

| | Bailian (bl) | Volcengine (ark) |
|---|---|---|
| Model | fun-asr | doubao-seed-asr |
| CLI | `bl` | `arkcli` |
| Auth env | `DASHSCOPE_API_KEY` | `ARK_API_KEY` |
| API Key URL | [bailian.console](https://bailian.console.aliyun.com/cn-beijing/?tab=app#/api-key) | [ark console](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) |
| File handling | Auto-upload to temp OSS | Direct multimodal input |

## How It Works

```
Your video files
    │
    ▼
CLI auto-uploads to cloud ASR service
    │
    ▼
ASR model transcribes audio track
    │
    ▼
Results collected → Excel/CSV written to source folder
```

## FAQ

**Q: Do I need to extract audio first?**
A: No. `bl speech recognize` accepts video files directly. Audio extraction is handled internally. No quality loss, no extra cost.

**Q: Is there a cost?**
A: Both backends have free tiers. Bailian fun-asr pricing → [here](https://help.aliyun.com/zh/model-studio/model-pricing). Volcengine doubao-seed-asr pricing → [here](https://www.volcengine.com/docs/6561/1816214).

**Q: Can I process subfolders?**
A: Currently only top-level files in the specified folder. For nested folders, run the skill once per folder.

**Q: What if a file has no speech?**
A: The script marks it as "失败" (failed) with the reason "ASR 返回了空结果". Other files continue.

**Q: Does it work on Windows?**
A: Yes. Uses Python `pathlib` and standard subprocess calls.

## License

MIT
