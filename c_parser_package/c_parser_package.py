def c_parser(filename):
    print(filename)
    format_lines = []
    for line in line_generator(filename):
        print(line)
        print(line.find('/'))
        format_lines.append(line)
    for line in format_lines:
        print(line)
    pass

def line_generator(filename):
    with open(filename) as f:
        buf = ''
        for line in f:
            line = line.rstrip('\r\n')
            if len(line) == 0:
                continue
            if line[-1] == '\\':
                buf += line[:-1]
                continue
            yield buf + line
            buf = ''
        if len(buf) != 0:
            yield buf

