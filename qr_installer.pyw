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
import math
import os
import shutil
import socket
import threading
try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from tkinter import Tk, Frame, Label, BitmapImage
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from Tkinter import Tk, Frame, Label, BitmapImage
import pyqrcode


class SingleFileServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, file_path):
        self.file_path = file_path
        HTTPServer.__init__(self, server_address, RequestHandlerClass)

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, self.file_path)


class SingleFileRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server, file_path):
        self.file_path = file_path
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        try:
            f = open(self.file_path, 'rb')
        except:
            self.send_error(404, 'File not found')
            return
        self.send_response(200, 'OK')
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', os.fstat(f.fileno()).st_size)
        self.end_headers()
        try:
            shutil.copyfileobj(f, self.wfile)
        except:
            pass
        f.close()


def qrcode_to_xbm(code, quiet_zone=4, zoom=5):
    pixel_width = (len(code[0]) + quiet_zone * 2) * zoom
    xbm = '#define im_width {}\n#define im_height {}\nstatic char im_bits[] = {{\n'.format(pixel_width, pixel_width)
    byte_width = int(math.ceil(pixel_width / 8.0))
    xbm += ('0x00,' * byte_width + '\n') * quiet_zone * zoom
    for row in code:
        row_bits = '0' * quiet_zone * zoom
        for b in row:
            row_bits += str(b) * zoom
        row_bits += '0' * quiet_zone * zoom
        row_bytes = ''
        for b in range(byte_width):
            row_bytes += '0x{:02x},'.format(int(row_bits[:8][::-1], 2))
            row_bits = row_bits[8:]
        row_bytes += '\n'
        xbm += row_bytes * zoom
    return xbm + ('0x00,' * byte_width + '\n') * quiet_zone * zoom + '};'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Serve a CIA file to FBI via a QR code.')
    parser.add_argument('-t', action='store_true', help='Display QR code in terminal instead of using a GUI.')
    parser.add_argument('cia', help='CIA file to be serverd.')
    args = parser.parse_args()
    server = SingleFileServer(('', 8080), SingleFileRequestHandler, args.cia)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    qr = pyqrcode.create('HTTP://{}:{}/installer.cia'.format(socket.gethostbyname(server.server_name), server.server_port))
    if args.t:
        print(qr.terminal())
        print('Serving file: {}'.format(os.path.abspath(args.cia)))
        try:
            raw_input('Press the Enter key to quit.')
        except NameError:
            input('Press the Enter key to quit.')
    else:
        root = Tk()
        root.title('FBI QR Code Install')
        main_frame = Frame(root)
        main_frame.pack()
        qr_bitmap = BitmapImage(data=qrcode_to_xbm(qr.code), foreground='black', background='white')
        qr_label = Label(main_frame, image=qr_bitmap)
        qr_label.pack()
        msg_label = Label(main_frame, text='Serving file: {}'.format(os.path.abspath(args.cia)))
        msg_label.pack()
        root.mainloop()
    server.shutdown()

