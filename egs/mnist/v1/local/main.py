#!/usr/bin/env python
"""
 Copyright 2018 Johns Hopkins University  (Author: Jesus Villalba)
 Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)
 Trains x-vectors
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from six.moves import xrange

import sys
import os
import argparse
import time
import logging

import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms

from hyperion.hyp_defs import config_logger
from hyperion.torch.utils import open_device
from hyperion.torch.archs import FCNetV1
from hyperion.torch.transforms import Reshape
from hyperion.torch.helpers import OptimizerFactory as OF
from hyperion.torch.lr_schedulers import LRSchedulerFactory as LRSF
from hyperion.torch.torch_trainer import TorchTrainer
from hyperion.torch.metrics import CategoricalAccuracy

input_width=28
input_height=28



def create_net(net_type):
    if net_type=='fcnet':
        return FCNetV1(2, input_width*input_height, 1000, 10 , dropout_rate=0.5)


    
def main(net_type, batch_size, test_batch_size, exp_path,
         epochs, use_cuda, log_interval, resume, **kwargs):

    opt_args = OF.filter_args(prefix='opt', **kwargs)
    lrsch_args = LRSF.filter_args(prefix='lrsch', **kwargs)

    if use_cuda:
        device = open_device(num_gpus=1)
    else:
        device = torch.device('cpu')

    transform_list = [transforms.ToTensor(),
                      transforms.Normalize((0.1307,), (0.3081,))]
    if net_type == 'fcnet':
        transform_list.append(Reshape((-1,)))
    transform = transforms.Compose(transform_list)
    
    largs = {'num_workers': 1, 'pin_memory': True} if use_cuda else {}
    train_loader = torch.utils.data.DataLoader(
        datasets.MNIST('./exp/data', train=True, download=True,
                       transform=transform), 
                       batch_size=args.batch_size, shuffle=True, **largs)

    test_loader = torch.utils.data.DataLoader(
        datasets.MNIST('./exp/data', train=False, transform=transform),
                       batch_size=args.test_batch_size, shuffle=False, **largs)

    model = create_net(net_type)
    model.to(device)

    print(opt_args)
    print(lrsch_args)
    optimizer = OF.create(model.parameters(), **opt_args)
    lr_sch = LRSF.create(optimizer, **lrsch_args)
    #optimizer = optim.SGD(model.parameters(), lr=lr, momentum=momentum)
    loss = nn.CrossEntropyLoss()
    metrics = { 'acc': CategoricalAccuracy() }
    
    trainer = TorchTrainer(model, optimizer, loss, epochs, exp_path, device=device, metrics=metrics, lr_scheduler=lr_sch)
    if resume:
        trainer.load_last_checkpoint()
    trainer.fit(train_loader, test_loader)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars='@',
        description='PyTorch MNIST')
    parser.add_argument('--net-type', default='fcnet', metavar='N',
                        help='Type of network architecture')

    parser.add_argument('--batch-size', type=int, default=64,
                        help='input batch size for training (default: 64)')
    parser.add_argument('--test-batch-size', type=int, default=1000,
                        help='input batch size for testing (default: 1000)')
    parser.add_argument('--epochs', type=int, default=10, 
                        help='number of epochs to train (default: 10)')
    OF.add_argparse_args(parser, prefix='opt')
    LRSF.add_argparse_args(parser, prefix='lrsch')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA training')
    parser.add_argument('--seed', type=int, default=1, 
                        help='random seed (default: 1)')
    parser.add_argument('--log-interval', type=int, default=10, 
                        help='how many batches to wait before logging training status')

    parser.add_argument('--resume', action='store_true', default=False,
                        help='resume training from checkpoint')

    parser.add_argument('--exp-path', help='experiment path')

    parser.add_argument('-v', '--verbose', dest='verbose', default=1, choices=[0, 1, 2, 3], type=int)

    args = parser.parse_args()
    config_logger(args.verbose)
    del args.verbose
    logging.debug(args)

    args.use_cuda = not args.no_cuda
    del args.no_cuda
    
    torch.manual_seed(args.seed)
    del args.seed

    main(**vars(args))



