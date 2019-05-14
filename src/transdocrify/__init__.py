import re

import ast
from ast import NodeVisitor
from io import StringIO
from textwrap import dedent

param_re = re.compile(r"(\s*)@param\s*(\w*):\s*(.*)")
param_re = re.compile(r"(\s*)@type\s*(\w*):\s*(.*)")


def process_from_epydoc_to_sphinx(fle, imp):

    from epydoc.markup.epytext import parse_docstring

    astinput = ast.parse(imp.encode('utf8'), filename=fle.path)
    docstrings = []

    f = imp.split("\n")

    class Vis(NodeVisitor):
        def visit_FunctionDef(self, node, indent=4):

            if len(node.body) > 0 and isinstance(node.body[0], ast.Expr):
                potential_docstring = node.body[0]
                if isinstance(potential_docstring.value, ast.Str):
                    doc = "\n".join(f[node.lineno : potential_docstring.lineno]).split(
                        '"""'
                    )[1]
                    length = len(doc.split("\n"))

                    if doc[0] != "\n":
                        doc = " " * (node.col_offset + 4) + s
                        length -= 1
                    if doc[-1] != "\n":
                        length -= 1

                    docstrings.append(
                        {
                            "offset": node.col_offset + indent,
                            "line_no": potential_docstring.lineno - length - 1,
                            "content": dedent(doc).strip(),
                            "length": length + 2,
                        }
                    )

        def visit_ClassDef(self, node):
            self.visit_FunctionDef(node)
            for i in node.body:
                if isinstance(i, (ast.FunctionDef, ast.ClassDef)):
                    self.visit_FunctionDef(i)

        def visit_Module(self, node):
            node.lineno = 0
            node.col_offset = 0
            self.visit_FunctionDef(node, indent=0)
            for i in node.body:
                if isinstance(i, (ast.FunctionDef, ast.ClassDef)):
                    self.visit_FunctionDef(i)

    v = Vis()
    v.visit(astinput)

    for i in docstrings:

        err = []
        parsed = parse_docstring(i["content"], err).split_fields()

        err = [x for x in err if x.is_fatal()]

        if err:
            print("")
            print("Errors, skipping " + fle.path + ":" + str(i["line_no"]))
            i["new_content"] = i["content"]
            continue

        content = []
        if parsed[0]:
            content.append(parsed[0].to_plaintext(None).strip())
            content.append("")

        def dump(t):
            resp = []
            if not t._tree.children:
                return ""

            print(t._tree.children)

            for child in t._tree.children:

                if child.tag == "para":
                    for i in child.children:
                        if isinstance(i, (str, unicode)):
                            resp.append(i)
                            continue

                        if i.tag == "link":
                            resp.append(":py:obj:`" + i.children[0].children[0] + "`")
                            continue

                        if i.tag == "code":
                            resp.append("``%s``" % (i.children[0],))
                            continue

                        if i.tag == "italic":
                            resp.append("*%s*" % (i.children[0],))
                            continue

                        if i.tag == "bold":
                            resp.append("**%s**" % (i.children[0],))
                            continue

                        raise Exception(i.tag)
                elif child.tag == "literalblock":
                    resp.append(":\n\n   ```\n" + child.children[0] + "\n   ```")

                else:
                    continue
                    raise Exception(child.tag)

            return "".join(resp)

        for x in parsed[1]:

            tag = x.tag()

            if tag in ["param", "type", "ivar", "cvar", "var", "see"]:
                content.append(":%s %s: " % (tag, x.arg()) + dump(x.body()))

            elif tag in ["rtype", "since"]:
                content.append(":%s: %s" % (tag, dump(x.body())))

            elif tag in ["raise", "raises"]:
                content.append(":raises %s: %s" % (tag, dump(x.body())))

            # TYPO IN TWISTED
            elif tag in ["params"]:
                content.append(":param %s: %s" % (tag, dump(x.body())))

            # TYPO IN TWISTED
            elif tag in ["types"]:
                content.append(":type %s: " % (tag,) + dump(x.body()))

            # TYPO IN TWISTED
            elif tag in ["arg"]:
                content.append(":param %s: %s" % (tag, dump(x.body())))

            # TYPO IN TWISTED
            elif tag in ["returntype"]:
                content.append(":rtype: %s" % (dump(x.body()),))

            elif tag in ["return", "returns"]:
                content.append(":returns: %s" % (dump(x.body()),))

            elif tag in ["note"]:
                content.append(".. note::")
                content.append("    " + dump(x.body()))

            else:
                print(x.body())
                print(parsed[0])
                raise Exception("Can't parse %s" % (tag,))

        k = StringIO()

        from .docstring_wrap import wrapPythonDocstring

        wrapPythonDocstring(
            "\n".join(content).decode('utf8'),
            k,
            width=79 - i["offset"],
            indentation=u'',
        )

        k.seek(0)
        i["new_content"] = k.read().strip()

    # Process docstrings here...
    last_point = 0

    regions = [[1, 0]]

    finished_file = []

    for i in docstrings:
        line_no = i["line_no"]
        length = i["length"]
        regions[-1][1] = line_no
        regions.append([line_no + length, -1])

    for region, i in zip(regions, docstrings):
        offset = i["offset"]
        new_content = i["new_content"]

        indented = list(
            map(lambda x: " " * offset + x if x else "", new_content.split("\n"))
        )
        indented_quotes = ' ' * offset + '"""'

        ripped = f[region[0] - 1 : region[1]]
        finished_file.extend(ripped)
        finished_file.extend([indented_quotes] + indented + [indented_quotes])

    return finished_file
