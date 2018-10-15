import xml.etree.ElementTree as etree
import re

class Pattern(object):

    def __init__(self, pattern):
        self.pattern = pattern
        self.pattern_re = re.compile(self.pattern, re.DOTALL | re.UNICODE)

    def match(self, text):
        return self.pattern_re.match(text)

    def get_nodes(self, match):
        return NotImplemented

    def __repr__(self):
        return self.__class__.__name__

class EmphasisPattern(Pattern):

    def __init__(self):
        super(EmphasisPattern, self).__init__(r'^(.*?)(\*)([^\*]+)\2(.*)$')

    def get_nodes(self, match):
        el = etree.Element('prosody')
        el.text = match.group(3)
        el.set('rate', '-20%')
        el.set('pitch', '+5%')
        return el,

class StrongPattern(Pattern):

    def __init__(self):
        super(StrongPattern, self).__init__(r'^(.*?)(\*{2})([^\*]+)\2(.*)$')

    def get_nodes(self, match):
        el = etree.Element('prosody')
        el.text = match.group(3)
        el.set('rate', '-20%')
        el.set('volume', '+6dB')
        el.set('pitch', '+5%')
        el2 = etree.Element('break')
        el2.set('time', '150ms')
        return el2, el

class MarkPattern(Pattern):

    def __init__(self):
        super(MarkPattern, self).__init__(r'^(.*?)(\|)([^\|]+)\2(.*)$')

    def get_nodes(self, match):
        name = match.group(3)
        if name.startswith('pause'):
            if ',' in name:
                name, time = name.split(',', 1)
            else:
                time = '1s'
            el = etree.Element('break')
            el.set('time', time)
        elif name.startswith('vocal'):
            if ',' in name:
                name, gid = name.split(',', 1)
                try:
                    gid = int(gid)
                except SyntaxError:
                    raise SyntaxError('vocal syntax error: id is not integer')
                el = etree.Element('spurt')
                el.set('audio', 'g0001_{:03d}'.format(gid))
                el.text = 'vocalgesture'
            else:
                raise SyntaxError('vocal syntax error: not enough argument')
        else:
            el = etree.Element('mark')
            el.set('name', name)
        return el,

