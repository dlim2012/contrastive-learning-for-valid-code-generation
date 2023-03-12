"""
Empty lines
"""
import random
from typing import Union

import libcst as cst
from libcst import FlattenSentinel, RemovalSentinel


class RemoveEmptyLineTransformer(cst.CSTTransformer):

    def __init__(self, p):
        # stack for storing the canonical name of the current function
        self.p = p
        self.num_changes = 0

    def get_logs(self):
        return {"remove_empty_line": self.num_changes}

    def leave_EmptyLine(
            self, original_node: "EmptyLine", updated_node: "EmptyLine"
    ) -> Union["EmptyLine", FlattenSentinel["EmptyLine"], RemovalSentinel]:
        # remove empty line if no comment
        if self.p != 1 and random.random() > self.p:
            return updated_node
        if not updated_node.comment:
            self.num_changes += 1
            return FlattenSentinel([])
        return updated_node


if __name__ == "__main__":
    source = '''# this is a comment
    
a   =    1 # assign 1 to a

b = 1'''
    from preprocess.transform.utils.tools import transform, print_code_diff

    p = 1
    fixed, num_changes = transform(source, RemoveEmptyLineTransformer, (p,))

    print_code_diff(source, fixed)
    cst.parse_module(fixed)
    print(num_changes)
