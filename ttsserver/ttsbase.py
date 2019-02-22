# -*- coding: utf-8 -*-
# Copyright (c) 2013-2019 Hanson Robotics, Ltd. 

from __future__ import division
import os
import re
import logging
import hashlib
import pinyin
from scipy.io import wavfile
import shutil
import yaml
import xml.etree.ElementTree as ET
import uuid
import traceback
import subprocess

try:
    from audio2phoneme import audio2phoneme
except ImportError as ex:
    pass
from ttsserver.visemes import BaseVisemes
from espp.emotivespeech import emotive_speech

CWD = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('hr.ttsserver.ttsbase')

ILLEGAL_CHARS = re.compile(r"""[/]""")

def get_duration(wav_fname):
    if os.path.isfile(wav_fname):
        try:
            duration = float(subprocess.check_output('sox --i -D %s' % wav_fname, shell=True))
            return duration
        except Exception as ex:
            logger.error(ex)
    return 0.0

def is_xml(text):
    if re.search(r'<.+>', text, re.UNICODE) is None:
        return False
    else:
        if not isinstance(text, unicode):
            text = text.decode('utf-8')
        root = u'<_root_ xmlns:amazon="www.amazon.com">{}</_root_>'.format(text)
        try:
            ET.fromstring(root.encode('utf-8'))
        except Exception:
            return False
        return True

def strip_xmltag(text):
    convert = False
    if not isinstance(text, unicode):
        text = text.decode('utf-8')
        convert = True
    root = u'<_root_ xmlns:amazon="www.amazon.com">{}</_root_>'.format(text)
    tree = ET.fromstring(root.encode('utf-8'))
    notags = ET.tostring(tree, encoding='utf8', method='text')
    notags = notags.strip()
    if convert:
        if isinstance(notags, unicode):
            notags = notags.encode('utf-8')
    return notags

# User data class to store information
class TTSData:
    def __init__(self, text=None, wavout=None):
        self.text = text
        self.wavout = wavout
        self.phonemes = []
        self.markers = []
        self.words = []
        self.visemes = []

    def get_duration(self):
        return get_duration(self.wavout)

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
        self.emo_cache_dir = '.' # emotive speech cache dir
        self.viseme_mapping = None
        self.tts_params = {}

    def set_output_dir(self, output_dir):
        self.output_dir = os.path.expanduser(output_dir)
        self.emo_cache_dir = os.path.join(self.output_dir, 'emo_cache')
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)
        if not os.path.isdir(self.emo_cache_dir):
            os.makedirs(self.emo_cache_dir)

    def set_viseme_mapping(self, mapping):
        self.viseme_mapping = mapping

    def get_tts_params(self):
        return self.tts_params

    def set_tts_params(self, **params):
        self.tts_params = {}
        self.tts_params.update(params)

    def get_emo_cache_file(self, text, params):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        hashcode = hashlib.sha1(text+str(params)).hexdigest()[:40]
        filename = os.path.join(self.emo_cache_dir, hashcode+'.wav')
        return filename

    def get_cache_file(self, text):
        raise NotImplementedError("get_cache_file is not implemented")

    def set_voice(self, voice):
        raise NotImplementedError("set_voice is not implemented")

    def do_tts(self, tts_data):
        raise NotImplementedError("do_tts is not implemented")

    def _adjust_phonemes_timing(self, phonemes, ratio):
        for p in phonemes:
            p['start'] = p['start']*ratio
            p['end'] = p['end']*ratio

    def tts(self, text, wavout=None, **kwargs):
        try:
            if wavout is None:
                id = str(uuid.uuid1())
                wavout = os.path.join(self.output_dir, id+'.wav')
            if isinstance(wavout, unicode):
                wavout = wavout.encode('utf-8')
            if isinstance(text, unicode):
                text = text.encode('utf8')
            tts_data = TTSData(text, wavout)
            self.set_tts_params(**kwargs)
            self.do_tts(tts_data)
            emotion = kwargs.get('emotion')
            orig_duration = tts_data.get_duration()
            if emotion is not None:
                cache_file = self.get_emo_cache_file(text, kwargs)
                try:
                    ofile = '{}/emo_tmp.wav'.format(os.path.dirname(tts_data.wavout))
                    if os.path.isfile(cache_file):
                        shutil.copy(cache_file, ofile)
                        logger.info("Get cached emotive speech tts for {} {}".format(
                            text, cache_file))
                    else:
                        emotive_speech(tts_data.wavout, ofile, **kwargs)
                        shutil.copy(ofile, cache_file)
                    shutil.move(ofile, tts_data.wavout)
                    emo_duration = tts_data.get_duration()
                    self._adjust_phonemes_timing(tts_data.phonemes, emo_duration/orig_duration)
                except Exception as ex:
                    logger.error(traceback.format_exc())
            if self.viseme_mapping is not None:
                tts_data.visemes = self.viseme_mapping.get_visemes(tts_data.phonemes)
            return tts_data
        except Exception as ex:
            logger.error(traceback.format_exc())


class Numb_Visemes(BaseVisemes):
    # Mapping is approx. May need tunning
    # All phonemes are from cereproc documentation
    # https://www.cereproc.com/files/CereVoiceCloudGuide.pdf
    default_visemes_map = {
        'A-I': ['A','AA','AI','AU','AE','AH','AW','AX','AY','EY',],
        'E': ['E','E@','EI','II','IY','EI', 'EH',],
        'F-V': ['F','V'],
        'Q-W': ['W'],
        'L': ['@', '@@', 'I', 'I@','IH','L', 'R', 'Y', 'R'],
        'C-D-G-K-N-S-TH': ['CH','D','DH','G','H','HH','JH','K','N','NG','S','SH','T','TH','Z','ZH','DX','ER',],
        'M': ['B','M','P'],
        'O': ['O','OI','OO','OU','AO','OW','OY',],
        'U': ['U','U@','UH','UU','UW'],
        'Sil': ['SIL']
    }


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
                logger.error(traceback.format_exc())
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
        if not os.path.isdir(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_cache_id(self, text):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        suffix = hashlib.sha1(text+str(self.get_tts_params())).hexdigest()[:6]
        text = strip_xmltag(text)
        text = ILLEGAL_CHARS.sub('_', text)
        return text[:200]+'-'+suffix

    def get_cache_file(self, text):
        cache_id = self.get_cache_id(text)
        filename = os.path.join(self.cache_dir, cache_id+'.wav')
        return filename

    def offline_tts(self, tts_data):
        cache_file = self.get_cache_file(tts_data.text)
        if os.path.isfile(cache_file):
            shutil.copy(cache_file, tts_data.wavout)
            logger.info("Get offline tts")
        else:
            raise TTSException("Offline tts failed, no such file {}".format(
                    self.get_cache_file(tts_data.text)))

    def do_tts(self, tts_data):
        try:
            self.offline_tts(tts_data)
        except Exception as ex:
            logger.exception(ex)
            self.online_tts(tts_data)

    def online_tts(self, tts_data):
        return NotImplemented

class ChineseTTSBase(OnlineTTS):
    def __init__(self):
        super(ChineseTTSBase, self).__init__()

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
            el = xml.etree.ET.XML(text)
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

