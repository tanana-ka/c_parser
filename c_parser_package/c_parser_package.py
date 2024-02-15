import warnings
import re

import operator_data

def debug_print(line):
    print(line)

def c_parser(filename):
    for line in initial_processing(filename):
        debug_print('parse_line: %s'%line)
        for token in tokenization_line(line):
            debug_print(token)

def tokenization_line(line):
    pos = 0
    is_first_token = True
    re_space = re.compile(r'^[ \t\n\r\f\v\0]')
    re_identifier_start = re.compile(r'^[a-zA-Z_]')
    re_number = re.compile(r'[0-9]')
    op = operator_data.operator_data()
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
        # TODO: 小数, 他の数字フォーマット
        if re_number.match(c) is not None:
            pos, token = token_number(line, pos)
            yield token
            continue
        # TODO: 特殊なリテラル, L""など
        if c == '"':
            pos, token = token_string_literal(line, pos)
            yield token
            continue
        if c == "'":
            pos, token = token_char(line, pos)
            yield token
            continue
        ope = op.parse_operator(line, pos)
        if ope is not None:
            yield ope
            pos += len(ope)
            continue
        warnings.warn('unidentifier token: %s, %s'%(line, c))
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
        pos, directives = token_identifier(line, pos)
        if directives == 'include':
            arg = token_directive_include(line, pos)
            return (directives, *arg)
        # TODO: directivesごとの処理
        # if, ifdef, ifndef, elif, else, endif
        # define, undef
        # warning, error
        # pragma once
        return directives

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

def token_string_literal(line, start):
    current = start + 1
    while current < len(line):
        next_pos = line.find('"', current)
        if line[next_pos-1] != '\\' and line[next_pos] == '"':
            return next_pos+1, line[start:next_pos+1]
    raise RuntimeError('string literal unclosed: %s', line)

def token_char(line, start):
    current = start + 1
    if line[current] == '\\':
        current += 1

    current += 1
    if line[current] != "'":
        debug_print(line[start])
        debug_print(line[current])
        raise RuntimeError('char unclosed: %s, %d'%(line, start))
    return current+1, line[start:current+1]

def token_directive_include(line, start):
    current = start
    re_space = re.compile(r'^[ \t\n\r\f\v\0]')
    re_identifier_start = re.compile(r'^[a-zA-Z_]')
    while current < len(line):
        if re_space.match(line[current]) is not None:
            current += 1
            break
        current += 1

    file_start = current + 1
    include_type = ''
    filename = ''
    if line[current] == '<':
        current = line.find('>', current+1)
        include_type = '<>'
        filename = line[file_start:current]
    elif line[current] == '"':
        current = line.find('"', current+1)
        include_type = '""'
        filename = line[file_start:current]
    elif re_identifier_start.match(line[current]) is not None:
        current, filename = token_identifier(line, current)
        include_type = 'identifier'
    else:
        raise RuntimeError(line)
    current += 1
    while current < len(line):
        if re_space.match(line[current]) is not None:
            raise RuntimeError(line)
        current += 1
    return (include_type, filename)

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
        elif token == '/*':
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

# TODO: includeの後は\"は解釈しない、普通の文字列リテラルは\"は解釈する、組み合わせを確認する
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
