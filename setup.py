from setuptools import setup

setup(
    name='ttsserver',
    version="0.2.0",
    packages=['ttsserver', 'ttsserver.espp'],
    description=('Hanson Robotics TTS Server.'),
    url='https://github.com/hansonrobotics/ttsserver',
    author='Wenwei Huang',
    author_email='wenwei@hansonrobotics.com',
    install_requires=[
        'flask',
        'sox>=1.2.9',
        'pysptk>=0.1.4',
        'numpy',
        'scipy',
    ],
    entry_points={
        'console_scripts': ['run_tts_server=ttsserver.server:main']
    },
)
