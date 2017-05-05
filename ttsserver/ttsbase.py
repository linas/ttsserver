# -*- coding: utf-8 -*-

from __future__ import division
import os
import re
import logging
import hashlib
import pinyin
from scipy.io import wavfile
import shutil
import yaml
import xml.etree.ElementTree
import uuid

from audio2phoneme import audio2phoneme

CWD = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('hr.ttsserver.ttsbase')

# User data class to store information
class TTSData:
    def __init__(self, text=None, wavout=None):
        self.text = text
        self.wavout = wavout
        self.phonemes = []
        self.markers = []
        self.words = []

    def get_duration(self):
        if os.path.isfile(self.wavout):
            rate, data = wavfile.read(self.wavout)
            duration = data.shape[0]/rate
        else:
            duration = 0
        return duration

    def get_nodes(self):
        typeorder = {'marker': 1, 'word': 2, 'phoneme': 3}
        items = self.markers+self.words+self.phonemes
        items = sorted(items, key=lambda x: (x['start'], typeorder[x['type']]))
        return items

    def __repr__(self):
        return "<TTSData wavout {}, text {}>".format(self.wavout, self.text)

class TTSException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class TTSBase(object):
    def __init__(self):
        self.output_dir = '.'

    def set_output_dir(self, output_dir):
        self.output_dir = os.path.expanduser(output_dir)
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

    def get_tts_session_params(self):
        raise NotImplementedError("get_tts_session_params is not implemented")

    def set_voice(self, voice):
        raise NotImplementedError("set_voice is not implemented")

    def do_tts(self, tts_data):
        raise NotImplementedError("_tts is not implemented")

    def tts(self, text, wavout=None):
        try:
            if wavout is None:
                id = str(uuid.uuid1())
                wavout = os.path.join(self.output_dir, id+'.wav')
            if isinstance(wavout, unicode):
                wavout = wavout.encode('utf-8')
            if isinstance(text, unicode):
                text = text.encode('utf8')
            tts_data = TTSData(text, wavout)
            self.do_tts(tts_data)
            return tts_data
        except Exception as ex:
            logger.error(ex)

class NumbTTS(TTSBase):

    def get_visemes(self, phonemes):
        visemes = []
        for ph in phonemes:
            v = self.get_viseme(ph)
            if v is not None:
                visemes.append(v)
        logger.debug("Get visemes {}".format(visemes))
        return visemes

    def do_tts(self, tts_data):
        text = tts_data.text
        fname = '{}.wav'.format(os.path.join(self.output_dir, text.strip()))
        if os.path.isfile(fname):
            shutil.copy(fname, tts_data.wavout)
            try:
                tts_data.phonemes = self.get_phonemes(fname)
            except Exception as ex:
                logger.error(ex)
                tts_data.phonemes = []

    def get_phonemes(self, fname):
        timing = '{}.yaml'.format(os.path.splitext(fname)[0])
        if os.path.isfile(timing):
            with open(timing) as f:
                phonemes = yaml.load(f)
            logger.info("Get timing info from file")
        else:
            phonemes = [
                {'type': 'phoneme', 'name': phoneme[0],
                    'start': phoneme[1], 'end': phoneme[2]}
                    for phoneme in audio2phoneme(fname)]
            with open(timing, 'w') as f:
                yaml.dump(phonemes, f)
            logger.info("Write timing info to file")
        return phonemes

