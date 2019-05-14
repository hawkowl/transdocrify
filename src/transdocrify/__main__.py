import ast
import click
from transdocrify import process_from_epydoc_to_sphinx
from twisted.python.filepath import FilePath


@click.command()
@click.argument('path')
def run(path):

    fp = FilePath(path)
    children = [x for x in fp.walk() if x.splitext()[1] == ".py"]

    with click.progressbar(children) as c:
        for f in c:

            inp = f.getContent().decode('utf8')
            out = process_from_epydoc_to_sphinx(f, inp)

            f.setContent(u'\n'.join(out).encode('utf8'))


if __name__ == "__main__":
    run()

    from difflib import context_diff
    import sys
    from transdocrify.tests import in_epydoc, out_rst

    with open(in_epydoc.__file__.replace(".pyc", ".py"), 'r') as f:
        inp = str(f.read())

    with open(out_rst.__file__.replace(".pyc", ".py"), 'r') as f:
        outp = f.readlines()

    out3 = process_from_epydoc_to_sphinx(inp)

    out2 = list(map(lambda x: x + "\n", out3))[:-1]

    print(''.join(context_diff(outp, out2)))
