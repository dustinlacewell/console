import docker

from console.app import app
from console.widgets.dialogs import MessageBox


def popup_failure(e, self):
    self.close_dialog()

    e.trap(docker.errors.APIError)
    e = e.value
    self.show_dialog(
        MessageBox(
            e.explanation,
            title="HTTP Error: " + str(e.response.status_code),
        )
    )
    app.draw_screen()


def catch_docker_errors(fn):
    def decorator(self, *args, **kwargs):
        try:
            d = fn(self, *args, **kwargs)
            d.addErrback(popup_failure, self)
        except docker.errors.APIError, e:
            popup_failure(e, self)
    return decorator


def split_repo_name(name):
    for idx in range(len(name)):
        c = name[-idx]
        if c == ':':
            return name[:-idx], name[-idx + 1:]
        elif c == '/':
            return name, ''
    return name, None


class Bag(object):
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


