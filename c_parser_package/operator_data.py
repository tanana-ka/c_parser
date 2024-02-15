class operator_data:
    OPERATORS = (
        '(',
        ')',
        '[',
        ']',
        '.',
        '->',
        '++',
        '--',
        '&',
        '*',
        '+',
        '-',
        '~',
        '!',
        '/',
        '%',
        '<<',
        '>>',
        '<',
        '<=',
        '>=',
        '>',
        '==',
        '!=',
        '^',
        '|',
        '&&',
        '||',
        '?',
        ':',
        '=',
        '+=',
        '-=',
        '*=',
        '/=',
        '%=',
        '<<=',
        '>>=',
        '&=',
        '^=',
        '|=',
        ',',
        '{',
        '}',
        ';',
        '...',
    )

    def __init__(self):
        starts, table = self.create_parse_data()
        self.STARTS_CHAR = starts
        self.PARSE_TABLE = table

    def create_parse_data(self):
        dict = {}
        starts = set()
        for ope in self.OPERATORS:
            starts.add(ope[0])
            num = len(ope)
            if dict.get(num) is None:
                dict[num] = set()

            dict[num].add(ope)

        table = sorted(dict.items(), key = lambda i : i[0], reverse=True)
        return (starts, table)

    def parse_operator(self, line, start):
        if not line[start] in self.STARTS_CHAR:
            return None

        for l, s in self.PARSE_TABLE:
            ope = line[start:start+l]
            if ope in s:
                return ope

        raise RuntimeError('inidentified: %s'%(line[start:]))
