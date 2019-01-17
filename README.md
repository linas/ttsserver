# Run TTS Server

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

# Call TTS Server

## Using curl

`curl "http://<host>:<port>/v1.0/tts?emotion=happy&text=hello&voice=audrey&vendor=cereproc"`
##### Copyright (c) 2013-2019 Hanson Robotics, Ltd. 
