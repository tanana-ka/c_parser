import warnings
import re

def debug_print(line):
    print(line)

def c_parser(filename):
    for line in initial_processing(filename):
        debug_print(line)
        for token in tokenization_line(line):
            debug_print('token = %s'%(token))

def tokenization_line(line):
    pos = 0
    is_first_token = True
    re_space = re.compile(r'^[ \t\n\r\f\v\0]')
    re_identifier_start = re.compile(r'^[a-zA-Z_]')
    re_number = re.compile(r'[0-9]')
    while pos < len(line):
        c = line[pos]
        if re_space.match(c) is not None:
            pos += 1
            continue
        if is_first_token and c == '#':
            yield tokenization_preprocess(line, pos+1)
            return
        is_first_token = False
        if re_identifier_start.match(c) is not None:
            pos, token = token_identifier(line, pos)
            yield token
            continue
        if re_number.match(c) is not None:
            pos, token = token_number(line, pos)
            yield token
            continue
        # TODO: 小数, 他の数字フォーマット
        # TODO: 記号
        # TODO: literal
        warnings.warn('unidentifier token: %s'%c)
        pos += 1

def tokenization_preprocess(line, start):
    re_space = re.compile(r'^[ \t\n\r\f\v\0]')
    re_identifier_start = re.compile(r'^[a-zA-Z_]')
    pos = start
    while pos < len(line):
        c = line[pos]
        if re_space.match(c) is not None:
            pos += 1
            continue
        if re_identifier_start.match(c) is None:
            raise RuntimeError('# after token is not identifier: %s'%line)
        pos, token = token_identifier(line, pos)
        if token == 'include':
            pass
        elif token == 'define':
            pass
        # TODO: tokenごとの処理
        return token

# 呼び出し前に1文字目が数字でないことを確認済み
def token_identifier(line, start):
    re_identifier = re.compile(r'^[a-zA-Z0-9_]')
    current = start
    while current < len(line):
        result = re_identifier.match(line[current])
        if result is None:
            break
        current += 1
    return (current, line[start:current])

def token_number(line, start):
    re_number = re.compile(r'[0-9]')
    current = start
    while current < len(line):
        result = re_number.match(line[current])
        if result is None:
            break
        current += 1
    return (current, line[start:current])

def initial_processing(filename):
    is_block = False
    block_buf = ''
    for line in line_generator(filename):
        ret, is_block = process_initial_in_line(line, is_block, block_buf)
        if ret == None:
            continue
        yield block_buf + ret
        block_buf = ''

def process_initial_in_line(line, is_block, block_buf):
    prev_pos = 0
    pos, token = get_next_initial_token(line, is_block, prev_pos)
    while pos != -1:
        if token == '//':
            return (line[prev_pos:pos], False)
        if token == '/*':
            is_block = True
            block_buf += line[prev_pos:pos] + ' '
        elif token == '*/':
            is_block = False
            prev_pos = pos + len(token)
        pos, token = get_next_initial_token(line, is_block, pos+len(token))
    ret = None if is_block else line[prev_pos:]
    return (ret, is_block)

def get_next_initial_token(line, is_block, start):
    head_char = '*' if is_block else '/'
    pos = start
    while pos < len(line)-1:
        c = line[pos]
        if is_block == False and c == '"':
            pos = skip_literal(line, pos)
            continue
        if c != head_char:
            pos += 1
            continue
        next_char = line[pos+1]
        if head_char == '*':
            if next_char == '/':
                return (pos, line[pos:pos+2])
        elif next_char == '/' or next_char == '*':
            return (pos, line[pos:pos+2])
        pos += 1
    return (-1, None)

# includeの後は\"は解釈しない、普通の文字列リテラルは\"は解釈する、違いを確認する
def skip_literal(line, start):
    pos = start + 1
    while pos < len(line):
        if line[pos-1] != '\\' and line[pos] == '"':
            return pos + 1
        pos += 1
    raise RuntimeError('"literal is not closed: %s'%line)

def line_generator(filename):
    with open(filename) as f:
        buf = ''
        for line in f:
            line = line.rstrip('\r\n')
            if len(line) == 0:
                continue
            if line[-1] == '\\':  # 本来は空白があっても可
                buf += line[:-1]
                continue
            yield buf + line
            buf = ''
        if len(buf) != 0:
            yield buf
