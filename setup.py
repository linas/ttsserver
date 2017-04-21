from setuptools import setup

setup(
    name='ttsserver',
    version="0.1.0",
    packages=['ttsserver', 'ttsserver.api'],
    description=('Hanson Robotics TTS Server.'),
    url='https://github.com/hansonrobotics/ttsserver',
    author='Wenwei Huang',
    author_email='wenwei@hansonrobotics.com',
    install_requires=[
        'flask',
    ],
)
