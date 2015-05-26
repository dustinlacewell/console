docker-console
==============

A curses interface for Docker


installing
----------

    git clone https://github.com/dustinlacewell/console.git
    cd console
    python setup.py install

building with Docker
-------------------

    git clone https://github.com/dustinlacewell/console.git
    cd console
    docker build -t console
    docker run -it -v /var/run/docker.sock:/var/run/docker.sock console

running with Docker from index
------------------------------

    docker pull dlacewell/console
    docker run -it -v /var/run/docker.sock:/var/run/docker.sock console

supported environment variables
-------------------------------

    * DOCKERD_URL : Path to dockerd socket or remote api url
    * DOCKERD_VERSION : Version of remote api to use


usage
-----

docker-console is a curses-like interface with interacting with a docker daemon. When it loads, you will be presented with an interface that lists your local Docker containers. At the top right, you can see the currently selected tab.

You can press '?' to view a list of the available key bindings for the current screen.
