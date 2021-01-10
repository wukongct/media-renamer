__all__ = ['get_file_odt', 'get_image_odt', 'rename_files', 'dedup_dir']

import hashlib
from datetime import datetime
from pprint import pprint
from typing import Iterable

from PIL import Image, UnidentifiedImageError
import os
import logging
import pathlib
import subprocess
import json
import dateutil.parser


logger = logging.getLogger(__name__)


def init_collision_dict(dr, collision_dict=None):
    if collision_dict is None:
        collision_dict = dict()

    files = os.listdir(dr)
    for file in files:
        if not os.path.isfile(os.path.join(dr, file)):
            continue
        file_base = os.path.basename(file)
        file_sdt = '_'.join(os.path.splitext(file_base)[0].split('_')[1:3])
        file_idx = os.path.splitext(file_base)[0].split('_')[-1]
        file_suffix = pathlib.Path(file).suffix.lower()
        file_key = file_sdt + file_suffix
        try:
            file_idx = int(file_idx)
            if file_key not in collision_dict.keys():
                collision_dict[file_key] = 0
            elif file_idx > collision_dict[file_key]:
                collision_dict[file_key] = file_idx
        except ValueError as ex:
            logger.error(ex)
    return collision_dict


def get_file_odt(file_path: str):
    if not (os.path.exists(file_path) and os.path.isfile(file_path)):
        raise FileNotFoundError("{] not found".format(file_path))
    return datetime.fromtimestamp(os.stat(file_path).st_mtime)


def get_video_odt(file_path: str):
    format_cmd = "ffprobe -v quiet -show_format -of json -i {}".format(file_path)
    try:
        out, err = subprocess.Popen(format_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        out_dict = json.loads(out.decode("ascii"))['format']
        format_tag_dict = out_dict.get('tags', {})
        creation_time = format_tag_dict.get('creation_time', None)
    except (KeyError, UnicodeDecodeError):
        creation_time = None
    try:
        creation_odt = dateutil.parser.parse(creation_time)
    except (ValueError, OverflowError) as ex:
        logger.error(ex)
        creation_odt = None
    # print(file_path, creation_time, creation_odt)
    return creation_odt


def get_image_odt(file_path: str):
    if not (os.path.exists(file_path) and os.path.isfile(file_path)):
        logger.error("{] not found".format(file_path))
        return None

    # Handle RAW files first
    file_suffix = pathlib.Path(file_path).suffix
    if file_suffix.lower() in ['.arw', '.cr2', '.nef', '.dng']:
        cmd = 'exiv2 -pt -K Exif.Photo.DateTimeOriginal {}'.format(file_path)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(cmd)
        out, err = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(out)
            logger.debug(err)
        sdt = ' '.join(out.decode('ascii').strip().split()[-2:])
        raw_odt = datetime.strptime(sdt, '%Y:%m:%d %H:%M:%S')
        return raw_odt

    try:
        im = Image.open(file_path)
        im_sdt = im.getexif()[36867]
    except (UnidentifiedImageError, KeyError) as ex:
        logger.error(ex)
        return None

    try:
        image_odt = datetime.strptime(im_sdt, '%Y:%m:%d %H:%M:%S')
    except ValueError as ex:
        logger.error(ex)
        return None
    return image_odt


def get_dupe_files(file_paths: Iterable[str]):
    file_sizes = [os.stat(file_path).st_size for file_path in file_paths]
    sorted_fs = [(file, size) for size, file in sorted(zip(file_sizes, file_paths))]
    BUF_SIZE = 65536
    dup_files = list()
    for (file1, size1), (file2, size2) in zip(sorted_fs[:-1], sorted_fs[1:]):
        if size1 == size2:
            md1 = hashlib.md5()
            md2 = hashlib.md5()
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                md1.update(f1.read(BUF_SIZE))
                md2.update(f2.read(BUF_SIZE))
            if md1.digest() == md2.digest():
                dup_files.append(file2)
                logger.info('Dup: ' + '  '.join([file1, file2, str(size1), str(size2), md1.hexdigest(), md2.hexdigest()]))
    for file in dup_files:
        os.remove(file)
    


def rename_files(files, dest):
    logger.info(files)
    logger.info(dest)
    video_formats = ['.mp4', '.avi', '.wmv', '.mkv', '.rmvb', '.iso', '.asf', '.mpg', '.mov']
    photo_path = os.path.join(dest, 'photo')
    video_path = os.path.join(dest, 'video')
    photo_dict = init_collision_dict(photo_path)
    video_dict = init_collision_dict(video_path)

    # pprint(photo_dict)
    # pprint(video_dict)

    for file in files:
        if not os.path.isfile(file):
            continue

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(file)
            logger.debug(get_image_odt(file))
            logger.debug(get_file_odt(file))

        file_suffix = pathlib.Path(file).suffix.lower()
        if file_suffix in video_formats:
            dest_path = video_path
        else:
            dest_path = photo_path

        if file_suffix in video_formats:
            odt = get_video_odt(file)
        else:
            odt = get_image_odt(file)

        if odt is None:
            odt = get_file_odt(file)

        if odt is None:
            logger.error("Cannot get creation time for {}, skipping".format(file))
            continue

        sdt = odt.strftime("%Y%m%d_%H%M%S")
        file_key = sdt + file_suffix

        if file_suffix in video_formats:
            video_dict[file_key] = video_dict.get(file_key, 0) + 1
            new_file = f'vid_{sdt}_{video_dict[file_key]:02d}{file_suffix}'
        else:
            photo_dict[file_key] = photo_dict.get(file_key, 0) + 1
            new_file = f'img_{sdt}_{photo_dict[file_key]:02d}{file_suffix}'

        logger.info("{} -> {}".format(file, os.path.join(dest_path, new_file)))
        os.rename(file, os.path.join(dest_path, new_file))

    logger.info('Completed renaming')
    return None


def dedup_dir(dest):
    logger.info(dest)
    photo_dir = os.path.join(dest, 'photo')
    video_dir = os.path.join(dest, 'video')
    photos = [os.path.join(photo_dir, x) for x in os.listdir(photo_dir)]
    videos = [os.path.join(video_dir, x) for x in os.listdir(video_dir)]
    # print(photos)
    # print(videos)

    get_dupe_files(photos)
    get_dupe_files(videos)

