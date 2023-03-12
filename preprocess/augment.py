import random

import libcst as cst

from preprocess.transform.add_new_lines import AddNewLineTransformer
from preprocess.transform.add_remove_commas import CommaTransformer
from preprocess.transform.change_comp_to_for import ChangeCompToForTransformer
from preprocess.transform.change_for_range_to_while import ForToWhileTransformer
from preprocess.transform.change_lambda_to_function import LambdaToFunctionTransformer
from preprocess.transform.combine_statements import CombineStatementsTransformer
from preprocess.transform.modify_whitespaces import ModifyWhiteSpaceTransformer
from preprocess.transform.remove_comments import RemoveCommentsTransformer
from preprocess.transform.remove_empty_lines import RemoveEmptyLineTransformer
from preprocess.transform.remove_unused_imports import RemoveUnusedImportTransformer
from preprocess.transform.utils.new_names import NameGenerator
from preprocess.transform.utils.tools import get_unused_imports, transform
from preprocess.transform.change_variable_names import ChangeVariableNameTransformer


def augment(source, temp=1, parse_test=False):
    try:
        source_tree = cst.parse_module(source)
    except:
        raise ValueError("Source code could not be parsed")

    name_generator = NameGenerator(source_tree, set())

    args_list = [
        (AddNewLineTransformer, (temp,)),
        (CommaTransformer, (True, temp)),
        (CommaTransformer, (False, temp)),
        (ChangeCompToForTransformer, ("list", name_generator, temp)),
        (ChangeCompToForTransformer, ("set", name_generator, temp)),
        (ChangeCompToForTransformer, ("dict", name_generator, temp)),
        (ChangeVariableNameTransformer, (temp,)),
        (ForToWhileTransformer, (name_generator, temp)),
        (LambdaToFunctionTransformer, (temp,)),
        (CombineStatementsTransformer, (temp, temp,)),
        (ModifyWhiteSpaceTransformer, (True, 0.1 * temp,)),
        (ModifyWhiteSpaceTransformer, (False, 0.1 * temp,)),
        (RemoveCommentsTransformer, (temp,)),
        (RemoveEmptyLineTransformer, (temp,)),
        (RemoveUnusedImportTransformer, (temp,), get_unused_imports)
    ]

    log = {}
    random.shuffle(args_list)
    for args in args_list:
        try:
            fixed, num_changes = transform(source, *args, **{'parse_test': parse_test})
        except:
            print(args)
            print(source)
            raise ValueError()


        log.update(num_changes)
        source = fixed

    return fixed, log


if __name__ == '__main__':
    import os
    import gzip
    import json
    data_python_dir = "../data/CodeSearchNet/resources/data/python"
    data_python_original_dir = os.path.join(data_python_dir, "final", "jsonl")
    data_python_train_dir = os.path.join(data_python_original_dir, "train")
    filename = "python_train_0"
    extension = ".jsonl.gz"

    json_data = []
    with gzip.open(os.path.join(data_python_train_dir, filename + extension), "r") as f:
        data = f.read().decode('utf-8')
        for line in data.split('\n'):
            json_data.append(json.loads(line))

    new_data = []
    for json_item in json_data:
        source = json_item["code"]
        try:
            cst.parse_module(source)
        except:
            continue

        try:
            fixed, log = augment(source, 0.2)
        except Exception as e:
            print(e)

        new_json_item = dict()
        new_json_item["source_code"] = source
        new_json_item["augmented_code"] = fixed
        new_json_item["log"] = log
        new_data.append(new_json_item)

    save_dir = os.path.join(data_python_dir, "augmented")

    with open(save_dir, 'w') as f:
        f.write(json.dumps(new_data))




