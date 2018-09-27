#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import sys
import logging
import datetime as dt
import subprocess
from collections import defaultdict
import xml.etree.ElementTree as ET
CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(CWD, '..'))

from flask import Flask, request, Response
import json
import wave
import time
import base64
import shutil

try:
    import colorlog
except ImportError:
    pass

app = Flask(__name__)
json_encode = json.JSONEncoder().encode
logger = logging.getLogger('hr.tts.server')

SERVER_LOG_DIR = os.path.expanduser('~/.hr/log/ttsserver')
TTS_TMP_OUTPUT_DIR = os.path.expanduser('~/.hr/ttsserver/tmp')
DEFAULT_TTS_OUTPUT_DIR = os.path.expanduser('~/.hr/ttsserver')
if os.path.isdir(TTS_TMP_OUTPUT_DIR):
    shutil.rmtree(TTS_TMP_OUTPUT_DIR)
if not os.path.isdir(TTS_TMP_OUTPUT_DIR):
    os.makedirs(TTS_TMP_OUTPUT_DIR)
VOICES = {}
KEEP_AUDIO = False
counter = 0

def next_count():
    global counter
    counter += 1
    return str(counter).zfill(4)

def init_logging():
    run_id = None
    try:
        run_id = subprocess.check_output(
            'rosparam get /run_id'.split(), stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as ex:
        run_id = None
    except OSError as ex:
        run_id = None
    ROS_LOG_DIR = os.environ.get('ROS_LOG_DIR', os.path.expanduser('~/.hr/log'))
    server_log_dir = SERVER_LOG_DIR
    if run_id is not None:
        server_log_dir = os.path.join(ROS_LOG_DIR, run_id, 'ttsserver')
    if not os.path.isdir(server_log_dir):
        os.makedirs(server_log_dir)
    log_config_file = '{}/{}.log'.format(server_log_dir,
                                                dt.datetime.strftime(dt.datetime.utcnow(), '%Y%m%d%H%M%S'))
    link_log_fname = os.path.join(server_log_dir, 'latest.log')
    if os.path.islink(link_log_fname):
        os.unlink(link_log_fname)
    os.symlink(log_config_file, link_log_fname)
    formatter = logging.Formatter(
        '[%(name)s][%(levelname)s] %(asctime)s: %(message)s')
    fh = logging.FileHandler(log_config_file)
    fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    if 'colorlog' in sys.modules and os.isatty(2):
        cformat = '%(log_color)s' + formatter._fmt
        formatter = colorlog.ColoredFormatter(
            cformat,
            log_colors={
                'DEBUG':'reset',
                'INFO': 'reset',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
    sh.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(fh)
    root_logger.addHandler(sh)

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
    params = request.args.to_dict()
    for p in ['vendor', 'voice', 'text']:
        params.pop(p)
    response = {}
    api = get_api(vendor, voice)
    if api:
        tts_data = api.tts(text, **params)
        if tts_data is None:
            response['error'] = "No TTS data"
            logger.error("No TTS data {}:{}".format(vendor, voice))
        else:
            response['phonemes'] = tts_data.phonemes
            response['markers'] = tts_data.markers
            response['words'] = tts_data.words
            response['visemes'] = tts_data.visemes
            response['duration'] = tts_data.get_duration()
            response['nodes'] = tts_data.get_nodes()
            if tts_data.wavout:
                logger.info("TTS file {}".format(tts_data.wavout))
                try:
                    with open(tts_data.wavout, 'rb') as f:
                        raw = f.read()
                        response['data'] = base64.b64encode(raw)
                    f = wave.open(tts_data.wavout, 'rb')
                    response['params'] = f.getparams()
                except Exception as ex:
                    logger.error(ex)
                    f = None
                finally:
                    if f:
                        f.close()
                    if os.path.isfile(tts_data.wavout):
                        timestamp = time.time()
                        num = next_count()
                        notags = None
                        try:
                            root = u'<_root_>{}</_root_>'.format(text)
                            tree = ET.fromstring(root.encode('utf-8'))
                            notags = ET.tostring(tree, encoding='utf8', method='text')
                            notags = notags.strip()
                            if len(notags) > 200:
                                notags = notags[:200]+'...' # prevent filename too long(255)
                            tmp_file = '{}-{} - {}.wav'.format(num, timestamp, notags)
                        except Exception as ex:
                            logger.error(ex)
                            tmp_file = '{}-{} - {}.wav'.format(num, timestamp, os.path.splitext(
                                os.path.basename(tts_data.wavout))[0])
                        tmp_file = os.path.join(TTS_TMP_OUTPUT_DIR, tmp_file)
                        try:
                            if notags:
                                shutil.copy(tts_data.wavout, tmp_file)
                        except IOError as err:
                            logger.error(err)
                        if not KEEP_AUDIO:
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
    init_logging()
    cwd = os.path.dirname(os.path.realpath(__file__))
    import argparse
    parser = argparse.ArgumentParser('HR TTS Server')

    parser.add_argument(
        '-p, --port',
        dest='port', default=10001, help='Server port', type=int)
    parser.add_argument(
        '--keep-audio',
        dest='keep_audio', action='store_true',
        help='Whether or not keep tts audio on server')
    parser.add_argument(
        '--tts-output-dir',
        dest='tts_output_dir', default=DEFAULT_TTS_OUTPUT_DIR,
        help='TTS wave data save directory')
    parser.add_argument(
        '--voice_path', default=os.path.join(cwd, 'api'), dest='voice_path',
        help='Voice path')

    option = parser.parse_args()

    global KEEP_AUDIO
    KEEP_AUDIO = option.keep_audio
    tts_output_dir = os.path.expanduser(option.tts_output_dir)

    load_voices(option.voice_path)
    if len(VOICES) == 0:
        logger.warn("No any voice is loaded")

    for name, engine in VOICES.items():
        for voice in engine.values():
            voice.set_output_dir(os.path.join(tts_output_dir, name))

    app.run(host='0.0.0.0', debug=False, use_reloader=False, port=option.port)

if __name__ == '__main__':
    main()
