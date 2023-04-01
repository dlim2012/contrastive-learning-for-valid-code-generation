import argparse

import torch
from transformers import AutoTokenizer, AutoModel
from datasets import load_dataset_builder, load_dataset, load_from_disk
from torch.utils.data import Dataset, DataLoader
from tensorboardX import SummaryWriter
from tqdm import tqdm
from collections import defaultdict
import numpy as np

import os

def parse():
    """
    parse arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--lr', '-lr', type=float, default=3e-7,
                        help='base learning rate')
    parser.add_argument('--warmup', '-w', type=int, default=5000,
                        help="""
                            Warmup steps for learning rate.
                            Learning rate will decay afterwards. 
                            No learning rate scheduling if 0 is given
                        """)
    parser.add_argument('--batch_size', '-bs', type=int, default=4,
                        help="batch size")
    parser.add_argument('--model_name', '-m', type=str, default="microsoft/codebert-base",
                        help="pretrained model name") # "microsoft/codebert-base"
    parser.add_argument('--version_name_prefix', '-v', type=str, default='v',
                        help="Prefix for name used for logging and checkpoints")
    parser.add_argument('--log_dir', '-log_dir', type=str, default='log',
                        help="base logging directory for tensorboard")
    parser.add_argument('--checkpoint_dir', '-ckpt_dir', type=str, default='ckpt',
                        help="base checkpoint directory") # /mnt/ssd/696ds/checkpoints

    args = parser.parse_args()
    return args



class CloneDetector(torch.nn.Module):
    def __init__(self, model_name, device):
        super().__init__()
        self.model = AutoModel.from_pretrained(model_name)
        self.linear = torch.nn.Linear(768, 768)
        self.dropout = torch.nn.Dropout(p=0.1)
        self.sigmoid = torch.nn.Sigmoid()
        self.bce_loss = torch.nn.BCELoss()
        self.device = device

    def forward(self, batch):
        code1, code2 = batch['code1'].to(self.device), batch['code2'].to(self.device)

        out1 = self.model(**code1).last_hidden_state[:, 0, :] # CLS vector (shape: (B, 768, ))
        out2 = self.model(**code2).last_hidden_state[:, 0, :]

        # out1 = self.dropout(out1) # (shape: (B, 768, ))
        # out2 = self.dropout(out2)

        out1 = self.linear(out1) # (shape: (B, 768, ))
        out2 = self.linear(out2)

        scores = torch.sum(out1 * out2, dim=1) / 10

        return scores

    def loss(self, scores, labels):
        probs = self.sigmoid(scores.type(torch.float32))

        loss = self.bce_loss(probs, labels)

        return loss

    def acc(self, scores, labels, threshold=0):
        return torch.mean(((scores > threshold).type(torch.int32) == labels).type(torch.float32))

def tokenize(code):
    return tokenizer(code, return_tensors="pt", truncation=True, padding="longest", max_length=512)

def collate_fn(items):
    x = {}

    code1, code2, labels = [], [], []
    for item in items:
        code1.append(item['code1'])
        code2.append(item['code2'])
        labels.append(item['similar'])

    x['code1'] = tokenize(code1)
    x['code2'] = tokenize(code2)
    x['labels'] = torch.tensor(labels, dtype=torch.float32)

    return x

def linear_learning_rate_scheduler(optimizer, steps, target, warm_up, decay):
    """
    Change the learning rate of the optimizer using a linear learning rate schedule
    :param optimizer: optimizer that are being used
    :param steps: current number of steps
    :param target: maximum learning rate
    :param warm_up: number of warm up steps
    :param decay: number of steps at which the learning rate will be 0
    :return: modified optimizer
    """
    if steps < warm_up:
        running_lr = target * steps / warm_up
    else:
        running_lr = target * (decay - steps) / (decay - warm_up)

    for g in optimizer.param_groups:
        g['lr'] = running_lr
    return optimizer, running_lr

if __name__ == '__main__':
    args = parse()

    version_name = args.version_name_prefix + f"_{args.model_name.split('/')[-1]}_lr{args.lr:.1e}" + (f"-w{args.warmup}" if args.warmup else "")
    print(version_name)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(device)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    PoolC_dataset_dir = os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)), 'data', 'PoolC_train')
    train_dataset = load_dataset("PoolC/1-fold-clone-detection-600k-5fold", split="train")
    val_dataset = load_dataset("PoolC/1-fold-clone-detection-600k-5fold", split="val")
    train_dataloader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)
    val_dataloader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)

    os.makedirs(args.log_dir, exist_ok=True)
    writer = SummaryWriter(os.path.join(args.log_dir, version_name))
    checkpoint_dir = os.path.join(args.checkpoint_dir, version_name)
    os.makedirs(checkpoint_dir, exist_ok=True)

    model = CloneDetector(args.model_name, device).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=0.01)
    model.train(True)
    pbar = tqdm(train_dataloader)

    history = defaultdict(list)
    for i, batch in enumerate(pbar):
        if args.warmup:
            optimizer, running_lr = linear_learning_rate_scheduler(optimizer, i + 1, args.lr, args.warmup, len(train_dataloader))
        optimizer.zero_grad()

        labels = batch['labels'].to(device)
        scores = model(batch)
        loss = model.loss(scores, labels)
        acc = model.acc(scores, labels)

        loss.backward()
        optimizer.step()

        loss, acc = loss.tolist(), acc.tolist()

        writer.add_scalar('train_loss', loss, i + 1)
        writer.add_scalar('train_acc', acc, i + 1)
        writer.add_scalar('lr', running_lr, i + 1)

        history['train_loss'].append(loss)
        history['train_acc'].append(acc)


        if (i+1) % 100000 == 0:
            checkpoint_path = os.path.join(checkpoint_dir, "step%d.pt" % (i+1))
            torch.save(model, checkpoint_path)

        postfix = {'loss': loss, 'acc': acc, 'lr': running_lr}
        pbar.set_postfix(postfix)

    writer.add_scalar('train_loss_epoch', np.mean(history['train_loss']), 0)
    writer.add_scalar('train_acc_epoch', np.mean(history['train_acc']), 0)


    model.train(False)
    pbar = tqdm(val_dataloader)
    val_acc_list, val_loss_list = [], []
    for i, batch in enumerate(pbar):
        labels = batch['labels'].to(device)
        scores = model(batch)
        loss = model.loss(scores, labels)
        acc = model.acc(scores, labels)

        optimizer.step()

        loss, acc = loss.tolist(), acc.tolist()

        history['val_loss'].append(loss)
        history['val_acc'].append(acc)

    writer.add_scalar('val_loss_epoch', np.mean(history['val_loss']), 0)
    writer.add_scalar('val_loss_epoch', np.mean(history['val_acc']), 0)