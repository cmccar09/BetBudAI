from html.parser import HTMLParser

class Validator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []
        self.stack = []
        self.void = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def handle_starttag(self, tag, attrs):
        if tag not in self.void:
            self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag in self.void:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            top = self.stack[-1] if self.stack else 'empty'
            self.errors.append(f'Unexpected </{tag}>, stack top: {top}')

for f in ['cheltenham_strategy_2026.html', 'barrys/barrys_cheltenham_2026.html']:
    v = Validator()
    with open(f, encoding='utf-8') as fp:
        v.feed(fp.read())
    if v.errors:
        print(f'{f}: ERRORS: {v.errors[:5]}')
    elif v.stack:
        print(f'{f}: Unclosed tags (last 5): {v.stack[-5:]}')
    else:
        print(f'{f}: OK - no issues')
