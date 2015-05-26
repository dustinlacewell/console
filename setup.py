from setuptools import setup

setup(
    name='docker-console',
    version='0.1.0',
    packages=[
        'console',
        'console.widgets',
        'console.ui',
        'console.ui.images',
        'console.ui.containers',
    ],
    scripts=['bin/docker-console'],
    install_requires=['docker-py', 'urwid', 'twisted', 'attrdict', 'click'],
    provides=['console'],
    author="Dustin Lacewell",
    author_email="dlacewell@gmail.com",
    url="https://github.com/dustinlacewell/console",
    description="A curses interface for Docker.",
    long_description=open("README.md", 'r').read(),
)
