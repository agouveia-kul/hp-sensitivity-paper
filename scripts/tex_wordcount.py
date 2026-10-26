"""Approximate prose word count of the manuscript's content files (no build needed).

Strips comments, math, labels, references and float commands; counts the words
left, including captions and table cells. Used to check that edits do not make
the paper longer. ``python scripts/tex_wordcount.py [rev]`` counts the working
tree, or the files at git revision ``rev``.
"""
import re
import subprocess
import sys

FILES = ('paper/content/abstract.tex', 'paper/content/body.tex')


def words(s):
    s = re.sub(r'(?<!\\)%.*', '', s)
    s = re.sub(r'\\begin\{(equation|align)\*?\}.*?\\end\{(equation|align)\*?\}', ' ', s, flags=re.S)
    s = re.sub(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', ' ', s, flags=re.S)
    s = re.sub(r'\$[^$]*\$', 'X', s)
    s = re.sub(r'\\(begin|end|label|ref|eqref|cite|includegraphics|centering|vspace|input)\b(\[[^\]]*\])?(\{[^}]*\})?', ' ', s)
    return len(re.findall(r"[A-Za-z0-9][\w'.\-]*", s))


def read(path, rev=None):
    if rev is None:
        return open(path, encoding='utf-8').read()
    return subprocess.run(['git', 'show', f'{rev}:{path}'], capture_output=True, text=True,
                          encoding='utf-8', check=True).stdout


if __name__ == '__main__':
    rev = sys.argv[1] if len(sys.argv) > 1 else None
    n = {f: words(read(f, rev)) for f in FILES}
    for f, v in n.items():
        print(f'{f}: {v}')
    print('total:', sum(n.values()))
