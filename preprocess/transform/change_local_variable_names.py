"""
Changing local variable names in function definitions when nonlocal is not used in a child scope
"""

import random
from typing import Union

import libcst as cst
import libcst.matchers as m
from libcst import FlattenSentinel, RemovalSentinel

from preprocess.transform.utils.new_names import NameGenerator
from preprocess.transform.utils.transform_node import modify_local_variable_names
from preprocess.transform.utils.visit import get_local_assigntarget_names, get_param_names, get_non_local_names


class ChangeLocalVariableNameTransformer(cst.CSTTransformer):

    def __init__(self, name_generator, p=1):
        # stack for storing the canonical name of the current function
        self.name_generator = name_generator

        self.p = p
        self.num_changes = 0

    def get_logs(self):
        return {"change_variable_names": self.num_changes}

    def get_updated_name(self, reference):
        if self.p == 1 or random.random() < self.p:
            updated_name = self.name_generator.new_name()
            self.num_changes += 1
        else:
            updated_name = reference
        return updated_name

    def leave_Name(
            self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        return updated_node

    def leave_FunctionDef(
            self, original_node: "FunctionDef", updated_node: "FunctionDef"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], RemovalSentinel]:

        if not m.matches(original_node.body, m.IndentedBlock()):
            return updated_node

        local_exclude_names = {updated_node.name.value} \
                              | get_param_names(updated_node.params) \
                              | get_non_local_names(updated_node)
        maybe_include_names = get_local_assigntarget_names(original_node.body)

        updated_names = {}
        for name in maybe_include_names:
            if name in local_exclude_names:
                continue
            updated_names[name] = self.get_updated_name(name)

        updated_node = modify_local_variable_names(updated_node, updated_names)

        return updated_node


if __name__ == "__main__":
    source = '''
def transform(source, transformer_class, args, get_metadata=None, parse_test=False):
    try:
        source_module = cst.parse_module(a=source)
    except:
        raise ValueError("Source code could not be parsed")
    if get_metadata:
        wrapper, metadata = get_metadata[0](source_module, *get_metadata[1:])
        transformer = transformer_class(metadata, *args)
    else:
        wrapper = cst.metadata.MetadataWrapper(source_module)
        transformer = transformer_class(*args)

    visit(transformer=1)
    fixed = wrapper.wt.visit(transformer).code
    fixed = wrapper.wt.visit(args.transformer).code
    fixed = wrapper.wt.visit(transformer.args).code
    fixed = wrapper.wt.visit(transformer=[]).code
    if parse_test:
        try:
            cst.parse_module(fixed)
        except:
            print_code_diff(source, fixed, show_diff=True)
    return fixed, transformer.get_logs()
    '''

    source = '''
def func():
    a = 1
    def func2():
        nonlocal a
        return
    global b
    '''


    from preprocess.transform.utils.tools import transform, print_code_diff

    name_generator = NameGenerator(cst.parse_module(source), set())

    p = 0.2
    args = (name_generator, p)
    fixed, num_changes = transform(source, ChangeLocalVariableNameTransformer, args)

    print_code_diff(source, fixed)
    cst.parse_module(fixed)
    print(num_changes)
