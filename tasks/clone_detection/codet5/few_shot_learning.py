from transformers import RobertaTokenizer, T5ForConditionalGeneration
import torch
from datasets import load_dataset_builder, load_dataset
from torch.utils.data import Dataset, DataLoader
import os
import json
from collections import deque
import argparse

def parse():
    """
    parse arguments
    """
    parser = argparse.ArgumentParser()
    # parser.add_argument('--lr', '-lr', type=float, default=3e-7,
    #                     help='base learning rate')
    # parser.add_argument('--warmup', '-w', type=int, default=5000,
    #                     help="""
    #                         Warmup steps for learning rate.
    #                         Learning rate will decay afterwards.
    #                         No learning rate scheduling if 0 is given
    #                     """)
    # parser.add_argument('--batch_size', '-bs', type=int, default=4,
    #                     help="batch size")
    parser.add_argument('--model_name', '-m', type=str, default='Salesforce/codet5-base',
                        help="pretrained model name") # "Salesforce/codet5-large"
    # parser.add_argument('--version_name_prefix', '-v', type=str, default='v',
    #                     help="Prefix for name used for logging and checkpoints")
    # parser.add_argument('--log_dir', '-log_dir', type=str, default='log',
    #                     help="base logging directory for tensorboard")
    # parser.add_argument('--checkpoint_dir', '-ckpt_dir', type=str, default='ckpt',
    #                     help="base checkpoint directory") # /mnt/ssd/696ds/checkpoints

    args = parser.parse_args()
    print(args)
    return args

def tokenize(code):
    # <cls> {code} </sep>
    ret =  tokenizer(code, truncation=True, max_length=254).input_ids
    return ret

def predict(out):
    i1, i2 = out.find("True"), out.find("False")
    if i1 == -1 and i2 == -1:
        return -1 # invalid
    if i1 == -1:
        return 0
    if i2 == -1:
        return 1
    return 1 if i1 < i2 else 0


if __name__ == '__main__':
    args = parse()

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    tokenizer = RobertaTokenizer.from_pretrained(args.model_name)
    model = T5ForConditionalGeneration.from_pretrained(args.model_name).to(device)

    dataset = load_dataset("PoolC/1-fold-clone-detection-600k-5fold", split="train")

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-6, weight_decay=0.01)
    valid, res = deque(), deque()
    n_correct, n_valid = 0, 0

    for i, item in enumerate(dataset):
        optimizer.zero_grad()

        # make input and output data
        # "<cls> Detect clones: {code1} </sep> {code2} </sep>"
        input_ids = torch.tensor(
            [tokenize("Detect clones:")[:-1] + tokenize(item['code1'])[1:] + tokenize(item['code2'])[1:]])
        target = True if item['similar'] else False
        labels = torch.tensor([tokenize(str(target))])
        input_ids, labels = input_ids.to(device), labels.to(device)

        # make prediction and evaluate
        out = tokenizer.decode(model.generate(input_ids, max_length=10)[0], skip_special_tokens=False)
        prediction = predict(out)
        if prediction != -1:
            res.append((prediction and target) or (not prediction and not target))
        else:
            valid.append(0)
            res.append(0)
        if len(valid) > 100:
            n_correct -= res.popleft()
            n_valid -= valid.popleft()
        n_correct += res[-1]
        n_valid += valid[-1]
        if (i + 1) % 100 == 0:
            print([i + 1], n_correct, n_valid, '%.2f' % (n_correct / (n_valid + 1e-10)), len(input_ids[0]), out)

        # train
        loss = model(input_ids=input_ids, labels=labels).loss
        loss.backward()
        optimizer.step()
