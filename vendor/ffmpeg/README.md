# Offline FFmpeg wheels: Windows x64

This optional wheel set is for the project's Python 3.11, 64-bit Windows environment. The files are **unmodified upstream wheels**, not a new FFmpeg build. Their SHA-256 digests were checked against PyPI release metadata.

- `ffmpeg_python-0.2.0-py3-none-any.whl`: provides `import ffmpeg` and the Python filter/conversion wrapper.
- `future-1.0.0-py3-none-any.whl`: the wrapper's runtime dependency.
- `imageio_ffmpeg-0.6.0-py3-none-win_amd64.whl`: includes the Windows FFmpeg 7.1 executable.

The main application's requirements and existing offline bundle are unchanged. This is an optional add-on for development on the Lloyds laptop.

## Install without internet

Pull or download the repository on an approved connected machine and transfer it through your organization's approved process. From the project root on the offline machine, use the Python interpreter belonging to your application:

```powershell
.\.venv\Scripts\python.exe -m pip install --no-index --only-binary=:all: --find-links .\vendor\ffmpeg\wheels --require-hashes -r .\vendor\ffmpeg\requirements.txt
.\.venv\Scripts\python.exe .\tools\verify_ffmpeg.py
```

No build tools, admin access, model download, or `.ps1` execution is needed. If your organization blocks executable files or package installation, obtain IT approval; these instructions do not override those controls.

## Use from Python

`ffmpeg-python` alone does not install the executable. Pass the bundled executable explicitly to the wrapper:

```python
import ffmpeg
import imageio_ffmpeg

executable = imageio_ffmpeg.get_ffmpeg_exe()
(
    ffmpeg.input("input.mp3")
    .output("output.wav", ac=1, ar=16000, acodec="pcm_s16le")
    .run(cmd=executable)
)
```

Do not install the unrelated PyPI package named `ffmpeg` to obtain this API. If another package shadows `import ffmpeg`, inspect your environment and remove only the conflicting package after confirming it is not needed elsewhere.

## Programs that expect `ffmpeg.exe` on PATH

Installing these wheels does **not** create a globally discoverable `ffmpeg` command. For command-line tools, Whisper-style loaders, or subprocess calls that require that name, make a local copy and add its directory to the **current PowerShell session**:

```powershell
$ffmpegExe = & .\.venv\Scripts\python.exe -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
New-Item -ItemType Directory -Force -Path .\outputs\ffmpeg | Out-Null
Copy-Item -LiteralPath $ffmpegExe -Destination .\outputs\ffmpeg\ffmpeg.exe
$env:PATH = (Resolve-Path .\outputs\ffmpeg).Path + ';' + $env:PATH
ffmpeg -version
```

Launch the application from that same terminal. This does not change the system PATH, and needs to be repeated in a new terminal. The executable path can alternatively be passed directly to `subprocess.run` in your code.

**Limit:** this wheel contains `ffmpeg.exe`, not `ffprobe.exe`. Code using `ffmpeg.probe()` or another tool that requires FFprobe needs a separately approved FFprobe binary. It also does not provide C-library DLLs for native linking.

## Provenance and licensing

Upstream releases: [ffmpeg-python 0.2.0](https://pypi.org/project/ffmpeg-python/0.2.0/), [future 1.0.0](https://pypi.org/project/future/1.0.0/), [imageio-ffmpeg 0.6.0](https://pypi.org/project/imageio-ffmpeg/0.6.0/). Requirements include exact SHA-256 digests. License notices inside the original wheels are retained unchanged. The Python wrapper is Apache-2.0, `future` is MIT, and the imageio wrapper is BSD-2-Clause. Those wrapper licenses must not be confused with the FFmpeg executable's own license.

The bundled executable identifies itself as `7.1-essentials_build-www.gyan.dev`; its configuration enables GPL and version 3, and `ffmpeg -L` reports **GPLv3-or-later**. Its upstream build is [Gyan's 7.1 essentials release](https://github.com/GyanD/codexffmpeg/releases/tag/7.1), whose FFmpeg source is [commit b08d7969c5](https://github.com/FFmpeg/FFmpeg/tree/b08d7969c5). See [the build distributor's information](https://www.gyan.dev/ffmpeg/builds/) for the included external libraries. Consult [FFmpeg's license information](https://ffmpeg.org/legal.html), the included GPL text, and the upstream distributor's source/build materials before further redistribution or organizational deployment. These files do not override your organization's software approval requirements.
