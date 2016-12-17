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
import threading
try:
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    from tkinter import Tk, Frame, Label, BitmapImage
except ImportError:
    from BaseHTTPServer import SimpleHTTPRequestHandler, HTTPServer
    from Tkinter import Tk, Frame, Label, BitmapImage
import pyqrcode


def main(input_path, ip_port=8080, terminal_display=False):
    if not os.path.exists(input_path):
        print('error: input path does not exist: {}'.format(input_path))
        return
    file_list = []
    if os.path.isfile(input_path) and (input_path.lower().endswith('.cia') or input_path.lower().endswith('.tik')):
        file_list.append(os.path.basename(input_path))
        input_path = os.path.dirname(input_path)
    elif os.path.isdir(input_path):
        for entry in os.listdir(input_path):
            if entry.lower().endswith('.cia') or entry.lower().endswith('.tik'):
                file_list.append(entry)
    if len(file_list) == 0:
        print('error: no CIA/TIK files found at input path: {}'.format(input_path))
        return
    input_path = os.path.abspath(input_path)
    os.chdir(input_path)
    server = HTTPServer(('', ip_port), SimpleHTTPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    ip_addr = socket.gethostbyname(server.server_name)
    qr_data = '\n'.join(['{}:{}/{}'.format(ip_addr, ip_port, f) for f in file_list])
    qr_code = pyqrcode.create(qr_data)
    if terminal_display:
        print(qr_code.terminal())
        print('Serving from path: {}'.format(input_path))
        print('Serving files:\n    {}'.format('\n    '.join(file_list)))
        try:
            raw_input('Press the Enter key to quit.\n')
        except NameError:
            input('Press the Enter key to quit.\n')
    else:
        root = Tk()
        root.title('FBI QR Code Install')
        main_frame = Frame(root)
        main_frame.pack()
        qr_bitmap = BitmapImage(data=qr_code.xbm(scale=6), foreground='black', background='white')
        qr_label = Label(main_frame, image=qr_bitmap)
        qr_label.pack()
        path_label = Label(main_frame, text='Serving from path:\n{}'.format(input_path))
        path_label.pack()
        files_label = Label(main_frame, text='Serving files:\n{}'.format('\n'.join(file_list)))
        files_label.pack()
        root.mainloop()
    server.shutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Serve CIA/TIK files to FBI via a QR code.')
    parser.add_argument('-p', '--port', default=8080, type=int, help='The port to listen on.')
    parser.add_argument('-t', action='store_true', help='Display QR code in terminal instead of using a GUI.')
    parser.add_argument('input', help='A folder conatianing CIA/TIK files or a single CIA/TIK file.')
    args = parser.parse_args()
    main(args.input, args.port, args.t)

