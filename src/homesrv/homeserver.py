#!/usr/bin/env python3
"""
Homesrv HTTP Server
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import urllib
import os
import shutil
import signal
import sys
from homesrv.config import cfg
from homesrv.HomeSrvHtml import HomeSrvHtml


# =======================
class RequestHandler(BaseHTTPRequestHandler):
    # ----------------------------------
    def _set_header(self, status=200, type="html", caching=True):
        if status == 200:
            self.send_response(200)
            self.send_header('Content-type', 'text/'+type)
            if caching:
                self.send_header('Cache-Control', 'max-age=604800')
            else:  
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')  
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
        else:
            self.send_error(status)
        self.end_headers()

    # ----------------------------------
    def do_GET(self):
        global hsrv
        parts = self.path.strip('/').split('?')
        ressource = parts[0]
        if ressource == '':
            ressource = "index.html"  
        if len(parts) > 1:
            params = urllib.parse.parse_qs(parts[1])
        else:
            params = ''
            if ressource == "index.html":
                # index.html is dynamically created
                logging.debug("GET request, dynamic ressource: {}".format(ressource) )  
                hsrv.refresh()
                content = hsrv.html_data.encode("utf-8")
                self._set_header(200, type="html", caching=False)
                self.wfile.write(content)  
            else: # read file from file system
                webroot = os.path.normpath(cfg['WEB_ROOT'])    
                fname = os.path.normpath(os.path.join(webroot, ressource))
                # Restrict access to files in/below WEB_ROOT - not outside!
                if os.path.commonpath([webroot, fname]) == webroot:
                    logging.debug("GET request, ressource: {}, fname: {}, params: {}".format(ressource, fname, str(params)) )  
                    try:
                        with open(fname, 'rb') as file:
                            content = file.read()
                            if fname.endswith(".css"):
                                self._set_header(200, type="css", caching=False)
                            else:
                                self._set_header(200, type="html", caching=True)
                            self.wfile.write(content)  
                    except IOError as e:
                        logging.warning("Couldn't open {}".format(e))
                        self._set_header(404)
                else:
                    logging.warning("Requested file {} is not in WEB_ROOT - file blocked for securoty reasons-".format(fname))
                    self._set_header(404)

    # ----------------------------------
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.debug("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))
        self._set_header()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

#===========================================
#-------------------------------------------
def signal_handler(signal_number, frame):
    global httpd
    logging.warning('Received Signal {}. Graceful shutdown initiated.'.format(signal_number))
    httpd_stop(httpd)

#-------------------------------------------
def copy_files(src_dir, dest_dir):
    for f in os.listdir(src_dir):
        src_f = os.path.join(src_dir, f)
        dest_f = os.path.join(dest_dir, f)
        if os.path.isfile(src_f):
            # copy file if destination does not exist or source file is newer
            if not os.path.exists(dest_f) or (os.stat(src_f).st_mtime - os.stat(dest_f).st_mtime > 1):
                logging.info("Copying {} --> {}".format(src_f, dest_f))
                shutil.copy2(src_f, dest_f)

#-------------------------------------------
def initialize_templates():
    # Copy latest templates to HTML directory
    web_root = cfg["WEB_ROOT"]     # HTML directory
    base_dir = os.path.dirname(__file__) # Base installation directory
    template_dir = os.path.join(base_dir, os.pardir, "homesrv_templates") 
    logging.info("Updating template files {} to web root {}".format(template_dir, web_root))
    if os.path.isdir(web_root):
        copy_files(template_dir, web_root)
        os.makedirs(os.path.join(web_root, "images"), exist_ok=True)
        copy_files(os.path.join(template_dir, "images"), os.path.join(web_root, "images"))
    else:
        logging.error("Web root directory doesn't exist: {}".format(web_root))

#----------------------
def httpd_stop():
    global httpd
    if httpd:
        httpd.server_close()
        httpd = None
        logging.info('httpd stopped')

#----------------------
def main():
    global httpd
    global hsrv

    logging.info('Initializing...')
    httpd = None
    hsrv = None
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    initialize_templates()
    hsrv = HomeSrvHtml()
    hsrv.refresh()

    logging.info('Starting httpd on {}:{}'.format(cfg['WEB_SERVER'], cfg['WEB_PORT']))
    httpd = HTTPServer((cfg['WEB_SERVER'], cfg['WEB_PORT']), RequestHandler, bind_and_activate=False)
    try:
        httpd.server_bind()
        httpd.server_activate()
        logging.info("httpd started")
    except BaseException as e:
        logging.error("Couldn't start http server: {}".format(e))
        sys.exit(1)

    try:
        httpd.serve_forever()
    except BaseException as e:
        logging.info('Exception while serving: {}'.format(e))

    logging.warning('Exiting.')

#----------------------
if __name__ == '__main__':
    main()