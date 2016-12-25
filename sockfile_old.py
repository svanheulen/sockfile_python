#!/usr/bin/python

# Copyright 2016 Seth VanHeulen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import argparse
import os
import socket
import struct


def send_file(host, file_path):
    print('Connecting to FBI...')
    try:
        conn = socket.create_connection((host, 5000))
    except socket.error:
        print('error: Unable to connect to FBI.')
        return
    try:
        file_ = open(file_path, 'rb')
        file_.seek(0, os.SEEK_END)
        file_size = file_.tell()
        file_.seek(0)
    except (IOError, OSError):
        print('error: Unable to read file: {}'.format(file_path))
        conn.close()
        return
    print('Sending: {}'.format(file_path))
    try:
        conn.sendall(struct.pack('!Q', file_size))
    except socket.error:
        print('error: Unable to send file size to FBI.')
        conn.close()
        return
    try:
        file_chunk = file_.read(1024 * 128)
        while len(file_chunk) != 0:
            conn.sendall(file_chunk)
            file_chunk = file_.read(1024 * 128)
        file_.close()
    except socket.error:
        print('error: Unable to send file to FBI.')
        file_.close()
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send CIA files to FBI (old protocol).')
    parser.add_argument('host', help='IP address or host name of the 3DS running FBI.')
    parser.add_argument('input', help='A CIA file to be sent to FBI.')
    args = parser.parse_args()
    send_file(args.host, args.input)

