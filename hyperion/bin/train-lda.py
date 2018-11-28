#!/usr/bin/env python

"""
Trains LDA
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

from hyperion.hyp_defs import config_logger
from hyperion.helpers import VectorClassReader as VCR
from hyperion.transforms import TransformList, LDA, SbSw
from hyperion.utils.scp_list import SCPList


def train_lda(iv_file, train_list, preproc_file,
              scp_sep, v_field,
              min_spc, max_spc, spc_pruning_mode,
              csplit_min_spc, csplit_max_spc, csplit_mode,
              csplit_overlap, vcr_seed, 
              lda_dim,
              name, save_tlist, append_tlist, output_path, **kwargs):

    
    if preproc_file is not None:
        preproc = TransformList.load(preproc_file)
    else:
        preproc = None

    vcr  = VCR(iv_file, train_list, preproc,
               scp_sep=scp_sep, v_field=v_field,
               min_spc=min_spc, max_spc=max_spc, spc_pruning_mode=spc_pruning_mode,
               csplit_min_spc=csplit_min_spc, csplit_max_spc=csplit_max_spc,
               csplit_mode=csplit_mode,
               csplit_overlap=csplit_overlap, vcr_seed=vcr_seed)
    x, class_ids = vcr.read()

    t1 = time.time()

    s_mat = SbSw()
    s_mat.fit(x, class_ids)

    model = LDA(name=name)
    model.fit(mu=s_mat.mu, Sb=s_mat.Sb, Sw=s_mat.Sw, lda_dim=lda_dim)

    logging.info('Elapsed time: %.2f s.' % (time.time()-t1))
    
    x = model.predict(x)

    s_mat = SbSw()
    s_mat.fit(x, class_ids)
    logging.debug(s_mat.Sb[:4,:4])
    logging.debug(s_mat.Sw[:4,:4])
    
    if save_tlist:
        if append_tlist and preproc is not None:
            preproc.append(model)
            model = preproc
        else:
            model = TransformList(model)

    model.save(output_path)
        
    
    
if __name__ == "__main__":

    parser=argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        fromfile_prefix_chars='@',
        description='Train LDA')

    parser.add_argument('--iv-file', dest='iv_file', required=True)
    parser.add_argument('--train-list', dest='train_list', required=True)
    parser.add_argument('--preproc-file', dest='preproc_file', default=None)

    VCR.add_argparse_args(parser)

    parser.add_argument('--output-path', dest='output_path', required=True)
    parser.add_argument('--lda-dim', dest='lda_dim', type=int,
                        default=None)
    parser.add_argument('--no-save-tlist', dest='save_tlist',
                        default=True, action='store_false')
    parser.add_argument('--no-append-tlist', dest='append_tlist', 
                        default=True, action='store_false')
    parser.add_argument('--name', dest='name', default='lda')
    args=parser.parse_args()
    config_logger(args.verbose)
    del args.verbose
    logging.debug(args)

    train_lda(**vars(args))

            
