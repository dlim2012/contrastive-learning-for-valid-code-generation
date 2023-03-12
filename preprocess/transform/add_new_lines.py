"""
Changing one new line to two new lines
"""
import random

import libcst as cst


class AddNewLineTransformer(cst.CSTTransformer):
    # METADATA_DEPENDENCIES = (ParentNodeProvider, )

    class MyNewline(cst.Newline):
        def _validate(self) -> None:
            pass

    def __init__(self, p):
        # stack for storing the canonical name of the current function
        self.p = p
        self.num_changes = 0

    def get_logs(self):
        return {"add_new_lines": self.num_changes}

    def leave_Newline(
            self, original_node: "Newline", updated_node: "Newline"
    ) -> "MyNewline":
        if self.p != 1 and random.random() > self.p:
            return updated_node
        return self.MyNewline("\n\n")


if __name__ == "__main__":
    source = '''# this is a comment
a   =    1 # assign 1 to a
b = 1'''
    from preprocess.transform.utils.tools import transform, print_code_diff

    p = 1
    fixed, num_changes = transform(source, AddNewLineTransformer, (p,))

    print_code_diff(source, fixed)
    cst.parse_module(fixed)
    print(num_changes)
