import collections
import re

Token = collections.namedtuple('Token', ['identifier', 'value', 'line', 'column'])


def tokenize(prison):
    # keywords = {'START', 'END'}
    token_specs = [
        ('BEGIN', r'BEGIN'),
        ('END', r'END'),
        ('NUMBER', r'\d+(\.\d*)?'),
        ('STRING', r'".+"'),
        ('CONTENT', r'[^\s]+'),
        ('NEWLINE', r'\n'),
        ('WHITESPACE', r'\s+'),
    ]
    token_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specs)
    get_token = re.compile(token_regex).match
    line = 1
    pos = line_start = 0
    matched = get_token(prison)
    while matched is not None:
        identifier = matched.lastgroup
        if identifier == 'NEWLINE':
            line_start = pos
            line += 1
        elif identifier != 'WHITESPACE':
            value = matched.group(identifier)
            if identifier == 'STRING':
                value = value.strip('"')
            yield Token(identifier, value, line, matched.start() - line_start)
        pos = matched.end()
        matched = get_token(prison, pos)
    if pos != len(prison):
        raise RuntimeError('Unexpected character %r on line %d' % (prison[pos], line))

infile = r"mini.prison"
with open(infile, "r") as prison:
    tokens = tokenize(prison.read())
    for token in tokens:
        print(token)


class BaseObj:
    all = []
    obj_attrs = []

    @classmethod
    def filter(cls, **kwargs):
        possibilities = list(cls.all)
        for k, v in kwargs.iteritems():
            if k not in cls.obj_attrs:
                raise NameError('Class %s has no attribute %s' % (cls, k))
            possibilities = filter(lambda x: getattr(x, k) == v, possibilities)
        return possibilities


class Attribute(BaseObj):
    obj_attrs = ['name', 'value', 'token', 'owner']

    def __repr__(self):
        return '<Attribute %s:%s>' % (self.name, self.value)

    def __init__(self, name, value, token, owner=None):
        self.name = name
        self.value = value
        self.token = token
        self.owner = owner
        Attribute.all.append(self)


class PrisonObj(BaseObj):
    def __init__(self, name):
        self.name = name
        self.attributes = []
        PrisonObj.all.append(self)

    def __repr__(self):
        return 'PrisonObj %s' % self.name

    def add_attribute(self, attribute):
        attribute.owner = self
        self.attributes.append(attribute)


a = Attribute('a', 3, 'tokena')
b = Attribute('b', 4, 'tokenb')


# def parse_tokens(tokens):
#     content = OrderedDict()
#     index = 0
#     if type(tokens) is list:
#         tokens = enumerate(tokens)
#     for index, token in tokens:
#         if token[0] == TOKEN_END:
#             break
#         elif token[0] == TOKEN_BEGIN:
#             secondIndex, secondToken = next(tokens)
#             if secondToken[0] != TOKEN_CONTENT:
#                 raise Exception("Expected a CONTENT token after a BEGIN token")
#             parsed_tokens, sub_contentLength = parse_tokens(tokens)
#             content.setdefault(secondToken[1].strip('"'), [])
#             content[secondToken[1].strip('"')].append(parsed_tokens)
#         else:
#             secondIndex, secondToken = next(tokens)
#             content.setdefault(token[1].strip('"'), [])
#             content[token[1].strip('"')].append(secondToken[1])
#     return content, index
