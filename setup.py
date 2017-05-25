from setuptools import setup

setup(
    name='ttsserver',
    version="0.1.7",
    packages=['ttsserver'],
    description=('Hanson Robotics TTS Server.'),
    url='https://github.com/hansonrobotics/ttsserver',
    author='Wenwei Huang',
    author_email='wenwei@hansonrobotics.com',
    install_requires=[
        'flask',
    ],
    entry_points={
        'console_scripts': ['run_tts_server=ttsserver.run_server:main']
    },
)
