"""
Combines statement when
    1) any values being assigned are not in targets
    2) number of targets and number of values match
    +: Any statement with call will be forced to not combine any further
"""

"""
corner case "a, a, a = a + 1, a+ 1, a+ 1"
"""

"""
corner case
a = 2
a = 1
b = deepcopy(a)
------------------
a = 2
a, b = 1, deepcopy(a)
"""

import random
from typing import Union

import libcst as cst
import libcst.matchers as m
from libcst import RemovalSentinel, FlattenSentinel, MaybeSentinel
from libcst._types import CSTNodeT

from preprocess.transform.utils.create_node import create_assign_statement_plural, create_assign_plural
from preprocess.transform.utils.visit import get_all_names
from preprocess.transform.utils.visit import has_call, has_same_name, has_yield


class CombineStatementsTransformer(cst.CSTTransformer):
    """
    Combine statements if all criteria are met
    Else split statements
    """

    def __init__(self, split_ratio, p):
        # stack for storing the canonical name of the current function
        self.split_ratio = split_ratio
        self.p = p
        self.num_combines = 0

        self.targets, self.values, self.target_names = [], [], set()
        self.part, self.num_parts = None, 0
        self.new_body, self.new_body_element = [], []

    def get_logs(self):
        return {"combine_statement": self.num_combines}

    def _append_to_new_body_element(self, part=None):
        if self.num_parts == 1:
            self.new_body_element.append(self.part)
        elif self.targets:
            self.num_combines += 1
            self.new_body_element.append(create_assign_plural(self.targets, self.values))

        if part:
            self.new_body_element.append(part)

        self.targets, self.values, self.target_names = [], [], set()
        self.num_parts = 0

    def _append_to_new_body(self, part=None):
        if self.num_parts == 1:
            self.new_body.append(cst.SimpleStatementLine((self.part,)))
        elif self.targets:
            self.num_combines += 1
            self.new_body.append(create_assign_statement_plural(self.targets, self.values))

        if part:
            self.new_body.append(part)

        self.targets, self.values, self.target_names = [], [], set()
        self.num_parts = 0

    def on_leave(
            self, original_node: CSTNodeT, updated_node: CSTNodeT
    ) -> Union[CSTNodeT, RemovalSentinel, FlattenSentinel[CSTNodeT]]:
        if hasattr(updated_node, "body") and (
                m.matches(updated_node, m.Module()) or m.matches(updated_node, m.ClassDef()) or m.matches(updated_node,
                                                                                                          m.FunctionDef())):
            isIndentBlock = m.matches(updated_node.body, m.IndentedBlock())
            body = updated_node.body.body if isIndentBlock else updated_node.body

            if m.matches(body, m.SimpleStatementSuite()):
                return updated_node

            self.new_body = []
            self.targets, self.values, self.target_names = [], [], set()
            self.part, self.num_parts = None, 0
            for body_element in body:

                # stop randomly attempt to modify
                if self.p != 1 and random.random() > self.p:
                    self._append_to_new_body(body_element)
                    continue

                # stop if body_element is not a simple statement line
                if not m.matches(body_element, m.SimpleStatementLine()):
                    self._append_to_new_body(body_element)
                    continue

                self.new_body_element = []
                for part in body_element.body:

                    # stop if the part is not an assign node
                    if not m.matches(part, m.Assign()):
                        self._append_to_new_body_element(part)
                        continue

                    # stop if number of targets and values doesn't match (e.g., 't = 1, 2')
                    if m.matches(part.value, m.Tuple()):
                        if not m.matches(part.targets[0].target, m.Tuple()) \
                                or len(part.targets[0].target.elements) != len(part.value.elements):
                            self._append_to_new_body_element(part)
                            continue

                    # stop if any value that will be assigned is in the targets
                    for assign_target in part.targets:
                        self.target_names = self.target_names.union(get_all_names(assign_target))
                    if has_same_name(part.value, self.target_names):
                        self._append_to_new_body_element(part)
                        continue

                    # split if any value has keyword "yield"
                    if has_yield(part):
                        self._append_to_new_body(part)
                        continue

                    # split randomly with a pre-defined ratio
                    if (self.split_ratio != 1 and random.random() > self.split_ratio):
                        self._append_to_new_body_element()

                    self.num_parts += 1
                    self.part = part

                    # add variables in part to self.targets and self.values
                    for assign_target in part.targets:
                        if m.matches(assign_target.target, m.Tuple()):
                            for element in assign_target.target.elements:
                                self.targets.append(element)
                        else:
                            self.targets += [cst.Element(
                                assign_target.target,
                                comma=cst.Comma(whitespace_before=assign_target.whitespace_before_equal)
                            )]
                    if m.matches(part.value, m.Tuple()):
                        for i in range(len(part.targets)):
                            for element in part.value.elements:
                                self.values.append(element)
                    else:
                        if self.values:
                            self.values[-1] = self.values[-1].with_changes(comma=cst.Comma(
                                whitespace_before=cst.SimpleWhitespace('') if self.values[
                                                                                  -1].comma == MaybeSentinel.DEFAULT else
                                self.values[-1].comma.whitespace_before,
                                whitespace_after=assign_target.whitespace_after_equal
                            ))
                        self.values += [cst.Element(part.value)] * len(part.targets)

                    # split if there was any function call
                    if has_call(part):
                        self._append_to_new_body_element()

                if self.new_body_element:
                    self.new_body.append(body_element.with_changes(body=self.new_body_element))
                else:
                    # some comments and whitespace may be lost here
                    self.new_body += list(body_element.leading_lines)

            if self.targets:
                self._append_to_new_body()
            self.new_body = tuple(self.new_body)
            if isIndentBlock:
                self.new_body = updated_node.body.with_changes(body=self.new_body)
            return updated_node.with_changes(body=self.new_body)
        return updated_node


if __name__ == "__main__":
    source = '''
def func(a):
    return
a = func(b) #1
a = a # 2
a = 1 # 3
b = 1 # 4
p, q = r, s = t, u; f = lambda x: x
g = h


p = a; y = z;



func(a); b = c

x = 1
((a, b), (c,
d)) = get_values()



func(a)
a =    func(); b = func()

'''

    from preprocess.transform.utils.tools import transform, print_code_diff

    args = (1, 1,)
    fixed, num_changes = transform(source, CombineStatementsTransformer, args)

    print_code_diff(source, fixed)
    cst.parse_module(fixed)
    print(num_changes)
