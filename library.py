__all__ = ['get_file_odt', 'get_image_odt', 'rename_files', 'dedup_dir', 'convert_heic_dir']

import hashlib
import random
import string
from datetime import datetime
from json.decoder import JSONDecodeError

from PIL import Image, UnidentifiedImageError
import os
import logging
import pathlib
import subprocess
import json
import dateutil.parser
import exifread


logger = logging.getLogger(__name__)


class MRNConfig:
    IGNORE_PTN = ['tmp', '#', '.', 'mrn']
    VIDEO_SFX = ['.mp4', '.avi', '.wmv', '.mkv', '.rmvb', '.iso', '.asf', '.mpg', '.mov']
    PHOTO_SFX = ['.jpg', '.jpeg', '.arw', '.cr2', '.nef', '.dng', '.bmp', '.gif', '.heic']
    PHOTO_RAW_SFX = ['.arw', '.cr2', '.nef', '.dng']


def get_file_odt(file_path: str):
    if not (os.path.exists(file_path) and os.path.isfile(file_path)):
        raise FileNotFoundError("{] not found".format(file_path))
    return datetime.fromtimestamp(os.stat(file_path).st_mtime)


def get_video_odt(file_path: str):
    cmd = "ffprobe -v quiet -show_format -of json -i {}".format(file_path)
    try:
        child_proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = child_proc.communicate()
        rc = child_proc.returncode
        if rc is None or rc != 0:
            logger.error(f'ffprobe error {file_path}: {err}')
        out_dict = json.loads(out.decode("ascii"))['format']
        format_tag_dict = out_dict.get('tags', {})
        creation_time = format_tag_dict.get('creation_time', None)
    except (KeyError, UnicodeDecodeError, JSONDecodeError) as ex:
        logger.error(f'ffprobe json parsing error  {file_path}: {ex}')
        creation_time = None
    try:
        creation_odt = dateutil.parser.parse(creation_time)
    except (ValueError, OverflowError, TypeError) as ex:
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
    if file_suffix.lower() in MRNConfig.PHOTO_RAW_SFX:
        cmd = 'exiv2 -pt -K Exif.Photo.DateTimeOriginal {}'.format(file_path)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(cmd)
        child_proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = child_proc.communicate()
        rc = child_proc.returncode
        if rc is None or rc != 0:
            logger.error(f'exiv2 extraction error {file_path}: {err}')
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(out)
            logger.debug(err)
        sdt = ' '.join(out.decode('ascii').strip().split()[-2:])
        raw_odt = datetime.strptime(sdt, '%Y:%m:%d %H:%M:%S')
        return raw_odt

    if file_suffix.lower() in ['.heic']:
        # Handle HEIC files
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                im_sdt = tags.get('EXIF DateTimeOriginal').values
        except (AttributeError, KeyError) as err:
            logger.error(f'EXIF extraction error {file_path}: {err}')
            return None
    else:
        # regular image files
        try:
            im = Image.open(file_path)
            im_sdt = im.getexif()[36867]
        except (UnidentifiedImageError, KeyError) as err:
            logger.error(f'EXIF extraction error {file_path}: {err}')
            return None

    try:
        image_odt = datetime.strptime(im_sdt, '%Y:%m:%d %H:%M:%S')
    except ValueError as err:
        logger.error(f'odt format error {file_path}: {im_sdt} {err}')
        return None
    return image_odt


def convert_heic_file(root, file):
    src_path = os.path.join(root, file)
    file_stem = pathlib.Path(file).stem
    file_suffix = pathlib.Path(file).suffix.lower()
    dst_path = os.path.join(root, f'{file_stem}.jpg')
    if not os.path.exists(src_path):
        logger.error(f'Cannot convert non-existent {src_path}')
        return 1
    if not file_suffix == '.heic':
        logger.error(f'Cannot convert non-HEIC {src_path}')
        return 1
    if os.path.exists(dst_path):
        logger.error(f'Cannot convert {src_path} as {dst_path} already exists')
        return 1
    cmd = f'heif-convert -q 100 {src_path} {dst_path}'
    child_proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = child_proc.communicate()
    rc = child_proc.returncode
    if rc is None or rc != 0:
        logger.error(f'HEIC Convert error {src_path}: {err}')
    else:
        logger.info(f'Success converted HEIC {src_path} to {dst_path}')
    return rc


