"""
Add or remove commas only inside tuple, list, set, or dictionaries
Assignments with multiple target or value are tuples without parenthesis
"""
import random

import libcst as cst
import libcst.matchers as m
from libcst import MaybeSentinel


class CommaTransformer(cst.CSTTransformer):

    def __init__(self, add, p):
        # stack for storing the canonical name of the current function
        self.func = self.add_comma_alike if add else self.remove_comma_alike
        self.p = p
        self.num_changes = 0
        self.add = add

    def get_logs(self):
        return {"add_commas" if self.add else "remove_commas": self.num_changes}

    def add_comma_alike(self, updated_node):
        if not self.add:
            return updated_node
        if self.p != 1 and random.random() > self.p:
            return updated_node
        if len(updated_node.elements) > 0 and not m.matches(updated_node.elements[-1].comma, m.Comma()):
            self.num_changes += 1
            return updated_node.with_changes(
                elements=tuple(
                    list(updated_node.elements[:-1]) + [updated_node.elements[-1].with_changes(comma=cst.Comma())]
                )
            )
        return updated_node

    def remove_comma_alike(self, updated_node):
        if self.add:
            return updated_node
        if self.p != 1 and random.random() > self.p:
            return updated_node
        if len(updated_node.elements) > 0 and not m.matches(updated_node.elements[-1].comma, m.Comma()):
            self.num_changes += 1
            return updated_node.with_changes(
                elements=tuple(
                    list(updated_node.elements[:-1]) + [
                        updated_node.elements[-1].with_changes(comma=MaybeSentinel.DEFAULT)]
                )
            )
        return updated_node

    def leave_Tuple(
            self, original_node: "Tuple", updated_node: "Tuple"
    ) -> "BaseExpression":
        if self.add and not updated_node.lpar and len(updated_node.elements) <= 1:
            return updated_node
        return self.func(updated_node)

    def leave_Dict(
            self, original_node: "Dict", updated_node: "Dict"
    ) -> "BaseExpression":
        return self.func(updated_node)

    def leave_List(
            self, original_node: "List", updated_node: "List"
    ) -> "BaseExpression":
        return self.func(updated_node)

    def leave_Set(self, original_node: "Set", updated_node: "Set") -> "BaseExpression":
        return self.func(updated_node)


if __name__ == "__main__":
    source = '''# this is a comment
a,b   =    1,2 # assign 1 to a

'''
    source = '''
a, b = (1,2)
b = {2, 3}
c = {1:2  ,3 :4}
d = [1,2]
    '''
    from preprocess.transform.utils.tools import transform, print_code_diff

    for add in [True, False]:
        args = (add, 1,)
        fixed, num_changes = transform(source, CommaTransformer, args)

        print_code_diff(source, fixed)
        cst.parse_module(fixed)
        print(num_changes)
