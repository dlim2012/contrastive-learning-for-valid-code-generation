"""
for loop over a variable -> did not implemented because the variable can be both sequence and iterable
"""

import random
from typing import Union

import libcst as cst
import libcst.matchers as m
from libcst import RemovalSentinel, FlattenSentinel

from preprocess.transform.utils.create_node import create_assign_statement, create_add_statement


class ForToWhileTransformer(cst.CSTTransformer):

    def __init__(self, name_generator, p):
        # stack for storing the canonical name of the current function
        self.name_generator = name_generator
        self.p = p
        self.num_changes = 0

    def get_logs(self):
        return {"for_to_while": self.num_changes}

    def leave_For(
            self, original_node: "For", updated_node: "For"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], RemovalSentinel]:

        if self.p != 1 and random.random() > self.p:
            return updated_node
        if m.matches(updated_node.iter, m.Call()):
            func = updated_node.iter.func
            if m.matches(func, m.Name()):
                args = updated_node.iter.args
                if func.value == "range":
                    if len(args) == 1:
                        start, stop, step = cst.Integer("0"), args[0].value, cst.Integer("1")
                    elif len(args) == 2:
                        start, stop, step = args[0].value, args[1].value, cst.Integer("1")
                    else:
                        start, stop, step = args[0].value, args[1].value, args[2].value

                    target = updated_node.target
                    init_line = create_assign_statement(target, start, updated_node.leading_lines)
                    aug_line = create_add_statement(target.deep_clone(), step)

                    if m.matches(updated_node.body, m.SimpleStatementSuite()):
                        new_body = [cst.SimpleStatementLine(updated_node.body.body)]
                        indented_block = cst.IndentedBlock(
                            body=new_body
                        )
                    else:
                        indented_block = updated_node.body.with_changes(
                            body=tuple(list(updated_node.body.body) + [aug_line])
                        )

                    while_statement = cst.While(
                        cst.Comparison(
                            left=target.deep_clone(),
                            comparisons=(cst.ComparisonTarget(
                                operator=cst.LessThan(),
                                comparator=stop
                            ),)
                        ),
                        indented_block
                    )
                    self.num_changes += 1
                    return FlattenSentinel([init_line, while_statement])
        elif m.matches(updated_node.iter, m.Name()):
            # the loop may be over a generator or a variable
            return updated_node
        return updated_node


"""
v0 = 0
"""
if __name__ == "__main__":
    source = '''
for i in range(5):
    print("*")
    
for i in a:
    print(i)
for i in range(5): print("*")
    
for i in range(1, 5, 2):
    print("*")
    
    
for i, num in enumerate(a, 2):
    print("*")
    '''

    from preprocess.transform.utils.tools import transform, print_code_diff
    from preprocess.transform.utils.new_names import NameGenerator

    try:
        source_tree = cst.parse_module(source)
    except:
        raise ValueError("Source code could not be parsed")

    name_generator = NameGenerator(source_tree, set())
    p = 1
    args = (name_generator, p,)
    fixed, num_changes = transform(source, ForToWhileTransformer, args)

    print_code_diff(source, fixed)
    cst.parse_module(fixed)
    print(num_changes)
