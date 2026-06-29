# bailian-echo

> Batch speech-to-text for videos — zero config, one folder, structured Excel.

**bailian-echo** is a Claude Code / Codex skill that turns a folder of videos into a formatted Excel report using Aliyun Bailian's [fun-asr](https://help.aliyun.com/zh/model-studio/asr-model) model. Handles upload, transcription, timing, and error tracking end-to-end.

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
| Bailian CLI | `npm install -g bailian-cli` |
| Bailian Skills | `npx skills add modelstudioai/cli --all -g` |
| ffprobe | `brew install ffmpeg` |
| Python openpyxl | `pip3 install openpyxl` |

### Install the Skill

```bash
npx skills add Rabbitmeaw/bailian-echo --all -g
```

### Authenticate

The skill agent will guide you through authentication on first use:

```bash
# Desktop — one browser click
bl auth login --console

# Or with API key from https://bailian.console.aliyun.com
bl auth login --api-key sk-xxxxx

# Privacy tip: use env var (no plaintext on disk)
export DASHSCOPE_API_KEY="sk-xxxxx"   # add to ~/.zshrc
```

### Use

In Claude Code or Codex, just talk naturally:

```
Transcribe all videos in ~/Downloads/meetings to Excel
```

## Output

An Excel (`.xlsx`) or CSV file is generated in the source folder:

| Column | Source |
|--------|--------|
| Filename | Original filename |
| File Path | Absolute path |
| Duration (s) | ffprobe |
| File Size (MB) | os.stat |
| Full Text | fun-asr transcription |
| Status | Success / Fail |
| Elapsed (s) | Per-file timing |
| Error | Failure details |

### Output Naming

```
ASR转写结果_{folder_name}_{YYYYMMDD_HHMMSS}.xlsx
```

## Supported Video Formats

`.mp4` `.mov` `.mkv` `.avi` `.webm` `.flv` `.wmv` `.m4v` `.ts` `.mts` `.m2ts` `.3gp` `.ogv` `.mpg` `.mpeg` `.rmvb` `.asf` `.vob`

Non-recursive — processes only top-level files in the given folder.

## Authentication Methods

The agent tries these in order:

| Priority | Method | User Effort |
|----------|--------|-------------|
| 1 | `bl auth login --console` | Click once in browser |
| 2 | `bl auth login --api-key` | Copy-paste a key |
| 3 | `DASHSCOPE_API_KEY` env var | Edit shell config (optional, for privacy) |

## How It Works

```
Your video files
    │
    ▼
bl CLI auto-uploads to DashScope temp OSS (48h expiry)
    │
    ▼
fun-asr model transcribes audio
    │
    ▼
Results collected → Excel/CSV written to source folder
```

No OSS account needed. No manual file upload. Temp files auto-expire in 48 hours.

## FAQ

**Q: Do I need ffmpeg to extract audio?**
A: No. `bl speech recognize` accepts video files directly — it handles audio extraction internally. No quality loss, no extra cost.

**Q: Is there a cost?**
A: fun-asr has a free tier. Beyond that, pricing is per audio-hour. See [Bailian pricing](https://help.aliyun.com/zh/model-studio/model-pricing).

**Q: Can I process subfolders?**
A: Currently only top-level files in the specified folder. For nested folders, run the skill once per folder.

**Q: What if a file has no speech?**
A: The script marks it as "失败" (failed) with the reason "ASR 返回了空结果". Other files continue.

**Q: Does it work on Windows?**
A: Yes. Uses Python `pathlib` and standard subprocess calls. ffmpeg via `winget install ffmpeg`.

## License

MIT
