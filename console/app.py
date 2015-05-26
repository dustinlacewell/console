import urwid

import docker

from zope.interface import Interface, Attribute
from twisted.python.components import proxyForInterface

from console.palette import palette
from console.state import DockerState

class IEventLoop(Interface):
    screen = Attribute("")
    event_loop = Attribute("")
    widget = Attribute("")

    def draw_screen(self):
        pass

    def entering_idle(self):
        pass

    def input_filter(self, keys, raw):
        pass

    def process_input(self, keys):
        pass

    def remove_alarm(self, handle):
        pass

    def remove_watch_file(self, handle):
        pass

    def remove_watch_pipe(self, write_fd):
        pass

    def run(self, ):
        pass

    def set_alarm_at(self, tm, callback, user_data=None):
        pass

    def set_alarm_in(self, sec, callback, user_data=None):
        pass

    def start(self, ):
        pass

    def stop(self, ):
        pass

    def unhandled_input(self, input):
        pass

    def watch_file(self, fd, callback):
        pass

    def watch_pipe(self, callback):
        pass


class ConsoleApp(proxyForInterface(IEventLoop)):
    def __init__(self):
        self.options = None
        self.client = None
        self.root = None
        self.state = None

    def init(self, options, root_cls):
        self.state = DockerState(options.host, '1.18', options.freq)
        self.client = docker.Client(base_url=options.host, version='1.18')
        self.options = options
        self.root = root_cls()
        event_loop = urwid.TwistedEventLoop(manage_reactor=True)
        loop = urwid.MainLoop(
            self.root,
            palette=palette,
            event_loop=event_loop,
        )
        super(ConsoleApp, self).__init__(loop)


app = ConsoleApp()
