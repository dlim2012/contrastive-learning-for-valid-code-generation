from datasets import load_dataset
from argparse import ArgumentParser
import libcst as cst
from tqdm_pathos import starmap
from tqdm import tqdm

import os
import json
from datetime import date

from preprocess.transform.utils.tools import transform
from preprocess.augment import augment



def parse_PoolC():
    parser = ArgumentParser()

    parser.add_argument('--p', '-p', action='append', required=True,
                        help='Temperature for transformation (0.0-1.0)')
    parser.add_argument('--data_dir', '-d', type=str, default="/mnt/ssd/696ds_data/PoolC",
                        help='data dir')
    parser.add_argument('--mode', '-m', type=str, default='train',
                        help='mode: train, val')
    parser.add_argument('--postfix', '-pf', type=str, default='',
                        help='postfix to save path')

    args = parser.parse_args()

    today = date.today().strftime("%m%d%y")

    save_dir = os.path.join(args.data_dir, args.mode, today)
    save_name = f"augmented_{str(args.p)}{'_' + args.postfix if args.postfix else ''}.json"
    os.makedirs(save_dir, exist_ok=True)
    args.save_path = os.path.join(save_dir, save_name)

    args.info = {
        'date': today,
        'p': args.p
    }


    print(args)

    return args


def filter_valid_parse(data):
    try:
        cst.parse_module(data["code1"])
        cst.parse_module(data["code2"])
        return data
    except:
        return None

def generate(args):
    """ Note: did not remove docstrings in this case """
    dataset = load_dataset("PoolC/1-fold-clone-detection-600k-5fold", split="train")
    dataset = [[data] for data in tqdm(dataset)]

    # filter by parse test
    print('parse test...')
    dataset = [data for data in starmap(filter_valid_parse, dataset) if data]

    print('augment...')
    results = {}
    for key in ['code1', 'code2']:
        results[key] = starmap(
            augment,
            [(data[key], [], float(p), None, True) for data in dataset for p in args.p]
        )

    new_json_list = []
    for i, data in enumerate(dataset):
        new_json_item = {
            'original': data,
            'augmented': [
                {
                    'code1': results['code1'][i * len(args.p) + j][0],
                    'code1_log': results['code1'][i * len(args.p) + j][1],
                    'code2': results['code2'][i * len(args.p) + j][0],
                    'code2_log': results['code2'][i * len(args.p) + j][1],
                } for j, p in enumerate(args.p)
            ]
        }
        new_json_list.append(new_json_item)

    to_save = {
        'transform_info': args.info,
        'data': new_json_list
    }

    with open(args.save_path, 'w') as f:
        f.write(json.dumps(to_save))
    print(f'Saved: {args.save_path}')

if __name__ == '__main__':
    args = parse_PoolC()
    generate(args)




