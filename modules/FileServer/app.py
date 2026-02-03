'''
    Serves files, such as images, from a local directory.

    2019-24 Benjamin Kellenberger
'''

import os
from io import BytesIO
from bottle import static_file, request, abort, parse_range_header, HTTPResponse

from util.cors import enable_cors
from util import helpers
from util.logDecorator import LogDecorator
from util.drivers import is_web_compatible, GDALImageDriver
from ..module import Module


def _file_iter_range(fp, offset, bytes_to_read, maxread=1024*1024):
    """
    Yield chunks from a file-like object, implementing HTTP range request support.
    This replaces the removed bottle._file_iter_range private API.

    Args:
        fp: File-like object to read from
        offset: Byte offset to start reading from
        bytes_to_read: Number of bytes to read
        maxread: Maximum chunk size (default 1MB)
    """
    fp.seek(offset)
    while bytes_to_read > 0:
        part = fp.read(min(bytes_to_read, maxread))
        if not part:
            break
        bytes_to_read -= len(part)
        yield part



class FileServer(Module):
    '''
        File server module, responsible for project as well as static data (images, etc.).
    '''
    DEFAULT_IMAGE_KWARGS = {
        'driver': 'GTiff',
        'compress': 'lzw'
    }
    DEFAULT_IMAGE_MIME_TYPE = 'image/tiff'

    def __init__(self,
                 config,
                 app,
                 db_connector,
                 user_handler,
                 task_coordinator,
                 verbose_start=False,
                 passive_mode=False) -> None:
        super().__init__(config,
                         app,
                         db_connector,
                         user_handler,
                         task_coordinator,
                         verbose_start,
                         passive_mode)

        if verbose_start:
            print('FileServer'.ljust(LogDecorator.get_ljust_offset()), end='')

        if not helpers.is_file_server(config):
            if verbose_start:
                LogDecorator.print_status('fail')
            raise Exception('Not a valid FileServer instance.')

        self.login_check_fun = None
        try:
            self.static_dir = self.config.get_property('FileServer', 'staticfiles_dir')
            self.static_address_suffix = self.config.get_property('FileServer',
                                                                  'staticfiles_uri_addendum',
                                                                  dtype=str,
                                                                  fallback='').strip()

            assert GDALImageDriver.init_is_available()  #TODO

            self._initBottle()
        except Exception as exc:
            if verbose_start:
                LogDecorator.print_status('fail')
            raise Exception(f'Could not launch FileServer (message: "{str(exc)}").') from exc

        if verbose_start:
            LogDecorator.print_status('ok')


    def _initBottle(self):

        ''' static routing to files '''
        @enable_cors
        @self.app.route(os.path.join('/', self.static_address_suffix, '/<project>/files/<path:path>'))
        def send_file(project, path):
            file_path = os.path.join(self.static_dir, project, path)
            need_conversion = not is_web_compatible(file_path)
            window = request.params.get('window', None)
            max_size = request.params.get('maxsize', None)
            if isinstance(max_size, str):
                max_size = [int(val) for val in max_size.strip().split(',')]
            bands = request.params.get('bands', None)
            if need_conversion or window is not None or bands is not None:
                # load from disk and crop
                driver_kwargs = {}
                if isinstance(window, str):
                    window = [int(w) for w in window.strip().split(',')]
                    driver_kwargs['window'] = window
                if isinstance(bands, str):
                    bands = [int(band) for band in bands.strip().split(',')]
                    driver_kwargs['bands'] = bands
                #TODO
                driver_kwargs['max_size'] = max_size

                # check if file needs conversion
                if need_conversion:
                    driver_kwargs.update(self.DEFAULT_IMAGE_KWARGS)

                bytes_arr = GDALImageDriver.disk_to_bytes(file_path, **driver_kwargs)
                clen = len(bytes_arr)

                headers = {}
                # headers['Content-type'] = mime_type
                headers['Content-Disposition'] = f'attachment; filename="{path}"'

                ranges = request.environ.get('HTTP_RANGE')
                if 'HTTP_RANGE' in request.environ:
                    # need to send bytes in chunks
                    fhandle = BytesIO(bytes_arr)
                    ranges = list(parse_range_header(request.environ['HTTP_RANGE'], clen))
                    offset, end = ranges[0]
                    headers['Content-Range'] = f'bytes {offset}-{end-1}/{clen}'
                    headers['Content-Length'] = str(end-offset)
                    fhandle = _file_iter_range(fhandle, offset, end-offset)
                    return HTTPResponse(fhandle, status=206, **headers)

                return HTTPResponse(bytes_arr, status=200, **headers)

            # full image; return static file directly
            #TODO: only go this route if fully-supported image (i.e., parseable by client)
            return static_file(path, root=os.path.join(self.static_dir, project))


        @enable_cors
        @self.app.get('/getFileServerInfo')
        def get_file_server_info():
            '''
                Returns immutable parameters like the file directory
                and address suffix.
                User must be logged in to retrieve this information.
            '''
            if not self.login_check(extend_session=True):
                abort(401, 'forbidden')

            return {
                'staticfiles_dir': self.static_dir,
                'staticfiles_uri_addendum': self.static_address_suffix
            }
