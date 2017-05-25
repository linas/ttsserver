import xml.etree.ElementTree as etree
import StringIO
from patterns import StrongPattern, EmphasisPattern, MarkPattern

class ActionParser(object):
    def __init__(self):
        self.patterns = []
        self.build_patterns()
        self.recognized_nodes = {}
        self.counter = 0
        self.sep = "0x1f"

    def reset(self):
        self.counter = 0
        self.recognized_nodes.clear()

    def build_patterns(self):
        self.patterns.append(StrongPattern())
        self.patterns.append(EmphasisPattern())
        self.patterns.append(MarkPattern())

    def add_recognized_nodes(self, node):
        id = 'sss{}eee'.format(self.counter)
        self.recognized_nodes[id] = node
        self.counter += 1
        return id

    def recover_recognized_nodes(self, text):
        tokens = text.split(self.sep)
        nodes = []
        for token in tokens:
            if token in self.recognized_nodes:
                node = self.recognized_nodes.get(token)
                nodes.append(node)
            else:
                nodes.append(token)
        return nodes

    def parse(self, text):
        text = text.strip()
        self.reset()
        pattern_index = 0
        while pattern_index < len(self.patterns):
            pattern = self.patterns[pattern_index]
            match = pattern.match(text)

            # Search all the matches then try the next pattern
            if not match:
                pattern_index += 1
                continue

            nodes = pattern.get_nodes(match)
            place_holders = []
            for node in nodes:
                if not self.is_string(node):
                    id = self.add_recognized_nodes(node)
                    place_holders.append(id)
                else:
                    place_holders.append(node)
            text = '{}{}{}{}{}'.format(match.group(1), self.sep, self.sep.join(place_holders), self.sep, match.groups()[-1])

        nodes = self.recover_recognized_nodes(text)
        return self.to_xml(nodes)

    def is_string(self, text):
        return isinstance(text, basestring) or isinstance(text, unicode)

    def to_xml(self, nodes):
        output = []

        for node in nodes:
            if self.is_string(node):
                output.append(node)
            else:
                buf = StringIO.StringIO()
                tree = etree.ElementTree(node)
                tree.write(buf)
                output.append(buf.getvalue())
                buf.close()

        return ''.join(output)

if __name__ == '__main__':
    parser = ActionParser()
    print parser.parse('*Hi there* |happy| this is **action mark down**')
    print parser.parse('*Hi there* |happy| |pause,2| this is **action mark down**')