def convert_heic_dir(root):
    if not os.path.exists(root):
        logger.error(f'Cannot run HEIC conversion on non-existent directory {root}')

    logger.info(f'Start converting all HEIC files in {root} recursively')
    for root, dirs, files in os.walk(root, topdown=False):
        for file in files:
            file_suffix = pathlib.Path(file).suffix.lower()
            if file_suffix == '.heic':
                convert_heic_file(root, file)
    logger.info(f'Completed converting all HEIC files in {root}')


def rename_files(input_dir, output_dir):
    logger.info(f'Start ingesting from {input_dir} to {output_dir}')
    input_objects = os.listdir(input_dir)

    albums = []
    for entry in input_objects:
        if os.path.isdir(os.path.join(input_dir, entry)):
            if any([entry.startswith(ignore_pattern) for ignore_pattern in MRNConfig.IGNORE_PTN]):
                logger.info(f'Skip ignored directory {entry}')
                continue
            albums.append(entry)
    logger.info(f'Albums: {albums}')

    for album in albums:
        # input and destination paths for the album
        album_path = os.path.join(input_dir, album)
        photo_path = os.path.join(output_dir, album, 'photo')
        if not os.path.exists(photo_path):
            os.makedirs(photo_path)
        video_path = os.path.join(output_dir, album, 'video')
        if not os.path.exists(video_path):
            os.makedirs(video_path)
        logger.info(f'Start ingesting {album}')

        files = []
        for entry in os.listdir(album_path):
            if os.path.isfile(os.path.join(album_path, entry)):
                file = entry
                file_path = os.path.join(album_path, file)
                if any([file.startswith(ignore_pattern) for ignore_pattern in MRNConfig.IGNORE_PTN]):
                    logger.info(f'Skip ignored file {album}/{file}')
                    continue

                file_suffix = pathlib.Path(file).suffix.lower()

                if file_suffix not in MRNConfig.PHOTO_SFX and file_suffix not in MRNConfig.VIDEO_SFX:
                    logger.info(f'Skip non-photo and non-video file {album}/{file}')
                    continue

                if file_suffix in MRNConfig.VIDEO_SFX:
                    dest_path = video_path
                    odt = get_video_odt(file_path)
                elif file_suffix in MRNConfig.PHOTO_SFX:
                    dest_path = photo_path
                    odt = get_image_odt(file_path)
                else:
                    continue

                if odt is None:
                    # fall back to file creation date
                    logger.error(f'Cannot parse creation date from EXIF for {album}/{file}; fall back to file date')
                    odt = get_file_odt(file_path)

                if odt is None:
                    # this file is really not good!
                    logger.error(f'Skip {album}/{file}; cannot identify any creation datetime!')
                    continue

                # Put outputs in year-quarter directories
                odt_quarter = (odt.month - 1) // 3 + 1
                dest_path = os.path.join(dest_path, f'{odt.year}Q{odt_quarter}')

                if not os.path.exists(dest_path):
                    logger.info(f'Create {dest_path}')
                    os.mkdir(dest_path)

                # form destination filename, use random string if needed to avoid collision
                sdt = odt.strftime("%Y%m%d_%H%M%S")
                dest_filename = f'{sdt}_01{file_suffix}'
                while os.path.exists(os.path.join(dest_path, dest_filename)):
                    rd_str = ''.join(random.choices(string.ascii_uppercase, k=4))
                    dest_filename = f'{sdt}_{rd_str}{file_suffix}'

                os.rename(file_path, os.path.join(dest_path, dest_filename))
                logger.info(f'Success {album}/{file} -> {dest_path}/{dest_filename}')
        logger.info(f'Completed ingesting {album}')
    logger.info(f'Completed ingesting {input_dir} to {output_dir}')
    return None


def dedup_files(file_paths):
    logger.info(f'Start deduping {len(file_paths)} files')
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
                logger.info('Dup: ' + ' '.join([file1, file2, str(size1), str(size2), md1.hexdigest(), md2.hexdigest()]))
    for file in dup_files:
        os.remove(file)


def dedup_dir(output_dir):
    if not os.path.exists(output_dir):
        logger.error(f'Cannot de-duplicate non-existent directory {output_dir}')
        return 1

    logger.info(f'Start de-duplicating {output_dir} recursively')
    file_paths = []
    for root, dirs, files in os.walk(output_dir, topdown=False):
        for file in files:
            file_paths.append(os.path.join(root, file))
    dedup_files(file_paths)
    logger.info(f'Completed de-duplicating {output_dir}')
    return 0

