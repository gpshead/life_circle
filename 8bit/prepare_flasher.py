#!/usr/bin/env python3

import os
import pathlib
import subprocess
import sys

template_creator_exe = pathlib.Path(__file__).parent/ '..' / 'trinketloader' / 'generate_images_cpp.py'
firmware_hex_path = pathlib.Path(__file__).parent / '.pio' / 'build' / 'attiny85' / 'firmware.hex'
if not firmware_hex_path.exists():
    raise RuntimeError(f'{firmware_hex_path} not found, did you build?')
subprocess.check_call([str(template_creator_exe), str(firmware_hex_path)])
os.chdir('../trinketloader')
subprocess.check_call(['pio', 'run', '-t', 'upload'])
