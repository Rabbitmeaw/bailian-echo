# bailian-echo

[**English**](README.md) | [**中文**](README.zh.md)

> Batch speech-to-text for videos — one folder in, one Excel out.

**bailian-echo** is a Claude Code / Codex skill that turns a folder of videos into a formatted Excel report using Aliyun Bailian's [fun-asr](https://help.aliyun.com/zh/model-studio/asr-model). Handles upload, transcription, timing, and error tracking end-to-end.

```
📁 ~/Videos/interviews/
   ├── interview_01.mp4
   ├── interview_02.mov
   └── panel.mp4
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

## Quick Start

### Prerequisites

| Dependency | Install |
|------------|---------|
| Node.js ≥ 22.12 | `brew install node` |
| Bailian CLI | `npm install -g bailian-cli` |
| Bailian Skills | `npx skills add modelstudioai/cli --all -g` |
| Python openpyxl | `pip3 install openpyxl` |

### Install

```bash
npx skills add Rabbitmeaw/bailian-echo --all -g
```

### Authenticate

The skill agent guides you through auth on first use. In short:

```bash
# Desktop — one browser click (auto-creates API key)
bl auth login --console

# Or with API key from https://bailian.console.aliyun.com
bl auth login --api-key sk-xxxxx

# Privacy: env var (no plaintext on disk)
export DASHSCOPE_API_KEY="sk-xxxxx"   # ~/.zshrc
```

## Usage

### Batch Mode (folder → Excel/CSV)

```
Transcribe all videos in ~/Downloads/meetings to Excel
帮我把 ./视频素材 里的视频全部转成文字
批量转写 ~/Desktop/录屏 输出 csv，5 并发
```

```bash
python3 batch_asr.py --folder ~/Videos/meetings
python3 batch_asr.py --folder ~/Videos/meetings --format csv
python3 batch_asr.py --folder ~/Videos/meetings --concurrency 5
```

### Single-File Mode (video → plain text / timed text)

```bash
# Plain full text → stdout
python3 batch_asr.py --file meeting.mp4

# Sentence-level timestamps → stdout
python3 batch_asr.py --file meeting.mp4 --timed

# Save to file
python3 batch_asr.py --file meeting.mp4 --timed -o transcript.txt
```

## Output

9 columns for batch mode:

| Column | Source |
|--------|--------|
| Filename | Original filename |
| File Path | Absolute path |
| Duration (s) | ASR JSON `original_duration_in_milliseconds` |
| File Size (MB) | os.stat |
| Full Text | fun-asr transcription |
| Timed Text | `[MM:SS.ms→MM:SS.ms] sentence text` per line |
| Status | Success / Fail |
| Elapsed (s) | Per-file timing |
| Error | Failure details |

Excel: blue header, frozen first row, auto-filter.

Results saved incrementally — each file written to disk as it completes. Interruption-safe.

Output: `ASR转写结果_{folder}_{timestamp}.xlsx` (or `.csv`) in the source folder.

## Supported Formats

`.mp4` `.mov` `.mkv` `.avi` `.webm` `.flv` `.wmv` `.m4v` `.ts` `.mts` `.m2ts` `.3gp` `.ogv` `.mpg` `.mpeg` `.rmvb` `.asf` `.vob`

Top-level files only.

## How It Works

```
Video files  →  bl CLI auto-uploads to temp OSS (48h expiry)
  →  fun-asr transcribes  →  Excel/CSV written to source folder
```

No OSS account needed. No manual upload. No ffmpeg. One dependency: `bl`.

## FAQ

**Q: Do I need to extract audio first?**
A: No. `bl speech recognize` accepts video files directly.

**Q: Can I get subtitles with timestamps?**
A: Yes. The **Timed Text** column includes sentence-level `[MM:SS.ms→MM:SS.ms]` timestamps. For single files, use `--timed` to print timestamped text directly.

**Q: How fast is it?**
A: Default 3 concurrent files. With `--concurrency N` you can speed up large batches.

**Q: What if the process is interrupted mid-batch?**
A: Results are saved after each file. Completed files are preserved.

**Q: Is there a cost?**
A: fun-asr has a free tier. Paid beyond that → [pricing](https://help.aliyun.com/zh/model-studio/model-pricing).

**Q: What if a file has no speech?**
A: Marked "失败". Other files continue.

**Q: Windows?**
A: Yes. Python `pathlib`, `npm install -g bailian-cli`.

## License

MIT
