#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import sys
import logging
import datetime as dt

CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(CWD, '..'))

from flask import Flask, request, Response
import json
import wave
import base64

app = Flask(__name__)
json_encode = json.JSONEncoder().encode
logger = logging.getLogger('hr.tts.server')

SERVER_LOG_DIR=os.path.expanduser('~/.hr/ttsserver/log')
if not os.path.isdir(SERVER_LOG_DIR):
    os.makedirs(SERVER_LOG_DIR)
LOG_CONFIG_FILE = '{}/ttsserver_{}.log'.format(SERVER_LOG_DIR,
                                            dt.datetime.strftime(dt.datetime.now(), '%Y%m%d%H%M%S'))
link_log_fname = os.path.join(SERVER_LOG_DIR, 'ttsserver_latest.log')
if os.path.islink(link_log_fname):
    os.unlink(link_log_fname)
os.symlink(LOG_CONFIG_FILE, link_log_fname)
fh = logging.FileHandler(LOG_CONFIG_FILE)
sh = logging.StreamHandler()
formatter = logging.Formatter(
    '[%(name)s][%(levelname)s] %(asctime)s: %(message)s')
fh.setFormatter(formatter)
sh.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(fh)
root_logger.addHandler(sh)

VOICES = {}

def load_voices(voice_path):
    if os.path.isdir(voice_path):
        sys.path.insert(0, voice_path)
        module_names = [f for f in os.listdir(voice_path) if f.endswith('.py')]
        for py_module in module_names:
            try:
                module = __import__(py_module[:-3])
                if hasattr(module, 'voices'):
                    VOICES.update(module.voices)
            except ImportError as ex:
                logger.error(ex)

VERSION = 'v1.0'
ROOT = '/{}'.format(VERSION)

def get_api(vendor, voice):
    api = None
    try:
        api = VOICES.get(vendor).get(voice)
    except Exception:
        logger.error("Can't get api {}:{}".format(vendor, voice))
    return api

@app.route(ROOT + '/tts')
def _tts():
    logger.info("Start TTS")
    vendor = request.args.get('vendor')
    voice = request.args.get('voice')
    text = request.args.get('text')
    response = {}
    api = get_api(vendor, voice)
    if api:
        tts_data = api.tts(text)
        response['phonemes'] = tts_data.phonemes
        response['markers'] = tts_data.markers
        response['words'] = tts_data.words
        response['duration'] = tts_data.get_duration()
        response['nodes'] = tts_data.get_nodes()
        if tts_data.wavout:
            logger.info("TTS file {}".format(tts_data.wavout))
            try:
                f = wave.open(tts_data.wavout, 'rb')
                data = f.readframes(f.getnframes())
                response['data'] = base64.b64encode(data)
                response['params'] = f.getparams()
            except Exception as ex:
                logger.error(ex)
                f = None
            finally:
                if f:
                    f.close()
                if not keep_audio and os.path.isfile(tts_data.wavout):
                    os.remove(tts_data.wavout)
                    logger.info("Removed file {}".format(tts_data.wavout))
    else:
        response['error'] = "Can't get api"
        logger.error("Can't get api {}:{}".format(vendor, voice))
    logger.info("End TTS")
    return Response(json_encode({'response': response}),
                    mimetype='application/json')

@app.route(ROOT + '/ping', methods=['GET'])
def _ping():
    return Response(json_encode({'response': {'code': 0, 'message': 'pong'}}),
                    mimetype="application/json")

def main():
    import argparse
    parser = argparse.ArgumentParser('HR TTS Server')

    parser.add_argument(
        '-p, --port',
        dest='port', default=10001, help='Server port')
    parser.add_argument(
        '--keep-audio',
        dest='keep_audio', action='store_true',
        help='Whether or not keep tts audio on server')
    parser.add_argument(
        '--tts-output-dir',
        dest='tts_output_dir', default='~/.hr/ttsserver', help='Server port')
    parser.add_argument(
        '--voice_path', required=True, dest='voice_path', help='Voice path')

    option = parser.parse_args()

    keep_audio = option.keep_audio
    tts_output_dir = os.path.expanduser(option.tts_output_dir)

    load_voices(option.voice_path)

    for name, engine in VOICES.items():
        for voice in engine.values():
            voice.set_output_dir(os.path.join(tts_output_dir, name))

    app.run(host='0.0.0.0', debug=False, use_reloader=False, port=option.port)

if __name__ == '__main__':
    main()
