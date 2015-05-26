import urwid

from console.ui.images.pane import ImagePane
from console.ui.containers.pane import ContainerPane
from console.widgets.tabs import Tab, TabFrame
from console.modes import modemap


class ImagesTab(Tab):
    label = "images"
    mode = {
        'ctrl n': ('next-image', 'select the next image'),
        'ctrl p': ('prev-image', 'select the previous image'),
        'ctrl d': ('delete-image', 'delete the selected image'),
        'ctrl h': ('view-history', 'view history of selected image'),
        'ctrl a': ('toggle-show-all', 'toggle whether all image layers are shown'),
        'ctrl t': ('tag-image', 'tag the selected image'),
        'ctrl u': ('push-image', 'push the selected image'),
        'ctrl v': ('inspect-details', 'inspect the selected image'),
    }

    def get_content(self):
        return ImagePane()


class ContainersTab(Tab):
    label = "containers"
    mode = {
        'ctrl n': ('next-container', 'select the next container'),
        'ctrl p': ('prev-container', 'select the previous container'),
        'ctrl d': ('delete-container', 'delete the selected container'),
        'ctrl a': ('toggle-show-all', 'toggle whether all containers are shown'),
        'ctrl t': ('commit-container', 'commit the selected container'),
        'ctrl v': ('inspect-details', 'inspect the selected container'),
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



