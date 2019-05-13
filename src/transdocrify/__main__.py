import ast
from transdocrify import process_from_epydoc_to_sphinx

if __name__ == "__main__":
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
