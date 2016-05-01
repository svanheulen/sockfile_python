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


def send_cias(host, cia_paths):
    print('Connecting to FBI...')
    try:
        conn = socket.create_connection((host, 5000))
    except socket.error:
        print('error: Unable to connect to FBI.')
        return
    try:
        conn.sendall(struct.pack('!I', len(cia_paths)))
    except:
        print('error: Unable to send CIA count to FBI.')
        conn.close()
        return
    print('Waiting for confirmation in FBI...')
    for i in range(len(cia_paths)):
        try:
            ack = conn.recv(1)
        except socket.error:
            print('error: Unable to recieve acknowledge from FBI.')
            break
        if ack[0] == 0:
            print('error: Install was cancelled by FBI.')
            break
        try:
            cia_size = os.stat(cia_paths[i]).st_size
            cia = open(cia_paths[i], 'rb')
        except (IOError, OSError):
            cia_size = 0
            print('({}/{}) Skipping (unable to read file): {}'.format(i + 1, len(cia_paths), cia_paths[i]))
        else:
            print('({}/{}) Sending: {}'.format(i + 1, len(cia_paths), cia_paths[i]))
        try:
            conn.sendall(struct.pack('!Q', cia_size))
        except socket.error:
            print('error: Unable to send CIA size to FBI.')
            if cia_size != 0:
                cia.close()
            break
        if cia_size == 0:
            continue
        try:
            cia_chunk = cia.read(1024 * 128)
            while len(cia_chunk) != 0:
                conn.sendall(cia_chunk)
                cia_chunk = cia.read(1024 * 128)
            cia.close()
        except socket.error:
            print('error: Unable to send CIA data to FBI.')
            cia.close()
            break
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send CIA files to FBI.')
    parser.add_argument('host', help='IP address or host name of the 3DS running FBI.')
    parser.add_argument('cia', nargs='+', help='CIA file to be sent to FBI.')
    args = parser.parse_args()
    send_cias(args.host, args.cia)

