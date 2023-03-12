import libcst as cst

from preprocess.transform.utils.visit import has_new_line


def add_parenthesis_if_new_line(node):
    if has_new_line(node):
        if hasattr(node, "lpar"):
            return node.with_changes(lpar=[cst.LeftParen()], rpar=[cst.RightParen()])
        else:
            raise NotImplementedError()
    return node
