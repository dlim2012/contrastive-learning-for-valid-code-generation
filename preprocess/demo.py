import random

import libcst as cst

from preprocess.transform.add_new_lines import AddNewLineTransformer
from preprocess.transform.add_remove_commas import CommaTransformer
from preprocess.transform.change_comp_to_for import ChangeCompToForTransformer
from preprocess.transform.change_for_range_to_while import ForToWhileTransformer
from preprocess.transform.change_lambda_to_function import LambdaToFunctionTransformer
from preprocess.transform.change_local_variable_names import ChangeLocalVariableNameTransformer
from preprocess.transform.combine_statements import CombineStatementsTransformer
from preprocess.transform.modify_whitespaces import ModifyWhiteSpaceTransformer
from preprocess.transform.remove_comments import RemoveCommentsTransformer
from preprocess.transform.remove_empty_lines import RemoveEmptyLineTransformer
from preprocess.transform.remove_unused_imports import RemoveUnusedImportTransformer
from preprocess.transform.utils.tools import get_unused_imports, transform, get_name_generator


def augment(source, temp=1, preserved_names: dict = None, parse_test=False):
    try:
        source_tree = cst.parse_module(source)
    except:
        raise ValueError("Source code could not be parsed")

    transformers = [
        (AddNewLineTransformer, (temp,)),
        (CommaTransformer, (True, temp)),
        (CommaTransformer, (False, temp)),
        (ChangeCompToForTransformer, ("list", temp), (get_name_generator, preserved_names,)),
        (ChangeCompToForTransformer, ("set", temp), (get_name_generator, preserved_names,)),
        (ChangeCompToForTransformer, ("dict", temp), (get_name_generator, preserved_names,)),
        (ChangeLocalVariableNameTransformer, (temp,), (get_name_generator, preserved_names,)),
        (ForToWhileTransformer, (temp,), (get_name_generator, preserved_names,)),
        (LambdaToFunctionTransformer, (temp,)),
        (CombineStatementsTransformer, (temp, temp,)),
        (ModifyWhiteSpaceTransformer, (True, 0.1 * temp,)),
        (ModifyWhiteSpaceTransformer, (False, 0.1 * temp,)),
        (RemoveCommentsTransformer, (temp,)),
        (RemoveEmptyLineTransformer, (temp,)),
        (RemoveUnusedImportTransformer, (temp,), (get_unused_imports,))
    ]
    log = {}
    random.shuffle(transformers)
    for transformer in transformers:
        fixed, num_changes = transform(source, *transformer, **{'parse_test': parse_test})
        log.update(num_changes)
        source = fixed

    return fixed, log


if __name__ == '__main__':

    source = '''
from p1.p2.p3 import p4 as p5
from type_names import type_name
def expand_compositor_keys(cls, spec):
    """
    Expands compositor definition keys into {type}.{group}
    keys. For instance a compositor operation returning a group
    string 'Image' of element type RGB expands to 'RGB.Image'.
    """
    expanded_spec={}
    applied_keys = []
    compositor_defs = {el.group:el.output_type.__name__
                       for el in Compositor.definitions}
    for key, val in spec.items():
        if key not in compositor_defs:
            expanded_spec[key] = val
        else:
            # Send id to Overlays
            applied_keys = ['Overlay']
            type_name = compositor_defs[key]
            expanded_spec[str(type_name+'.'+key)] = val
    return expanded_spec, applied_keys
    '''
    while True:
        fixed, log = augment(source, parse_test=True)
        from preprocess.transform.utils.tools import print_code_diff

        cst.parse_module(fixed)
        break

    print_code_diff(source, fixed, show_diff=True)
    print(log)
    for key in sorted(log.keys()):
        print('%-25s: %s' % (key, log[key]))

    print({key: log[key] for key in sorted(log.keys())})
