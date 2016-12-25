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


def send_files(host, file_list):
    print('Connecting to FBI...')
    try:
        conn = socket.create_connection((host, 5000))
    except socket.error:
        print('error: Unable to connect to FBI.')
        return
    try:
        conn.sendall(struct.pack('!I', len(file_list)))
    except:
        print('error: Unable to send file count to FBI.')
        conn.close()
        return
    print('Waiting for confirmation in FBI...')
    for i in range(len(file_list)):
        try:
            ack = conn.recv(1)
        except socket.error:
            print('error: Unable to recieve acknowledge from FBI.')
            break
        if ack[0] == 0:
            print('error: Install was cancelled by FBI.')
            break
        try:
            file_ = open(file_list[i], 'rb')
            file_.seek(0, os.SEEK_END)
            file_size = file_.tell()
            file_.seek(0)
        except (IOError, OSError):
            file_ = None
            file_size = 0
            print('({}/{}) Skipping (unable to read file): {}'.format(i + 1, len(file_list), file_list[i]))
        else:
            print('({}/{}) Sending: {}'.format(i + 1, len(file_list), file_list[i]))
        try:
            conn.sendall(struct.pack('!Q', file_size))
        except socket.error:
            print('error: Unable to send file size to FBI.')
            if file_ is not None:
                file_.close()
            break
        if file_ is None:
            continue
        try:
            file_chunk = file_.read(1024 * 128)
            while len(file_chunk) != 0:
                conn.sendall(file_chunk)
                file_chunk = file_.read(1024 * 128)
            file_.close()
        except socket.error:
            print('error: Unable to send file to FBI.')
            file_.close()
            break
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send CIA/TIK files to FBI.')
    parser.add_argument('host', help='IP address or host name of the 3DS running FBI.')
    parser.add_argument('input', nargs='+', help='A CIA/TIK file to be sent to FBI.')
    args = parser.parse_args()
    send_files(args.host, args.input)

