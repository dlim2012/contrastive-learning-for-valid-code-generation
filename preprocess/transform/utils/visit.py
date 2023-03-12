from typing import Optional

import libcst as cst
import libcst.matchers as m


def get_all_names(source_tree):
    class NameVisitor(cst.CSTVisitor):
        def __init__(self):
            self.names = set()

        def visit_Name(self, node: "Name") -> Optional[bool]:
            self.names.add(node.value)
            return True

    visitor = NameVisitor()
    source_tree.visit(visitor)
    return visitor.names


def has_same_name(node, target_names):
    class HasSameNameVisitor(cst.CSTVisitor):
        def __init__(self, target_names):
            self.has_name = False
            self.target_names = target_names

        def visit_Name(self, node: "Name") -> Optional[bool]:
            # print(node, self.target_names)
            if node.value in self.target_names:
                self.has_name = True
            return True

    visitor = HasSameNameVisitor(target_names)
    node.visit(visitor)
    return visitor.has_name


def has_call(node):
    class HasCallVisitor(cst.CSTVisitor):
        def __init__(self):
            self.has_call = False

        def visit_Call(self, node: "Name") -> Optional[bool]:
            self.has_call = True
            return

    visitor = HasCallVisitor()
    node.visit(visitor)
    return visitor.has_call


def has_new_line(node):
    class NewLineVisitor(cst.CSTVisitor):
        def __init__(self):
            self.has_new_line = False

        def visit_TrailingWhitespace(self, node: "TrailingWhitespace") -> Optional[bool]:
            if m.matches(node.newline, m.Newline()):
                self.has_new_line = True
            return True

    visitor = NewLineVisitor()
    node.visit(visitor)
    return visitor.has_new_line

def has_comment(node):
    class CommentVisitor(cst.CSTVisitor):
        def __init__(self):
            self.has_comment = False

        def visit_Comment(self, node: "Comment") -> Optional[bool]:
            self.has_comment = True
            return True

    visitor = CommentVisitor()
    node.visit(visitor)
    return visitor.has_comment

def has_yield(node):
    class YieldVisitor(cst.CSTVisitor):
        def __init__(self):
            self.has_yield = False

        def visit_Yield(self, node: "Yield") -> Optional[bool]:
            self.has_yield = True
            return True

    visitor = YieldVisitor()
    node.visit(visitor)
    return visitor.has_yield

