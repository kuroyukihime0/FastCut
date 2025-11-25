- **Keyboard Shortcuts**: 
  - `C` - Set start point
  - `V` - Set end point
- **Preview**: Preview selected range before exporting
- **Smart Cut**: Optional keyframe-aligned cutting for faster processing
- **Playback Controls**: Variable speed playback (0.25x - 3.0x)
- **Fast Export**: FFmpeg-based export without re-encoding

## Requirements

- Python 3.10+
- PyQt6
- FFmpeg (must be in system PATH)

## Installation

1. Install Python dependencies:
```bash
pip install PyQt6
```

2. Install FFmpeg:
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Add to system PATH

## Usage

1. Run the application:
```bash
python main.py
```

2. Load a video file (drag & drop or click "Open File")
3. Set start point (click "Set Start [C]" or press `C`)
4. Set end point (click "Set End [V]" or press `V`)
5. Preview the selection (optional)
6. Click "Export Clip" to save

## Configuration

- **Export Directory**: Settings → Select Export Folder
- **Smart Cut**: Settings → Smart Cut (Keyframe Aligned)
- **Playback Speed**: Saved automatically

## License

MIT License
