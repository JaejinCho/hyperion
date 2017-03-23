#!/usr/bin/env python
"""
Converts from Ark format to h5 format.
"""
from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import argparse
import time
import numpy as np
from six.moves import xrange

from hyperion.io import HypDataWriter, KaldiDataReader

def ark2hyp(input_file, input_dir, output_file, field):

    ark_r = KaldiDataReader(input_file, input_dir)
    X, keys = ark_r.read()

    h_w = HypDataWriter(output_file)
    h_w.write(keys, field, X)


if __name__ == "__main__":
    
    parser=argparse.ArgumentParser(
        fromfile_prefix_chars='@',
        description='Compacts .arr files into a hdf5 file.')

    parser.add_argument('--input-file',dest='input_file', required=True)
    parser.add_argument('--input-dir', dest='input_dir', default=None)
    parser.add_argument('--output-file', dest='output_file', required=True)
    parser.add_argument('--field', dest='field', default='')

    args=parser.parse_args()

    ark2hyp(**vars(args))
    