'''
    Serves files, such as images, from a local directory.

    2019-22 Benjamin Kellenberger
'''

import os
from io import BytesIO
from bottle import static_file, request, abort, _file_iter_range, parse_range_header, HTTPResponse
from util.cors import enable_cors
from util import helpers
from util.drivers import GDALImageDriver        #TODO


class FileServer():

    def __init__(self, config, app, dbConnector, verbose_start=False):
        self.config = config
        self.app = app

        if verbose_start:
            print('FileServer'.ljust(helpers.LogDecorator.get_ljust_offset()), end='')

        if not helpers.is_fileServer(config):
            if verbose_start:
                helpers.LogDecorator.print_status('fail')
            raise Exception('Not a valid FileServer instance.')
        
        self.login_check = None
        try:
            self.staticDir = self.config.getProperty('FileServer', 'staticfiles_dir')
            self.staticAddressSuffix = self.config.getProperty('FileServer', 'staticfiles_uri_addendum', type=str, fallback='').strip()

            assert GDALImageDriver.init_is_available()  #TODO

            self._initBottle()
        except Exception as e:
            if verbose_start:
                helpers.LogDecorator.print_status('fail')
            raise Exception(f'Could not launch FileServer (message: "{str(e)}").')

        if verbose_start:
            helpers.LogDecorator.print_status('ok')

    
    def loginCheck(self, project=None, admin=False, superuser=False, canCreateProjects=False, extend_session=False):
        return self.login_check(project, admin, superuser, canCreateProjects, extend_session)


    def addLoginCheckFun(self, loginCheckFun):
        self.login_check = loginCheckFun


    def _initBottle(self):

        ''' static routing to files '''
        @enable_cors
        @self.app.route(os.path.join('/', self.staticAddressSuffix, '/<project>/files/<path:path>'))
        def send_file(project, path):
            window = request.params.get('window', None)
            if window is not None:
                # load from disk and crop
                if isinstance(window, str):
                    window = [int(w) for w in window.strip().split(',')]
                filePath = os.path.join(self.staticDir, project, path)
                bytes = GDALImageDriver.disk_to_bytes(filePath, window=window)
                clen = len(bytes)

                headers = {}
                # headers['Content-type'] = 'image/tiff'        #TODO
                
                ranges = request.environ.get('HTTP_RANGE')
                if 'HTTP_RANGE' in request.environ:
                    # need to send bytes in chunks
                    fhandle = BytesIO(bytes)
                    ranges = list(parse_range_header(request.environ['HTTP_RANGE'], clen))
                    offset, end = ranges[0]
                    headers['Content-Range'] = f'bytes {offset}-{end-1}/{clen}'
                    headers['Content-Length'] = str(end-offset)
                    fhandle = _file_iter_range(fhandle, offset, end-offset)
                    return HTTPResponse(fhandle, status=206, **headers)

                return bytes

            else:
                # full image; return static file directly
                return static_file(path, root=os.path.join(self.staticDir, project))


        @enable_cors
        @self.app.get('/getFileServerInfo')
        def get_file_server_info():
            '''
                Returns immutable parameters like the file directory
                and address suffix.
                User must be logged in to retrieve this information.
            '''
            if not self.loginCheck(extend_session=True):
                abort(401, 'forbidden')
            
            return {
                'staticfiles_dir': self.staticDir,
                'staticfiles_uri_addendum': self.staticAddressSuffix
            }