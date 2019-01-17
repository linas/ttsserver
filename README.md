# Text to Speech Server

This is a server that can provide audio output for text input, using any one
of several different systems, including the CMU Festival system and Cereproc.

This does not include voices.

This is a basic server; it does not offer any means of syncing sound to animation.
There's minimal (i.e. no) control for timing, articulation, intonation, rhythm.

## Run TTS Server

```bash
usage: HR TTS Server [-h] [-p, --port PORT] [--keep-audio]
                     [--tts-output-dir TTS_OUTPUT_DIR]
                     [--voice_path VOICE_PATH]

optional arguments:
  -h, --help            show this help message and exit
  -p, --port PORT       Server port
  --keep-audio          Whether or not keep tts audio on server
  --tts-output-dir TTS_OUTPUT_DIR
                        TTS wave data save directory
  --voice_path VOICE_PATH
                        Voice path
```

## Call TTS Server

### Call TTS using curl

`curl "http://<host>:<port>/v1.0/tts?emotion=happy&text=hello&voice=audrey&vendor=cereproc"`

## Status
As of 2019, this is in acttive use for various Hanson Robotics demos.

##### Copyright (c) 2017-2019 Hanson Robotics, Ltd. 
