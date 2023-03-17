import difflib
from collections import defaultdict
from typing import Dict, Union, Set

import libcst as cst

from preprocess.transform.utils.new_names import NameGenerator


def transform(source, transformer_class, args, get_metadata=None, parse_test=False):
    try:
        source_module = cst.parse_module(source)
    except:
        raise ValueError("Source code could not be parsed")
    if get_metadata:
        wrapper, metadata = get_metadata[0](source_module, *get_metadata[1:])
        transformer = transformer_class(metadata, *args)
    else:
        wrapper = cst.metadata.MetadataWrapper(source_module)
        transformer = transformer_class(*args)

    try:
        fixed = wrapper.visit(transformer).code
    except:
        print(args)
        print(source)
        raise RuntimeError()

    if parse_test:
        try:
            cst.parse_module(fixed)
        except:
            print(args)
            print_code_diff(source, fixed, show_diff=True)
            raise ValueError()
    return fixed, transformer.get_logs()


def get_name_generator(source_module, preserved_names):
    name_generator = NameGenerator(source_module, preserved_names)
    wrapper = cst.metadata.MetadataWrapper(source_module)
    return wrapper, name_generator


def get_unused_imports(source_module):
    wrapper = cst.metadata.MetadataWrapper(source_module)
    scopes = set(wrapper.resolve(cst.metadata.ScopeProvider).values())
    unused_imports: Dict[Union[cst.Import, cst.ImportFrom], Set[str]] = defaultdict(set)
    for scope in scopes:
        for assignment in scope.assignments:
            node = assignment.node
            if isinstance(assignment, cst.metadata.Assignment) and isinstance(
                    node, (cst.Import, cst.ImportFrom)
            ):
                if len(assignment.references) == 0:
                    unused_imports[node].add(assignment.name)
    return wrapper, unused_imports


def get_undefined_references(source):
    wrapper = cst.metadata.MetadataWrapper(cst.parse_module(source))
    scopes = set(wrapper.resolve(cst.metadata.ScopeProvider).values())
    ranges = wrapper.resolve(cst.metadata.PositionProvider)
    undefined_references: Dict[cst.CSTNode, Set[str]] = defaultdict(set)
    references = defaultdict(set)
    for scope in scopes:

        for assignment in scope.assignments:
            node = assignment.node
            for access in scope.accesses:
                references[node].add(assignment.name)
                if len(access.referents) == 0:
                    undefined_references[node].add(assignment.name)
                    node = access.node
                    location = ranges[node].start
                    print(
                        f"Warning on line {location.line:2d}, column {location.column:2d}: Name reference `{node.value}` is not defined."
                    )
    return wrapper, undefined_references


def print_code_diff(code1, code2, show_diff=False, show_codes=True):
    print('==================================================================')
    if show_diff:
        print(
            "".join(
                difflib.unified_diff(code1.splitlines(1), code2.splitlines(1))
            )
        )
        print('------------------------------------------------------------------')
    if show_codes:
        print(code1)
        print('------------------------------------------------------------------')
        print(code2)
    print('==================================================================')
