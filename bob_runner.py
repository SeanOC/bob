import signal
from daemon import DaemonContext
from daemon.runner import DaemonRunner, make_pidlockfile

class BobRunner(DaemonRunner):
    
    def __init__(self, *args, **kwargs):
        super(BobRunner, self).__init__(*args, **kwargs)
        self.daemon_context.signal_map = {
            signal.SIGTERM: self.app.stop
        }