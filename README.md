# media-renamer
Simple tool for organizing imported photos and videos.
Given an input directory, the tool:
* Creates a jpg copy of any .heic pictures, as HEIC is not as widely-supported.
* Renames and moves photo/videos to an output directory, with 'YYYYMMDD_HHMMSS' style naming.
  * It uses level-1 sub-directories of `INPUT_DIR` as albums.
  * It separates photos and videos.
  * It organizes photos and videos into `YYYYQ{1,2,3,4}` directories for each album.

The tool uses EXIF and video-container-encoded creation time (and failing that, fall back to file system time).
In case of photos taken at the same second-precision timestamp, random string is appended to file name to avoid collision.

## Input Directory
Please create a directory structure for ingesting photos and videos:
```commandline
$DATA_DIR
|- $INPUT_DIR
    |- album_1
        |- pic1.jpg
        |- vid1.mp4
        |- ...
    |- album_2
    |- ...
|- $OUTPUT_DIR
```


## Docker
### Installation

Ensure you have docker installed. The container is based on official ubuntu image.
```shell
git clone git@github.com:wukongct/media-renamer.git
docker build -t mrn media-renamer/
```

### Usage
```shell
docker run -d --name mrn1 -v {YOUR_IMG_DIR}:/data:rw mrn:latest
```
Optionally, you can export `INPUT_DIR` and `OUTPUT_DIR` environment variables, which defaults to `input` and `originals`, respectively.


## Running Directly on Host
### Installation

Ensure `ffmpeg` and `exiv2` are installed, if you want to handle video files and raw images (e.g `arw`, `cr2`, `nef`, `dng`), respectively.

```shell
git clone git@github.com:wukongct/media-renamer.git
cd media-renamer
make env
```
### Usage
```shell
source ./venv/bin/activate
./main.py {FILES_TO_BE_RENAMED} {OUTPUT_DIRECTORY}
```
