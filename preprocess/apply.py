import os

from augment import augment

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


def apply(path, preserved_names):
    temp = 1
    args_list = [
        # (AddNewLineTransformer, (0.5 * temp,)),
        # (CommaTransformer, (True, temp)),
        # (CommaTransformer, (False, temp)),
        # (ChangeCompToForTransformer, ("list", temp), (get_name_generator, preserved_names,)),
        # (ChangeCompToForTransformer, ("set", temp), (get_name_generator, preserved_names,)),
        # (ChangeCompToForTransformer, ("dict", temp), (get_name_generator, preserved_names,)),
        # (ChangeLocalVariableNameTransformer, (temp,), (get_name_generator, preserved_names,)),
        # (ForToWhileTransformer, (temp,), (get_name_generator, preserved_names,)),
        # (LambdaToFunctionTransformer, (temp,)),
        (CombineStatementsTransformer, (temp, temp,)),
        # (ModifyWhiteSpaceTransformer, (True, 0.1 * temp,)),
        # (ModifyWhiteSpaceTransformer, (False, 0.1 * temp,)),
        # (RemoveCommentsTransformer, (temp,)),
        # (RemoveEmptyLineTransformer, (0.5 * temp,)),
    ]

    for name in os.listdir(path):
        new_path = os.path.join(path, name)

        if os.path.isdir(new_path):
            apply(new_path, preserved_names)
        elif os.path.isfile(new_path) and len(name) > 2 and name[-3:] == '.py':

            with open(new_path, 'r') as f:
                source = f.read()
            print(new_path)
            fixed, log = augment(source, args_list, 1, preserved_names)
            print(sorted(log.items()))
            with open(new_path, 'w') as f:
                f.write(fixed)
            print()


if __name__ == "__main__":
    base_dir = '/Users/imjeonghun/Downloads/696ds_test'

    apply(base_dir, {'augment'})
