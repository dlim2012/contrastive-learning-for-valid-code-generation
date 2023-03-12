"""
Comments starting with #
Unassigned strings
"""
import random
from typing import Union

import libcst as cst
import libcst.matchers as m
from libcst import RemovalSentinel, Comment, FlattenSentinel
from libcst.metadata import ParentNodeProvider


class RemoveCommentsTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, p):
        # stack for storing the canonical name of the current function
        self.p = p
        self.num_changes = 0

    def get_logs(self):
        return {"remove_comments": self.num_changes}

    def leave_Comment(
            self, original_node: "Comment", updated_node: "Comment"
    ) -> "Comment":
        if self.p != 1 and random.random() > self.p:
            return updated_node
        self.num_changes += 1
        return RemovalSentinel(RemovalSentinel.REMOVE)

    def leave_Expr(
            self, original_node: "Expr", updated_node: "Expr"
    ) -> Union[
        "BaseSmallStatement", FlattenSentinel["BaseSmallStatement"], RemovalSentinel
    ]:
        if self.p != 1 and random.random() > self.p:
            return updated_node
        if m.matches(updated_node.value, m.SimpleString()):
            return RemovalSentinel(RemovalSentinel.REMOVE)
        return updated_node


if __name__ == "__main__":
    source = '''# this is a comment
s = """this string"""
def func(source, p=1):
    """
    This function has two parameters and returns None
    :param source: first parameter
    :param p: second parameter
    :return: None
    """
    return
a   =    1 # assign 1 to a

b = 1'''

    from preprocess.transform.utils.tools import transform, print_code_diff

    p = 0.5
    fixed, num_changes = transform(source, RemoveCommentsTransformer, (p,))

    print_code_diff(source, fixed)
    cst.parse_module(fixed)
    print(num_changes)
