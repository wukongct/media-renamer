# media-renamer
Simple tool for organizing imported photos and videos.
Given a set of photo and video files, the tool reads the creation date/time, and rename the files into `YYYYMMDD_HHMMSS_{i}.*` format.

The tool uses EXIF and video-container-encoded creation time (and failing that, fall back to file system time).
In case of name collision, a counter `{i = 1,2,...}` is included.

## Installation
Ensure `ffmpeg` and `exiv2` are installed, if you want to handle video files and raw images (e.g `arw`, `cr2`, `nef`, `dng`), respectively.

```shell
git clone git@github.com:wukongct/media-renamer.git
cd media-renamer
make env
```

## Usage
```shell
source ./venv/bin/activate
./main.py {FILES_TO_BE_RENAMED} {OUTPUT_DIRECTORY}
```
