from typing import Optional

import libcst as cst
import libcst.matchers as m


def get_all_names(node):
    class NameVisitor(cst.CSTVisitor):
        def __init__(self):
            self.names = set()

        def visit_Name(self, node: "Name") -> Optional[bool]:
            self.names.add(node.value)
            return True

    visitor = NameVisitor()
    node.visit(visitor)
    return visitor.names


def get_local_assigntarget_names(node):
    class GetLocalAssignTargetNames(cst.CSTVisitor):
        def __init__(self):
            self.names = set()

        def visit_FunctionDef(self, node: "FunctionDef") -> Optional[bool]:
            return False

        def visit_ClassDef(self, node: "ClassDef") -> Optional[bool]:
            return False

        def visit_CompFor(self, node: "CompFor") -> Optional[bool]:
            return False

        def visit_AssignTarget(self, node: "AssignTarget") -> Optional[bool]:
            if m.matches(node.target, m.Tuple()):
                for element in node.target.elements:
                    if m.matches(element.value, m.Name()):
                        self.names.add(element.value.value)
            elif m.matches(node.target, m.Name()):
                self.names.add(node.target.value)
            return True

    visitor = GetLocalAssignTargetNames()
    node.visit(visitor)
    return visitor.names


def get_param_names(node):
    class GetParamNames(cst.CSTVisitor):
        def __init__(self):
            self.names = set()

        def visit_Param(self, node: "Param") -> Optional[bool]:
            self.names.add(node.name.value)
            return True

    visitor = GetParamNames()
    node.visit(visitor)
    return visitor.names


def get_non_local_names(node):
    class NonLocalAndGlobalNameVisitor(cst.CSTVisitor):
        def __init__(self):
            self.name = set()

        def visit_Nonlocal(self, node: "Nonlocal") -> Optional[bool]:
            self.name |= get_all_names(node)
            return True

        def visit_Global_semicolon(self, node: "Global") -> None:
            self.name |= get_all_names(node)
            return True

    visitor = NonLocalAndGlobalNameVisitor()
    node.visit(visitor)
    return visitor.name


def has_same_name(node, target_names):
    class HasSameNameVisitor(cst.CSTVisitor):
        def __init__(self, target_names):
            self.has_name = False
            self.target_names = target_names

        def visit_Name(self, node: "Name") -> Optional[bool]:
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
