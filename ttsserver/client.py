#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import requests
import base64
import logging

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 10001

logger = logging.getLogger('hr.ttserver.client')

class TTSResponse(object):

    def __init__(self):
        self.response = None
        self.params = {}

    def get_duration(self):
        if self.response:
            return self.response.get('duration', 0)
        return 0

    def write(self, wavfile):
        if self.response:
            data = self.response['data']
            data = base64.b64decode(data)
            try:
                with open(wavfile, 'wb') as f:
                    f.write(data)
                logger.info("Write to file {}".format(wavfile))
                return True
            except Exception as ex:
                logger.error(ex)
                f = None
            finally:
                if f:
                    f.close()
        else:
            logger.error("No data to write")
        return False

    def __repr__(self):
        return "<TTSResponse params {}, duration {}>".format(
            self.params, self.get_duration())

class Client(object):

    VERSION = 'v1.0'

    def __init__(self, host=None, port=None):
        self.host = host or DEFAULT_HOST
        self.port = port or DEFAULT_PORT
        self.root_url = 'http://{}:{}/{}'.format(self.host, self.port, Client.VERSION)

    def tts(self, text, **kwargs):
        params = {
            'text': text,
        }
        params.update(kwargs)
        timeout = kwargs.get('timeout')
        result = TTSResponse()
        try:
            r = requests.get(
                '{}/tts'.format(self.root_url), params=params, timeout=timeout)
            if r.status_code == 200:
                response = r.json().get('response')
                result.response = response
                result.params = params
            else:
                logger.error("Error code: {}".format(r.status_code))
        except Exception as ex:
            logger.error("TTS Error {}".format(ex))
        return result

    def asynctts(self, text, callback, **kwargs):
        pass

    def ping(self):
        try:
            r = requests.get('{}/ping'.format(self.root_url))
            response = r.json().get('response')
            if response['message'] == 'pong':
                return True
        except Exception:
            return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    client = Client()
    result = client.tts('test', vendor='cereproc', voice='audrey')
    visemes = result.response['visemes']
    print visemes
    result.write('test.wav')
    client.tts('hello hello hello', vendor='cereproc', voice='katherine', emotion='sad', chunk_size=512, semitones=-2).write('happy.wav')
    client.tts('hello hello hello', vendor='cereproc', voice='katherine', emotion='sad').write('sad.wav')
    client.tts('hello hello hello', vendor='cereproc', voice='katherine', emotion='afraid').write('afraid.wav')
    client.tts('hello hello hello', vendor='cereproc', voice='giles', emotion='happy_tensed').write('happy_tensed.wav')
    client.tts('hello', vendor='cereproc', voice='giles').write('hello2.wav')
    client.tts('hi<mark name="mark_hello"/>hello', vendor='cereproc', voice='giles').write('hello3.wav')
    client.tts('你好', vendor='iflytek', voice='xiaoyan').write('hello4.wav')
    client.tts('你好', vendor='baidu', voice='male', spd=7, pit=9, aa=2).write('hello5.wav')
    import os
    os.system('aplay hello4.wav')
    os.system('aplay hello5.wav')
