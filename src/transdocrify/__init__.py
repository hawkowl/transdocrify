import re

import ast
from ast import NodeVisitor
from io import StringIO
from textwrap import dedent

param_re = re.compile(r"(\s*)@param\s*(\w*):\s*(.*)")
param_re = re.compile(r"(\s*)@type\s*(\w*):\s*(.*)")

def process_from_epydoc_to_sphinx(imp):

    from epydoc.markup.epytext import parse_docstring

    astinput = ast.parse(imp)
    docstrings = []

    class Vis(NodeVisitor):

        def visit_FunctionDef(self, node):

            if len(node.body) > 0 and isinstance(node.body[0], ast.Expr):
                potential_docstring = node.body[0]
                if isinstance(potential_docstring.value, ast.Str):
                    # We think it's a docstring.
                    doc = potential_docstring.value

                    length = len(doc.s.split("\n"))

                    docstrings.append({
                        "offset": node.col_offset + 4,
                        "line_no": potential_docstring.lineno - length + 1,
                        "content": dedent(doc.s).strip(),
                        "length": length
                    })

    v = Vis()
    v.visit(astinput)

    f = imp.split("\n")

    for i in docstrings:

        parsed = parse_docstring(i["content"], []).split_fields()

        content = []
        content.append(parsed[0].to_plaintext(None).strip())
        content.append("")

        def dump(t):
            resp = []
            for i in t._tree.children[0].children:
                if isinstance(i, str):
                    resp.append(i)
                    continue

                if i.tag == "link":
                    resp.append(":py:obj:`" + i.children[0].children[0] + "`")
                    continue

            return "".join(resp)

        for x in parsed[1]:
            if x.tag() in ["param", "type"]:
                content.append(":%s %s: %s" % (x.tag(), x.arg(), dump(x.body())))

            if x.tag() in ["return", "rtype"]:
                content.append(":%s: %s" % (x.tag(), dump(x.body())))

        k = StringIO()

        from .docstring_wrap import wrapPythonDocstring
        wrapPythonDocstring("\n".join(content).decode('utf8'), k, width=79 - i["offset"], indentation=u'')

        k.seek(0)
        i["new_content"] = k.read().strip()

    # Process docstrings here...
    reduced_by = 1

    for i in docstrings:
        line_no = i["line_no"]
        length = i["length"]
        offset = i["offset"]
        new_content = i["new_content"]

        del f[line_no - reduced_by:line_no - reduced_by + length]

        indented = list(map(lambda x: " " * offset + x if x else "", new_content.split("\n")))
        indented_quotes = ' ' * offset + '"""'

        f = f[0:line_no-reduced_by] + [indented_quotes] + indented + [indented_quotes] + f[line_no-reduced_by:]

        reduced_by += len(indented) - length + 2

    return f
