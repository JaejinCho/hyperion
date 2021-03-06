"""
 Copyright 2019 Johns Hopkins University  (Author: Jesus Villalba)
 Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)
"""
from __future__ import absolute_import

import torch
import torch.nn as nn

class TorchDataParallel(nn.DataParallel):
    def __getattr__(self, name):
        try:
            return super(TorchDataParallel, self).__getattr__(name)
        except AttributeError:
            return getattr(self.module, name)
