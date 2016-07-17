#!/usr/bin/env python3
# vim: set sw=4 expandtab ai
#
# Released under the Apache 2.0 license.
# http://www.apache.org/licenses/

"""Push a file to a wipy's /flash directory via ftp.

Usage:
  push2wipy.py 192.168.4.5 myfile.py
"""

import ftplib
import os
import sys


def main(argv):
    hostname, filename = argv[1:]
    with ftplib.FTP(host=hostname, timeout=10,
                    user='micro', passwd='python') as wipy_ftp:
      wipy_ftp.set_pasv(True)
      print('connected:', wipy_ftp.getwelcome())
      print('cd flash:', wipy_ftp.cwd('flash'))
      with open(filename, 'rb') as binaryfile:
          basename = os.path.basename(filename)
          command = 'STOR {}'.format(basename)
          print(command+':', wipy_ftp.storbinary(command, binaryfile))
      print('WiPy /flash contents via dir():')
      wipy_ftp.dir()


if __name__ == '__main__':
    try:
        main(sys.argv)
    except Exception:
        print(__doc__)
        raise
