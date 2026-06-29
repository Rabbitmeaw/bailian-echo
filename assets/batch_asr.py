#!/usr/bin/env python3
"""
批量视频 ASR 转写工具
━━━━━━━━━━━━━━━━━━━━━━━━━━
基于阿里云百炼 CLI (bl speech recognize / fun-asr)，
遍历指定文件夹中的视频文件，逐一转写为文字，
最终输出 Excel (.xlsx) 或 CSV 文件。

用法:
    python3 batch_asr.py --folder /path/to/videos
    python3 batch_asr.py --folder /path/to/videos --format csv
    python3 batch_asr.py --folder /path/to/videos --output /path/to/result.xlsx

依赖:
    - bl (bailian-cli) 已安装并已鉴权
    - Python 3.8+ / openpyxl
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# ── 支持识别的视频扩展名 ──────────────────────────────────
VIDEO_EXTENSIONS = {
    '.mp4', '.mov', '.mkv', '.avi', '.webm', '.flv',
    '.wmv', '.m4v', '.ts', '.mts', '.m2ts', '.3gp',
    '.ogv', '.mpg', '.mpeg', '.rmvb', '.asf', '.vob',
}

# ── ASR 超时 (秒)，大视频可能需要较长时间
ASR_TIMEOUT = 900


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def get_file_size_mb(filepath: str) -> float:
    """获取文件大小 (MB)。"""
    return os.path.getsize(filepath) / (1024 * 1024)


def run_asr(filepath: str) -> tuple[str | None, float | None, str | None]:
    """
    调用 bl speech recognize 转写单个文件。

    返回 (text, duration_seconds, error)。
    成功时 text 为转写全文，duration_seconds 为音频时长，error 为 None；
    失败时 text/duration 为 None，error 为错误信息。
    """
    with tempfile.NamedTemporaryFile(
        suffix='.json', prefix='asr_', delete=False
    ) as tmp:
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ['bl', 'speech', 'recognize', '--url', filepath,
             '--out', tmp_path, '--output', 'json'],
            capture_output=True, text=True, timeout=ASR_TIMEOUT,
        )

        if result.returncode != 0:
            # 尝试从 stderr 提取有用信息
            err = result.stderr.strip() or result.stdout.strip()
            return None, None, err[:500] if err else f'退出码 {result.returncode}'

        # 读取结构化 JSON
        with open(tmp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 音频时长从 ASR 返回的 JSON 中获取（无需 ffprobe）
        props = data.get('properties', {})
        duration_ms = props.get('original_duration_in_milliseconds')
        duration_s = duration_ms / 1000.0 if duration_ms else None

        transcripts = data.get('transcripts', [])
        if not transcripts:
            return None, duration_s, 'ASR 返回了空结果（可能文件中没有语音）'

        # 合并所有 channel 的文本
        texts = [t.get('text', '') for t in transcripts]
        full_text = '\n'.join(texts).strip()

        if not full_text:
            return None, duration_s, 'ASR 返回了空文本'

        return full_text, duration_s, None

    except subprocess.TimeoutExpired:
        return None, None, f'ASR 处理超时 (>{ASR_TIMEOUT}s)'
    except json.JSONDecodeError as e:
        return None, None, f'JSON 解析失败: {e}'
    except Exception as e:
        return None, None, f'未知错误: {e}'
    finally:
        # 清理临时 JSON 文件
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════════
# 输出
# ═══════════════════════════════════════════════════════════════

FIELD_NAMES = [
    '文件名', '文件路径', '时长(秒)', '文件大小(MB)',
    '完整文本', '处理状态', '处理耗时(秒)', '错误信息',
]


def save_xlsx(results: list[dict], output_path: str) -> None:
    """保存为格式化的 Excel 文件。"""
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'ASR转写结果'

    # ── 表头样式 ──
    header_font = Font(name='Microsoft YaHei', bold=True, color='FFFFFF', size=11)
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

    for col, name in enumerate(FIELD_NAMES, 1):
        cell = ws.cell(row=1, column=col, value=name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    # ── 数据行 ──
    fail_font = Font(color='FF0000', bold=True)
    success_font = Font(color='006100')

    for row_idx, entry in enumerate(results, 2):
        for col_idx, name in enumerate(FIELD_NAMES, 1):
            value = entry[name]
            # 时长格式化为 2 位小数
            if name == '时长(秒)' and value is not None:
                value = round(value, 2)
            elif name == '文件大小(MB)' and value is not None:
                value = round(value, 2)

            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(vertical='top', wrap_text=True)

            if name == '处理状态':
                if value == '失败':
                    cell.font = fail_font
                elif value == '成功':
                    cell.font = success_font

    # ── 列宽 ──
    col_widths = {
        '文件名': 42, '文件路径': 64, '时长(秒)': 11,
        '文件大小(MB)': 13, '完整文本': 72, '处理状态': 10,
        '处理耗时(秒)': 13, '错误信息': 44,
    }
    for col, name in enumerate(FIELD_NAMES, 1):
        ws.column_dimensions[get_column_letter(col)].width = col_widths.get(name, 14)

    # ── 冻结首行 ──
    ws.freeze_panes = 'A2'

    # ── 自动筛选 ──
    ws.auto_filter.ref = f'A1:{get_column_letter(len(FIELD_NAMES))}{len(results) + 1}'

    wb.save(output_path)


def save_csv(results: list[dict], output_path: str) -> None:
    """保存为 UTF-8 CSV (带 BOM，Excel 友好)。"""
    import csv
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_NAMES, extrasaction='ignore')
        writer.writeheader()
        for entry in results:
            # 数值格式化
            row = dict(entry)
            if row.get('时长(秒)') is not None:
                row['时长(秒)'] = round(row['时长(秒)'], 2)
            if row.get('文件大小(MB)') is not None:
                row['文件大小(MB)'] = round(row['文件大小(MB)'], 2)
            writer.writerow(row)


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def generate_output_name(folder: Path, fmt: str) -> str:
    """生成输出文件名。"""
    folder_name = folder.name or folder.parts[-1] if len(folder.parts) > 1 else 'videos'
    # 清理文件夹名中的特殊字符
    safe_name = folder_name.replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'ASR转写结果_{safe_name}_{timestamp}.{fmt}'


def process_folder(folder_path: str, output_format: str = 'xlsx',
                   output_path: str | None = None) -> None:
    """处理文件夹中的所有视频文件。"""
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        print(f'❌ 错误：{folder_path} 不是有效目录')
        sys.exit(1)

    # ── 收集视频文件 (不递归子目录) ──
    video_files: list[Path] = []
    for item in sorted(folder.iterdir()):
        if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS:
            video_files.append(item)

    if not video_files:
        print(f'❌ 在 {folder} 中没有找到视频文件')
        print(f'   支持的格式: {", ".join(sorted(VIDEO_EXTENSIONS))}')
        sys.exit(1)

    # ── 确定输出路径 ──
    if output_path is None:
        output_name = generate_output_name(folder, output_format)
        output_path = str(folder / output_name)
    else:
        output_path = str(Path(output_path).resolve())

    # ── 逐个处理 ──
    total = len(video_files)
    print(f'\n📁 文件夹 : {folder}')
    print(f'🎬 视频数量: {total}')
    print(f'📄 输出格式: {output_format.upper()}')
    print(f'📝 输出文件: {output_path}')
    print(f'{"─" * 60}\n')

    results: list[dict] = []
    overall_start = time.time()

    for idx, filepath in enumerate(video_files, 1):
        # 进度行
        progress = f'[{idx}/{total}]'
        print(f'{progress} {filepath.name}', end=' ', flush=True)

        entry = {
            '文件名': filepath.name,
            '文件路径': str(filepath),
            '时长(秒)': None,
            '文件大小(MB)': None,
            '完整文本': '',
            '处理状态': '处理中',
            '处理耗时(秒)': None,
            '错误信息': '',
        }

        task_start = time.time()

        # ── 获取文件大小 ──
        entry['文件大小(MB)'] = round(get_file_size_mb(str(filepath)), 2)

        # ── ASR 转写（时长从 ASR 返回的 JSON 中提取，无需 ffprobe）──
        text, duration_s, error = run_asr(str(filepath))
        elapsed = round(time.time() - task_start, 1)
        entry['处理耗时(秒)'] = elapsed
        entry['时长(秒)'] = round(duration_s, 2) if duration_s else None

        if text:
            entry['完整文本'] = text
            entry['处理状态'] = '成功'
            print(f'✅ {elapsed}s')
        else:
            entry['处理状态'] = '失败'
            entry['错误信息'] = error or '未知错误'
            print(f'❌ {error[:80] if error else "未知错误"}')

        results.append(entry)

    overall_elapsed = round(time.time() - overall_start, 1)

    # ── 保存输出 ──
    if output_format == 'xlsx':
        save_xlsx(results, output_path)
    else:
        save_csv(results, output_path)

    # ── 汇总 ──
    success = sum(1 for r in results if r['处理状态'] == '成功')
    fail = sum(1 for r in results if r['处理状态'] == '失败')
    total_duration = sum(
        (r['时长(秒)'] or 0) for r in results if r['处理状态'] == '成功'
    )

    print(f'\n{"═" * 60}')
    print(f'✅ 成功: {success}  /  ❌ 失败: {fail}  /  📦 共计: {total}')
    print(f'⏱  总耗时: {overall_elapsed}s  |  音频总时长: {total_duration:.0f}s')
    print(f'📄 输出文件: {output_path}')
    print(f'{"═" * 60}')


# ═══════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='批量视频 ASR 转写 — 基于阿里云百炼 fun-asr',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 batch_asr.py --folder ~/Videos/interviews
  python3 batch_asr.py --folder ~/Videos/meetings --format csv
  python3 batch_asr.py --folder ~/Videos/demo --output ~/reports/demo.xlsx
        """.strip(),
    )
    parser.add_argument(
        '--folder', '-f', required=True,
        help='视频文件夹路径 (不递归子目录)',
    )
    parser.add_argument(
        '--format', '-fmt', choices=['xlsx', 'csv'], default='xlsx',
        help='输出格式: xlsx (默认) 或 csv',
    )
    parser.add_argument(
        '--output', '-o', default=None,
        help='输出文件路径 (默认: 在源文件夹中自动命名)',
    )
    args = parser.parse_args()

    process_folder(
        folder_path=args.folder,
        output_format=args.format,
        output_path=args.output,
    )


if __name__ == '__main__':
    main()
