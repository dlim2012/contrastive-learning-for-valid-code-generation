"""
Removing unused imports
Modified from a source code provided in the documentation of LibCST
"""

import random
from typing import Dict, Union, Set

import libcst as cst

from preprocess.transform.utils.tools import get_unused_imports


class RemoveUnusedImportTransformer(cst.CSTTransformer):
    def __init__(
            self, unused_imports: Dict[Union[cst.Import, cst.ImportFrom], Set[str]],
            p
    ) -> None:
        self.unused_imports = unused_imports
        self.p = p
        self.num_changes = 0

    def get_logs(self):
        return {"remove_unused_imports": self.num_changes}

    def leave_import_alike(
            self,
            original_node: Union[cst.Import, cst.ImportFrom],
            updated_node: Union[cst.Import, cst.ImportFrom],
    ) -> Union[cst.Import, cst.ImportFrom, cst.RemovalSentinel]:
        if original_node not in self.unused_imports:
            return updated_node
        names_to_keep = []
        for name in updated_node.names:
            asname = name.asname
            if asname is not None:
                name_value = asname.name.value
            else:
                name_value = name.name.value
            if name_value not in self.unused_imports[original_node] or (self.p != 1 and random.random() > self.p):
                names_to_keep.append(name.with_changes(comma=cst.MaybeSentinel.DEFAULT))
            else:
                self.num_changes += 1
        if len(names_to_keep) == 0:
            return cst.RemoveFromParent()
        else:
            return updated_node.with_changes(names=names_to_keep)

    def leave_Import(
            self, original_node: cst.Import, updated_node: cst.Import
    ) -> cst.Import:
        return self.leave_import_alike(original_node, updated_node)

    def leave_ImportFrom(
            self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        return self.leave_import_alike(original_node, updated_node)


if __name__ == '__main__':
    source = """\
import a, b, c as d, e as f  # expect to keep: a, c as d
from g import h, i, j as k, l as m  # expect to keep: h, j as k
from n import o  # expect to be removed entirely

a()

def fun():
    d()

class Cls:
    att = h.something

    def __new__(self) -> "Cls":
        var = k.method()
        func_undefined(var_undefined)
        fun()
    """
    from preprocess.transform.utils.tools import transform, print_code_diff

    p = 1
    fixed, num_changes = transform(source, RemoveUnusedImportTransformer, (p,), get_unused_imports)

    print_code_diff(source, fixed)
    cst.parse_module(fixed)
    print(num_changes)
