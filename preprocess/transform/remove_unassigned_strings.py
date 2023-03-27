"""
Empty lines
"""
import random
from typing import Union

import libcst as cst
import libcst.matchers as m
from libcst import FlattenSentinel, RemovalSentinel


class RemoveUnassignedStringTransformer(cst.CSTTransformer):

    def __init__(self, p):
        # stack for storing the canonical name of the current function
        self.p = p
        self.num_changes = 0

    def get_logs(self):
        return {"remove_empty_line": self.num_changes}

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
    source = '''
"""
This is a doc string
"""
# this is a comment

a   =    1 # assign 1 to a

b = 1'''
    from preprocess.transform.utils.tools import transform, print_code_diff

    p = 1
    fixed, num_changes = transform(source, RemoveUnassignedStringTransformer, (p,))

    print_code_diff(source, fixed)
    cst.parse_module(fixed)
    print(num_changes)
