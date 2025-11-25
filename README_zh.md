# FastCut (快剪)

<p align="center">
  <img src="assets/logo.png" alt="FastCut Logo" width="128"/>
</p>

FastCut 是一款轻量级且高效的视频剪辑工具，专为快速精准的视频截取而设计。您可以轻松设置开始和结束点，预览选区，并进行无损导出，速度极快。

## 功能特点

- **高效工作流**:
  - **快捷键支持**:
    - `C` - 设置开始点
    - `V` - 设置结束点
  - **拖拽加载**: 直接将视频文件拖入窗口即可加载。
- **精准控制**:
  - **实时预览**: 导出前预览选定片段，确保准确无误。
  - **播放控制**: 支持变速播放 (0.25x - 3.0x)，方便逐帧查看。
- **高性能**:
  - **快速导出**: 使用 FFmpeg 流复制技术，无损画质且瞬间完成导出。
  - **智能剪切**: 可选的关键帧对齐剪切模式，处理速度更快。

## 下载 (Downloads)

我们提供两种版本的发布包：

- **完整版 (Full Version - 推荐)**: 内置 FFmpeg，无需安装任何外部依赖，下载即用。
  - 文件名: `FastCut-ffmpeg-embed-*.exe` (Windows) / `FastCut-ffmpeg-embed-*-osx` (macOS)
- **精简版 (Lite Version)**: 体积更小，但需要您自行安装 FFmpeg 并配置到系统环境变量中。
  - 文件名: `FastCut-*.exe` (Windows) / `FastCut-*-osx` (macOS)

## 环境要求

- **精简版**: FFmpeg (必须添加到系统 PATH 环境变量中)
- **源码运行**: Python 3.10+, PyQt6

## 安装指南

1. **安装 Python 依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **安装 FFmpeg**:
   - 从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载。
   - 将 `bin` 文件夹添加到系统的 PATH 环境变量中。

## 使用说明

1. **启动应用**:
   ```bash
   python main.py
   ```

2. **加载视频**: 拖拽文件到窗口或点击 "Open File" (打开文件)。
3. **选择片段**:
   - 移动到开始位置并按 `C` (或点击 "Set Start")。
   - 移动到结束位置并按 `V` (或点击 "Set End")。
4. **导出**: 点击 "Export Clip" (导出片段) 即可瞬间保存视频。

## 配置

- **导出目录**: 通过 `Settings` -> `Select Export Folder` 修改保存路径。
- **智能剪切**: 在 `Settings` 中切换 Smart Cut (关键帧对齐)。
- **播放速度**: 自动保存您上次使用的播放速度。

## 许可证

MIT License
