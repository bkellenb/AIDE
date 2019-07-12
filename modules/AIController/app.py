'''
    Main Bottle and routings for the AIController instance.

    2019 Benjamin Kellenberger
'''

from bottle import post, request, response, abort
from modules.AIController.backend.middleware import AIMiddleware


class AIController:

    def __init__(self, config, app):
        self.config = config
        self.app = app

        self.middleware = AIMiddleware(config)

        self.login_check = None

        self._initBottle()


    def loginCheck(self, needBeAdmin=False):
        return True if self.login_check is None else self.login_check(needBeAdmin)


    def addLoginCheckFun(self, loginCheckFun):
        self.login_check = loginCheckFun


    def _initBottle(self):
        
        @self.app.post('/startTraining')
        def start_training():
            '''
                Manually request AIController to train the model.
                This still only works if there is no training process ongoing.
                Otherwise the request is aborted.
            '''
            if self.loginCheck(True):
                try:
                    status = self.middleware.start_training(minTimestamp='lastState', distributeTraining=True) #TODO
                except Exception as e:
                    status = str(e)
                return { 'status' : status }

            else:
                abort(401, 'unauthorized')

        
        @self.app.post('/startInference')
        def start_inference():
            '''
                TODO: just here for debugging purposes; in reality inference should automatically be called after training
            '''
            if self.loginCheck(True):
                status = self.middleware.start_inference(forceUnlabeled=True, maxNumImages=None, maxNumWorkers=1)
                return { 'status' : status }
            
            else:
                abort(401, 'unauthorized')


        @self.app.get('/status')
        def check_status():
            '''
                Queries the middleware for any ongoing training worker processes
                and returns the stati of each in a dict.
            '''
            if self.loginCheck(False):
                try:
                    queryProject = 'project' in request.query
                    queryTasks = 'tasks' in request.query
                    queryWorkers = 'workers' in request.query
                    status = self.middleware.check_status(queryProject, queryTasks, queryWorkers)
                except Exception as e:
                    status = str(e)
                return { 'status' : status }

            else:
                abort(401, 'unauthorized')