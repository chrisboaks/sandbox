import collections
import re

Token = collections.namedtuple('Token', ['typ', 'value', 'line', 'column'])


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
            val = matched.group(identifier)
            if identifier == 'STRING':
                val = val.strip('"')
            yield Token(identifier, val, line, matched.start() - line_start)
        pos = matched.end()
        matched = get_token(prison, pos)
    if pos != len(prison):
        raise RuntimeError('Unexpected character %r on line %d' % (prison[pos], line))

inFile = r"mini.prison"
with open(inFile, "r") as prison:
    tokens = tokenize(prison.read())
    for token in tokens:
        print(token)


# inFile = r"orig.prison"
# outFile = r"parsed.prison"
# with open(inFile, "r") as oldPrisonFile, open(outFile, "w") as newPrisonFile:
#     scanner = re.Scanner([
#         (r"\s+", None),
#         (r"BEGIN", lambda scanner, token:(TOKEN_BEGIN, token)),
#         (r"END", lambda scanner, token:(TOKEN_END, token)),
#         (r'".*"', lambda scanner, token:(TOKEN_CONTENT, token)),
#         (r"[^\s]*", lambda scanner, token:(TOKEN_CONTENT, token)),
#     ])

#     tokens, remainder = scanner.scan(oldPrisonFile.read())
#     parsed_prison = parse_tokens(tokens)[0]

#     security_hearings(parsed_prison)
#     newPrisonFile.write("\n".join(generate_prison_format(parsed_prison)))
