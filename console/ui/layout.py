import urwid

from console.ui.images.pane import ImagePane
from console.ui.containers.pane import ContainerPane
from console.widgets.tabs import Tab, TabFrame
from console.modes import modemap


class ImagesTab(Tab):
    label = "images"
    mode = {
        'ctrl n': ('next-image', 'set focus on the next image'),
        'ctrl p': ('prev-image', 'set focus on the previous image'),
        'ctrl d': ('delete-image', 'delete the selected image(s)'),
        'ctrl y': ('view-history', 'view history of selected image'),
        'ctrl a': ('toggle-show-all', 'toggle whether all image layers are shown'),
        'ctrl t': ('tag-image', 'tag the selected image'),
        'ctrl b': ('push-image', 'push the selected image'),
        'ctrl v': ('inspect-details', 'inspect the selected image'),
        'ctrl k': ('set-mark', 'select current image'),
        'ctrl u': ('unmark-images', 'unmark all selected images'),
        'ctrl l': ('pull-image', 'pull image from repository'),
    }

    def get_content(self):
        return ImagePane()


class ContainersTab(Tab):
    label = "containers"
    mode = {
        'ctrl n': ('next-container', 'set focus on the next container'),
        'ctrl p': ('prev-container', 'set focus on the previous container'),
        'ctrl d': ('delete-container', 'delete the selected container(s)'),
        'ctrl a': ('toggle-show-all', 'toggle whether all containers are shown'),
        'ctrl t': ('commit-container', 'commit the selected container'),
        'ctrl v': ('inspect-details', 'inspect the selected container'),
        'ctrl k': ('set-mark', 'select current container'),
        'ctrl r': ('run-container(s)', 'run the selected container(s) in screen or tmux'), 
        'ctrl u': ('unmark-containers', 'unmark all selected containers'),
        'ctrl e': ('rename-container', 'rename the selected container'),
        'ctrl f': ('inspect-changes', 'inspect changes on container filesystem'),
        'ctrl g': ('restart-container', 'restart the selected container'),
        'ctrl l': ('kill-container', 'kill the selected container'),
        'ctrl x': ('pause-container', 'pause the selected container'),
        'ctrl o': ('unpause-container', 'unpause the selected container'),
        'ctrl w': ('start-container', 'start the selected container'),
        'ctrl y': ('stop-container', 'stop the selected container'),
        'shift tab': ('top-container', 'display running processes'),
    }

    def get_content(self):
        return ContainerPane()


class InfoTab(Tab):
    label = "info"


class RootFrame(TabFrame):
    """
    The main frame of the application. It contains the tab header and the main
    content pane. Flipping through the tabs should cycle the content pane with
    the content of each respective tab content.
    """
    def __init__(self):
        tabs = (ContainersTab(), ImagesTab(),)
        TabFrame.__init__(self, tabs)

    def make_header(self, tabs):
        """
        Generate the frame header.
        """
        columns = urwid.Columns([])
        columns.title = urwid.Text("docker-console 0.1.0")
        columns.tabs = TabFrame.make_header(self, tabs)

        columns.contents = [
            (columns.title, columns.options('weight', 1)),
            (columns.tabs, columns.options('weight', 2)),
        ]

        return columns



