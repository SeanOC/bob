import signal
from daemon import DaemonContext
from daemon.runner import DaemonRunner, make_pidlockfile

class BobRunner(DaemonRunner):
    
    def __init__(self, *args, **kwargs):
        super(BobRunner, self).__init__(*args, **kwargs)
        self.daemon_context.signal_map = {
            signal.SIGTERM: self.app.stop
        }
    
    '''
    def _start(self):
        super(BobRunner, self)._start()
        
    def _restart(self):
        super(BobRuner, self)._restart()
    
    def _stop(self):
        self.app.stop()
        super(BobRunner, self)._stop()
        
    action_funcs = {
        'start': _start,
        'stop': _stop,
        'restart': _restart,
        }'''