class OnlineTTS(TTSBase):

    def __init__(self):
        super(OnlineTTS, self).__init__()
        self.cache_dir =  os.path.expanduser('{}/cache'.format(self.output_dir))

    def set_output_dir(self, output_dir):
        super(OnlineTTS, self).set_output_dir(output_dir)
        self.cache_dir =  os.path.expanduser('{}/cache'.format(self.output_dir))

    def get_cache_file(self, text):
        suffix = hashlib.sha1(text+str(self.get_tts_session_params())).hexdigest()[:6]
        filename = os.path.join(self.cache_dir, suffix+'.wav')
        return filename

    def offline_tts(self, tts_data):
        cache_file = self.get_cache_file(tts_data.text)
        if os.path.isfile(cache_file):
            shutil.copy(cache_file, tts_data.wavout)
            logger.info("Get offline tts for {} {}".format(
                tts_data.text, cache_file))
        else:
            raise TTSException("Offline tts failed, no such file {}".format(
                    self.get_cache_file(tts_data.text)))

    def do_tts(self, tts_data):
        try:
            self.offline_tts(tts_data)
        except Exception as ex:
            logger.error(ex)
            self.online_tts(tts_data)

    def online_tts(self, tts_data):
        return NotImplemented

class ChineseTTSBase(OnlineTTS):
    def __init__(self):
        super(ChineseTTSBase, self).__init__()

    def get_cache_file(self, text):
        delimiter = '#'
        pys = pinyin.get(text, delimiter=delimiter)
        if pys:
            pys = pys.split(delimiter)
            pys=[py for py in pys if re.match('[a-zA-Z]', py)]
            pys = ''.join(pys)
        pys = pys[:251-6-1]
        suffix = hashlib.sha1(text+str(self.get_tts_session_params())).hexdigest()[:6]
        filename = os.path.join(self.cache_dir, pys+'_'+suffix+'.wav')
        return filename

    def nonchinese2pinyin(self, text):
        """replace non-Chinese characters to pinyins"""
        NON_CHN_MAP = {
            '0': 'ling', '1': 'yi', '2': 'er', '3': 'san', '4': 'si', '5': 'wu',
            '6': 'liu', '7': 'qi', '8': 'ba', '9': 'jiu',
        }
        pattern = re.compile('|'.join(NON_CHN_MAP.keys()))
        new_text = ''
        last_point = 0
        it = re.finditer('[0-9]+', text)
        for i in it:
            new_text += text[last_point:i.span()[0]]
            new_text += pattern.sub(lambda x: NON_CHN_MAP[x.group()]+' ', i.group()).strip()
            last_point = i.span()[1]
        new_text += text[last_point:]
        return new_text

    def is_ssml(self, text):
        try:
            el = xml.etree.ElementTree.XML(text)
            if el.tag == 'speak':
                return True
            else:
                return False
        except Exception as ex:
            return False

    def strip_tag(self, text):
        text = re.sub('<[^<]+>', '', text)
        text = re.sub('\s{1,}', ' ', text)
        return text.strip()

    def get_phonemes(self, txt, duration):
        phonemes = []
        regexp = re.compile("""^(?P<initial>b|p|m|f|d|t|n|l|g|k|h|j|q|x|zh|ch|sh|r|z|c|s|y|w*)(?P<final>\w+)$""")
        if self.is_ssml(txt):
            txt = self.strip_tag(txt)
        pys = pinyin.get(txt, delimiter=' ')
        pys = self.nonchinese2pinyin(pys)
        pys = pys.strip().split(' ')
        logger.info('Get pinyin {}'.format(pys))
        if not pys:
            return []
        unit_time = float(duration)/len(pys)
        start_time = 0
        for py in pys:
            match = regexp.match(py)
            if match:
                mid_time = start_time + unit_time/2
                # Use 2 phonemes for a Chinese character
                initial = match.group('initial')
                final = match.group('final')
                if initial:
                    phonemes.append({
                        'type': 'phoneme',
                        'name': initial.lower(),
                        'start': start_time,
                        'end': mid_time,
                    })
                if final:
                    phonemes.append({
                        'type': 'phoneme',
                        'name': final.lower(),
                        'start': mid_time,
                        'end': start_time + unit_time,
                    })
                start_time += unit_time
        logger.debug('phonemes {}'.format(phonemes))
        return phonemes

    def do_tts(self, tts_data):
        super(ChineseTTSBase, self).do_tts(tts_data)
        duration = tts_data.get_duration()
        tts_data.phonemes = self.get_phonemes(tts_data.text, duration)

