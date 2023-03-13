import random
from typing import Union

import libcst as cst
import libcst.matchers as m
from libcst import RemovalSentinel, FlattenSentinel, MaybeSentinel
from libcst._types import CSTNodeT

from preprocess.transform.utils.create_node import create_assign_statement_plural, create_assign_statement
from preprocess.transform.utils.new_names import NameGenerator
from preprocess.transform.utils.visit import has_call, has_same_name, get_all_names


class ModifyAfterExtractionTransformer(cst.CSTTransformer):

    def __init__(self, value_types=None, target_types=None, modify_func=None, name_generator=None, p=1):
        # stack for storing the canonical name of the current function
        self.p = p
        self.value_types = value_types
        self.target_types = target_types
        self.modify_func = modify_func
        self.name_generator = name_generator
        self.num_changes = 0

    def match_value_type(self, value):
        for value_type in self.value_types:
            if m.matches(value, value_type):
                return True
        return False

    def match_target_type(self, target):
        for target_type in self.target_types:
            if m.matches(target, target_type):
                return True
        return False

    def criteria_check_from_body_element(self, element):
        if not m.matches(element, m.SimpleStatementLine()):
            return False

        count_type = 0
        count_type_with_call = 0

        for part in element.body:
            if m.matches(part, m.Assign()):
                ret1, ret2 = self.count_value_type_from_assign(part)
                if ret1 == -1:
                    return False
                count_type += ret1
                count_type_with_call += ret2
                if count_type_with_call > 1:
                    return False
        if count_type_with_call == 1:
            return count_type == 1
        return count_type > 0

    def count_value_type_from_assign(self, part):
        count_type = 0
        count_type_with_call = 0
        if hasattr(part, "value"):
            if m.matches(part.value, m.Tuple()):
                for element in part.value.elements:
                    if self.match_value_type(element.value):
                        count_type += 1
                        if has_call(element):
                            count_type_with_call += 1
                    else:
                        if has_call(element):
                            return -1, -1
            else:
                if self.match_value_type(part.value):
                    count_type += 1
                    if has_call(part):
                        count_type_with_call += 1
                else:
                    if has_call(part):
                        return -1, -1
        return count_type, count_type_with_call

    def on_leave(
            self, original_node: CSTNodeT, updated_node: CSTNodeT
    ) -> Union[CSTNodeT, RemovalSentinel, FlattenSentinel[CSTNodeT]]:
        if hasattr(updated_node, "body") and (
                m.matches(updated_node, m.Module())
                or m.matches(updated_node, m.ClassDef())
                or m.matches(updated_node, m.FunctionDef())):

            isIndentBlock = m.matches(updated_node.body, m.IndentedBlock())
            body = updated_node.body.body if isIndentBlock else updated_node.body

            if m.matches(body, m.SimpleStatementSuite()):
                return updated_node

            new_body = []

            for body_element in body:
                # criteria check
                # 1) at least one element has a type match
                # 2) if there is a call it should be in the only element that matches the type
                if self.criteria_check_from_body_element(body_element):
                    new_body += body_element.leading_lines
                    for part in body_element.body:
                        # check if assign statement has target cst type
                        if not self.count_value_type_from_assign(part):
                            new_body.append(cst.SimpleStatementLine(
                                (part.with_changes(semicolon=MaybeSentinel.DEFAULT)
                                 ,)))
                            continue
                        if m.matches(part, m.Assign()):

                            # do not split when any value being assigned is in one of the targets
                            target_names = set()
                            for assign_target in part.targets:
                                target_names = target_names.union(get_all_names(assign_target))
                            if has_same_name(part.value, target_names):
                                new_body.append(cst.SimpleStatementLine(
                                    (part.with_changes(semicolon=MaybeSentinel.DEFAULT)
                                     ,)))
                                continue

                            # for simplification, split only when each value is being assigned to one variable
                            # (e.g., "f1 = f2 = lambda x: x" will not be transformed)
                            if len(part.targets) != 1:
                                new_body.append(cst.SimpleStatementLine(
                                    (part.with_changes(semicolon=MaybeSentinel.DEFAULT)
                                     ,)))
                                continue

                            # randomly do not split with a pre-defined probability
                            if self.p != 1 and random.random() > self.p:
                                new_body.append(cst.SimpleStatementLine(
                                    (part.with_changes(semicolon=MaybeSentinel.DEFAULT)
                                     ,)))
                                continue

                            assign_target = part.targets[0]
                            assign_value = part.value
                            if m.matches(assign_target.target, m.Tuple()) and len(
                                    assign_target.target.elements) != 1:
                                # number of targets and values should match (plural)
                                if not m.matches(part.value, m.Tuple()) \
                                        or len(assign_target.target.elements) != len(part.value.elements):
                                    new_body.append(cst.SimpleStatementLine(
                                        (part.with_changes(semicolon=MaybeSentinel.DEFAULT)
                                         ,)))
                                    continue

                                target_elements = assign_target.target.elements
                                value_elements = assign_value.elements
                                targets, values = [], []
                                for target_element, value_element in zip(target_elements, value_elements):
                                    if self.match_value_type(value_element.value):
                                        if targets:
                                            new_body.append(create_assign_statement_plural(targets, values))
                                            targets, values = [], []
                                        if self.modify_func and self.target_types and self.match_target_type(
                                                target_element.value):
                                            self.num_changes += 1
                                            new_body += self.modify_func(target_element.value, value_element.value,
                                                                         self.name_generator)
                                        else:
                                            new_body.append(create_assign_statement_plural(
                                                [target_element], [value_element]))
                                    else:
                                        targets.append(target_element)
                                        values.append(value_element)
                                if targets:
                                    new_body.append(create_assign_statement_plural(targets, values))
                            else:
                                # number of targets and values should match (single)
                                if m.matches(part.value, m.Tuple()) and len(part.value.elements) != 1:
                                    new_body.append(cst.SimpleStatementLine(
                                        (part.with_changes(semicolon=MaybeSentinel.DEFAULT)
                                         ,)))
                                    continue

                                if self.match_value_type(assign_value):
                                    if self.modify_func and self.target_types and self.match_target_type(
                                            assign_target.target):
                                        self.num_changes += 1
                                        new_body += self.modify_func(assign_target.target, assign_value,
                                                                     self.name_generator)
                                        continue
                                new_body.append(create_assign_statement(
                                    assign_target.target, assign_value))
                        else:
                            new_body.append(cst.SimpleStatementLine(
                                (part.with_changes(semicolon=MaybeSentinel.DEFAULT),)))
                else:
                    new_body.append(body_element)

            new_body = tuple(new_body)
            if isIndentBlock:
                new_body = updated_node.body.with_changes(body=new_body)
            return updated_node.with_changes(body=new_body)
        return updated_node


def modify_after_extraction(source_tree, value_type, target_type, modify_func=None, name_generator=False, p=1):
    name_generator = NameGenerator(source_tree, set()) if name_generator else None
    transformer = ModifyAfterExtractionTransformer(value_type, target_type, modify_func, name_generator=name_generator,
                                                   p=p)
    fixed_module = source_tree.visit(transformer)
    return fixed_module, transformer.num_changes
