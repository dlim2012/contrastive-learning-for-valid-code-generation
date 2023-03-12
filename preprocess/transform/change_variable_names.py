import random

import libcst as cst
import libcst.matchers as m
from libcst.metadata import ParentNodeProvider
from preprocess.transform.utils.new_names import NameGenerator


# todo
class ChangeVariableNameTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, p=1, exclude_builtin=True):
        # stack for storing the canonical name of the current function
        self.name_generator = NameGenerator(None, set())
        self.exclude_builtin = exclude_builtin
        self.p = p
        self.num_changes = 0
        self.updated_names = {}

    def get_logs(self):
        return {"change_variable_names": self.num_changes}

    def get_updated_name(self, reference):
        if self.exclude_builtin and self.name_generator.is_name_preserved(reference):
            return reference
        updated_name = self.updated_names.get(reference, "")
        if not updated_name:
            if self.p == 1 or random.random() < self.p:
                updated_name = self.updated_names[reference] = self.name_generator.new_name()
                self.num_changes += 1
            else:
                updated_name = self.updated_names[reference] = reference
        return updated_name

    def leave_Name(
            self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:

        # exclude names from external files
        parent = self.get_metadata(ParentNodeProvider, original_node)
        if m.matches(parent, m.ImportFrom()) or m.matches(parent, m.ImportAlias()):
            return updated_node

        updated_name = self.get_updated_name(original_node.value)
        return updated_node.with_changes(value=updated_name)


if __name__ == "__main__":
    source = '''
from tools import *
from utils import split_lines, tokenize_lines as tokenize

a = []

class PythonToken(Token):
    def __init__(self):
        super.__init__()
        self.tokens = []

    def __repr__(self):
        lines = split_lines(a, keepends=True)
        return ('TokenInfo(type=%s, string=%r, start_pos=%r, prefix=%r)' %
                self._replace(type=self.type.name))
                
a = PythonToken().__repr__()
    '''


    from preprocess.transform.utils.tools import transform, print_code_diff
    from preprocess.transform.utils.new_names import NameGenerator

    try:
        source_tree = cst.parse_module(source)
    except:
        raise ValueError("Source code could not be parsed")

    name_generator = NameGenerator(source_tree, set())
    p = 1
    args = (p,)
    fixed, num_changes = transform(source, ChangeVariableNameTransformer, args)

    print_code_diff(source, fixed)
    cst.parse_module(fixed)
    print(num_changes)
