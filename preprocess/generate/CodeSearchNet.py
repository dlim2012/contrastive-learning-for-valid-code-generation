
import os
import gzip
import json
from datetime import date
from tqdm_pathos import starmap
import libcst as cst

from preprocess.transform.remove_unassigned_strings import RemoveUnassignedStringTransformer
from preprocess.transform.utils.tools import transform
from preprocess.augment import augment

from argparse import ArgumentParser

def parse_CodeSearchNet():
    parser = ArgumentParser()

    parser.add_argument('--p', '-p', action='append', required=True,
                        help='Temperature for transformation (0.0-1.0)')
    parser.add_argument('--data_dir', '-d', type=str, default="/mnt/ssd/696ds_data/CodeSearchNet/resources/data/python",
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
    data_original_dir = os.path.join(args.data_dir, "final", "jsonl")
    source_filename = args.filename + '.jsonl.gz'
    read_path = os.path.join(data_original_dir, args.mode, source_filename)

    # save path
    data_augmented_dir = os.path.join(args.data_dir, "augmented")
    save_dir = os.path.join(data_augmented_dir, args.mode, args.filename, today)
    save_name = f"augmented_{str(args.p)}{'_' + args.postfix if args.postfix else ''}.json"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, save_name)

    info = {
            'source_filename': source_filename,
            'date': today,
            'p': args.p
        }

    print(args)
    print(info)
    return args, (read_path, save_path, info)

def filter_valid_parse(line):
    item = json.loads(line)
    try:
        cst.parse_module(item["code"])
        return item
    except:
        return None


def remove_docstring(json_item):
    json_item['code'], _ = transform(
        json_item['code'],
        *(RemoveUnassignedStringTransformer, (1,))
    )
    return json_item


def generate(args, read_path, save_path, info):

    with gzip.open(read_path, "r") as f:
        data = f.read().decode('utf-8')

        lines = [[line] for line in data.split('\n')]

    # filter by parse test
    json_list = [item for item in starmap(filter_valid_parse, lines) if item]

    # remove docstrings
    json_list = starmap(
        remove_docstring,
        [(json_item,) for json_item in json_list]
    )

    results = starmap(
            augment,
            [(json_item['code'], [], float(p), None, True) for json_item in json_list for p in args.p]
        )

    new_json_list = []
    for i, item in enumerate(json_list):
        new_json_item = {
            'original': item,
            'augmented': [
                {
                    'code': results[i * len(args.p) + j][0],
                    'log': results[i * len(args.p) + j][1],
                    'temp': p
                } for j, p in enumerate(args.p)
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