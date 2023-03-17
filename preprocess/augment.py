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

import os
import gzip
import json
from datetime import date
from multiprocessing import Pool, cpu_count
from tqdm_pathos import starmap
from tqdm import tqdm
from argparse import ArgumentParser

def parse_CodeSearchNet():
    parser = ArgumentParser()

    parser.add_argument('--n', '-n', type=int, default=5,
                       help='Number of transformation for each source code')
    parser.add_argument('--p', '-p', type=float, default=0.2,
                        help='Probability of transformation')
    parser.add_argument('--data_python_dir', '-d', type=str, default="../data/CodeSearchNet/resources/data/python",
                        help='data dir')
    parser.add_argument('--mode', '-m', type=str, default='train',
                        help='subfolder name')
    parser.add_argument('--filename', '-fn', type=str, default="python_train_0",
                        help='filename')
    parser.add_argument('--postfix', '-pf', type=str, default='',
                        help='postfix to save path')

    args = parser.parse_args()
    today = date.today().strftime("%m%d%y")

    # read path
    data_python_original_dir = os.path.join(args.data_python_dir, "final", "jsonl")
    source_filename = args.filename + '.jsonl.gz'
    read_path = os.path.join(data_python_original_dir, args.mode, source_filename)

    # save path
    data_python_augmented_dir = os.path.join(args.data_python_dir, "augmented")
    save_dir = os.path.join(data_python_augmented_dir, args.mode, args.filename, today)
    save_name = f"augmented_{'p%.2f' % args.p}_{'n%d' % args.n}{'_' + args.postfix if args.postfix else ''}.json"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, save_name)

    info = {
            'source_filename': source_filename,
            'date': today,
            'n_augmented': args.n,
            'p': args.p
        }
    return args, (read_path, save_path, info)

def augment(
        source,
        transformers=None,
        temp=1,
        preserved_names=None,
        parse_test=True
):
    try:
        source_tree = cst.parse_module(source)
    except:
        raise ValueError("Source code could not be parsed")

    if not transformers:
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
    for args in transformers:
        fixed, num_changes = transform(source, *args, **{'parse_test': parse_test})

        log.update(num_changes)
        source = fixed
    return fixed, log

def generate(args, read_path, save_path, info):
    n, p = args.n, args.p

    with gzip.open(read_path, "r") as f:
        data = f.read().decode('utf-8')

        def filter_valid_parse(line):
            item = json.loads(line)
            try:
                cst.parse_module(item["code"])
                return item
            except:
                return None

        lines = [[line] for line in data.split('\n')]
        json_list = [item for item in starmap(filter_valid_parse, lines) if item]

    results = starmap(
            augment,
            [(json_item['code'], [], p, None, True) for json_item in json_list for _ in range(n)]
        )

    new_json_list = []
    for i, item in enumerate(json_list):
        new_json_item = {
            'original': item,
            'augmented': [
                {
                    'code': results[i * n + j][0],
                    'log': results[i * n + j][1]
                } for j in range(n)
            ]
        }
        new_json_list.append(new_json_item)


    to_save = {
        'transform_info': info,
        'data': new_json_list
    }

    with open(save_path, 'w') as f:
        f.write(json.dumps(to_save))
    print(f'Saved: {save_path}')

def read_generated(save_path):
    with open(save_path, 'r') as f:
        data = json.load(f)
        print(type(data))

if __name__ == '__main__':

    args, (read_path, save_path, info) = parse_CodeSearchNet()

    generate(args, read_path, save_path, info)

    read_generated(save_path)

