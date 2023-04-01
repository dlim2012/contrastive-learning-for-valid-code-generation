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


def augment(
        source,
        args_list=None,
        temp=1,
        preserved_names=None,
        parse_test=True
):
    try:
        cst.parse_module(source)
    except:
        raise ValueError("Source code could not be parsed")

    if not args_list:
        args_list = [
            (AddNewLineTransformer, (0.5 * temp,)),
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
            (RemoveEmptyLineTransformer, (0.5 * temp,)),
            (RemoveUnusedImportTransformer, (temp,), (get_unused_imports,))
        ]

    log = {}
    random.shuffle(args_list)
    for args in args_list:
        fixed, num_changes = transform(source, *args, **{'parse_test': parse_test})

        log.update(num_changes)
        source = fixed

    return fixed, log



