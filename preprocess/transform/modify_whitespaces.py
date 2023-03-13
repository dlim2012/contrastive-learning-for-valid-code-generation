"""
Add or remove blanks
"""
import random
from typing import Union

import libcst as cst
from libcst import MaybeSentinel


class ModifyWhiteSpaceTransformer(cst.CSTTransformer):

    def __init__(self, mode: Union[bool, str] = True, p=1):
        # stack for storing the canonical name of the current function
        self.p = p
        self.mode = mode
        self.num_changes = 0

    def get_logs(self):
        if self.mode == True:
            text = "add_whitespace"
        elif self.mode == False:
            text = "remove_whitespace"
        else:
            text = "set_whitespace_" + len(self.mode)
        return {text: self.num_changes}

    def leave_SimpleWhitespace(
            self, original_node: "SimpleWhitespace", updated_node: "SimpleWhitespace"
    ) -> Union["BaseParenthesizableWhitespace", MaybeSentinel]:
        if self.p != 1 and random.random() > self.p:
            return updated_node
        if self.mode == True:
            self.num_changes += 1
            return updated_node.with_changes(
                value=original_node.value + ' '
            )
        elif self.mode == False:
            self.num_changes += 1
            if len(updated_node.value) <= 1:
                return updated_node
            return updated_node.with_changes(
                value=updated_node.value[:-1]
            )
        else:
            if self.mode != updated_node.value:
                self.num_changes += 1
            return updated_node.with_changes(
                value=self.mode
            )


if __name__ == "__main__":
    source = '''# this is a comment
a=  1 # assign 1 to a
self . func(  a , 
 b )
'''
    from preprocess.transform.utils.tools import transform, print_code_diff

    p = 1
    for add in [True, False]:
        fixed, num_changes = transform(source, ModifyWhiteSpaceTransformer, (add, p,))

        print_code_diff(source, fixed)
        cst.parse_module(fixed)
        print(num_changes)
