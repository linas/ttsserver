# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger('hr.ttsserver.visemes')

class BaseVisemes:

    # Params for each visime passed to blender
    # duration: multiplier opf the actual visime time
    # rampin: time to ramp in in % of duration
    # rampout: time to ramp in in % of duration
    # magnitude: magnitude in blender
    visemes_param = {
       'A-I':               {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'E':                 {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'F-V':               {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'Q-W':               {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'L':                 {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'C-D-G-K-N-S-TH':    {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'M':                 {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'O':                 {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'U':                 {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'u':                 {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       's':                 {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'S':                 {'duration': 1.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
       'Sil':               {'duration': 3.0, 'rampin': 0.1, 'rampout': 0.1, 'magnitude': 0.99},
    }

    def __init__(self):
        self.set_visemes_map(self.default_visemes_map)

    def set_visemes_map(self, visemes_map):
        if visemes_map is not None:
            self.phonemes = {}
            for v, s in visemes_map.iteritems():
                for p in s:
                    self.phonemes[p] = v

    def get_visemes(self, phonemes):
        visemes = []
        for ph in phonemes:
            v = self.get_viseme(ph)
            if v is not None:
                visemes.append(v)
        logger.debug("Get visemes {}".format(visemes))
        self.expand_m_visems(visemes)
        return visemes

    def expand_m_visems(self, visemes):
        """
            Let M last longer to close the mouth
        """
        ids = [i for i, v in enumerate(visemes) if v['name']=='M' or v['name']=='F-V']
        logger.info('Before visemes {}'.format(visemes))
        logger.info('ids of M {}'.format(ids))
        for id in ids:
            if id < (len(visemes)-1):
                t = visemes[id+1]['duration']/2
                visemes[id]['duration'] += t
                visemes[id+1]['start'] += t
                visemes[id+1]['duration'] -= t
        logger.info('After visemes {}'.format(visemes))

    def get_viseme(self, ph):
        try:
            v = {}
            v['type'] = 'viseme'
            v['name'] = self.phonemes[ph['name']]
            v['start'] = ph['start']
            v['end'] = ph['end']
            v['duration'] = ph['end']-ph['start']
        except KeyError:
            logger.error("Unknown phoneme "+ph['name'])
            return None
        return v

    def filter_visemes(self, visemes, threshold):
        return [viseme for viseme in visemes if viseme['duration']>threshold]

