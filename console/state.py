from datetime import datetime

import docker
import urwid

from twisted.internet import reactor, threads

class ContainerMonitor(object):
    def __init__(self, client, frequency=1, all=False):
        self.client = client
        self.frequency = frequency
        self.all = False
        urwid.register_signal(ContainerMonitor, 'container-list')

    def process_containers(self, container_data):
        containers = []
        for container in container_data:
            created = datetime.fromtimestamp(container['Created'])
            now = datetime.now()
            containers.append({
                'age': (now - created).days,
                'id': container['Id'],
                'image': container['Image'],
                'names': container['Names'],
                'status': container['Status'],
                'command': container['Command'],
            })
        containers.sort(key=lambda x: (x['age'], x['image'], x['status']))
        return containers

    def emit_containers(self, containers):
        urwid.emit_signal(self, 'container-list', containers)
        reactor.callLater(self.frequency, self.get_containers)
        return containers

    def get_containers(self):
        d = threads.deferToThread(self.client.containers, all=self.all)
        d.addCallback(self.process_containers)
        d.addCallback(self.emit_containers)
        return d


class ImageMonitor(object):
    def __init__(self, client, frequency=1, all=False):
        self.client = client
        self.frequency = frequency
        self.all = False
        urwid.register_signal(ImageMonitor, 'image-list')

    def process_images(self, image_data):
        images = []
        for image in image_data:
            created = datetime.fromtimestamp(image['Created'])
            now = datetime.now()
            time_diff = now - created
            id = image['Id']
            for tag in image['RepoTags']:
                images.append({
                    'id': id,
                    'tag': tag,
                    'days_old': time_diff.days,
                })

        images.sort(key=lambda x: (x['days_old'], x['tag'], x['id']))
        return images

    def emit_images(self, images):
        urwid.emit_signal(self, 'image-list', images)
        reactor.callLater(self.frequency, self.get_images)
        return images

    def get_images(self):
        d = threads.deferToThread(self.client.images, all=self.all)
        d.addCallback(self.process_images)
        d.addCallback(self.emit_images)
        return d


class DockerState(object):

    def __init__(self, host, version, frequency):
        self.host = host
        self.version = version
        self.client = docker.Client(base_url=host, version=version)
        self.frequency = frequency
        self.images = ImageMonitor(self.client)
        self.images.get_images()
        self.containers = ContainerMonitor(self.client)
        self.containers.get_containers()

