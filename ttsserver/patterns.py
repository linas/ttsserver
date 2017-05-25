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
        el.set('rate', '-30%')
        el.set('volume', '+20%')
        el.set('pitch', '+10%')
        el2 = etree.Element('break')
        el2.set('time', '300ms')
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
        else:
            el = etree.Element('mark')
            el.set('name', name)
        return el,

