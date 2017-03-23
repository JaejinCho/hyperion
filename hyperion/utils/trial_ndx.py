"""
Bosaris compatible Ndx
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from six.moves import xrange

import os.path as path
import copy

import numpy as np
import h5py

from .list_utils import *


class TrialNdx(object):

    def __init__(self, model_set=None, seg_set=None, trial_mask=None):
        self.model_set = model_set
        self.seg_set = seg_set
        self.trial_mask = trial_mask
        if (model_set is not None) and (seg_set is not None):
            self.validate()
        
        
    def copy(self):
        return copy.deepcopy(self)

    
    def sort(self):
        self.model_set, m_idx = sort(self.model_set, return_index=True)
        self.seg_set, s_idx = sort(self.seg_set, return_index=True)
        self.trial_mask = self.trial_mask[np.ix_(m_idx, s_idx)]
        
        
    def save(self, file_path):
        file_base, file_ext = path.splitext(file_path)
        if file_ext == '.txt' :
            self.save_txt(file_path)
        else:
            self.save_h5(file_path)

            
    def save_h5(self, file_path):
        with h5py.File(file_path, 'w') as f:
            model_set = self.model_set.astype('S')
            seg_set = self.seg_set.astype('S')
            f.create_dataset('ID/row_ids', data=model_set)
            f.create_dataset('ID/column_ids', data=seg_set)
            f.create_dataset('trial_mask',
                             data=self.trial_mask.astype('uint8'))

            # model_set = self.model_set.astype('S')
            # f.create_dataset('ID/row_ids', self.model_set.shape, dtype=model_set.dtype)
            # f['ID/row_ids'] = model_set
            # seg_set = self.seg_set.astype('S')
            # f.create_dataset('ID/column_ids', self.seg_set.shape, dtype=seg_set.dtype)
            # f['ID/column_ids'] = seg_set
            # f.create_dataset('trial_mask', self.trial_mask.shape, dtype='uint8')
            # f['trial_mask'] = self.trial_mask.astype('uint8')

            
    def save_txt(self, file_path):
        idx=(self.trial_mask.T == True).nonzero()
        with open(file_path, 'w') as f:
            for item in zip(idx[0], idx[1]):
                f.write('%s %s\n' % (self.model_set[item[1]], self.seg_set[item[0]]))
                    

    @classmethod
    def load(cls, file_path):
        file_base, file_ext = path.splitext(file_path)
        if file_ext == '.txt' :
            return TrialNdx.load_txt(file_path)
        else:
            return TrialNdx.load_h5(file_path)


    @classmethod
    def load_h5(cls, file_path):
        with h5py.File(file_path, 'r') as f:
            model_set = [t.decode('utf-8') for t in f['ID/row_ids']]
            seg_set = [t.decode('utf-8') for t in f['ID/column_ids']]
            trial_mask = np.asarray(f['trial_mask'], dtype='bool')
        return cls(model_set, seg_set, trial_mask)


    @classmethod
    def load_txt(cls, file_path):
        with open(file_path, 'r') as f:
            fields = [line.split() for line in f]
        models = [i[0] for i in fields]
        segments = [i[1] for i in fields]
        model_set, _, model_idx = np.unique(
            models, return_index=True, return_inverse=True)
        seg_set, _, seg_idx = np.unique(
            segments, return_index=True, return_inverse=True)
        trial_mask = np.zeros((len(model_set), len(seg_set)), dtype='bool')
        for item in zip(model_idx, seg_idx):
            trial_mask[item[0], item[1]] = True
        return cls(model_set, seg_set, trial_mask)

    
    @classmethod
    def merge(cls, ndx_list):
        nb_ndx = len(ndx_list)
        model_set = ndx_list[0].model_set
        seg_set = ndx_list[0].seg_set
        trial_mask = ndx_list[0].trial_mask
        for i in xrange(1, nb_ndx):
            ndx_i = ndx_list[i]
            new_model_set = np.union1d(model_set, ndx_i.model_set)
            new_seg_set = np.union1d(seg_set, ndx_i.seg_set)
            trial_mask_1 = np.zeros((len(new_model_set), len(new_seg_set)),
                                    dtype='bool')
            _, mi_a, mi_b = intersect(new_model_set, model_set,
                                      assume_unique=True, return_index=True)
            _, si_a, si_b = intersect(new_seg_set, seg_set,
                                      assume_unique=True, return_index=True)
            trial_mask_1[np.ix_(mi_a, si_a)] = trial_mask[np.ix_(mi_b, si_b)]
            
            trial_mask_2=np.zeros((len(new_model_set), len(new_seg_set)),
                                  dtype='bool')
            _, mi_a, mi_b = intersect(new_model_set, ndx_i.model_set,
                                     assume_unique=True, return_index=True)
            _, si_a, si_b = intersect(new_seg_set, ndx_i.seg_set,
                                     assume_unique=True, return_index=True)
            trial_mask_2[np.ix_(mi_a, si_a)] = ndx_i.trial_mask[
                np.ix_(mi_b, si_b)]

            model_set = new_model_set
            seg_set = new_seg_set
            trial_mask= np.logical_or(trial_mask_1, trial_mask_2)
                            
        return cls(model_set, seg_set, trial_mask)


    @staticmethod
    def parse_eval_set(ndx, enroll, test, eval_set):
        if eval_set == 'enroll-test':
            enroll = enroll.filter(ndx.model_set)
        if eval_set == 'enroll-coh':
            ndx = TrialNdx(ndx.model_set, test.file_path)
            enroll = enroll.filter(ndx.model_set)
        if eval_set == 'coh-test':
            ndx = TrialNdx(enroll.key, ndx.seg_set)
        if eval_set == 'coh-coh':
            ndx = TrialNdx(enroll.key, test.file_path)
        return ndx, enroll

    
    def filter(self, model_set, seg_set, keep=True):
        if not(keep):
            model_set = np.setdiff1d(self.model_set, model_set)
            seg_set = np.setdiff1d(self.seg_set, seg_set)

        f, mod_idx = ismember(model_set, self.model_set)
        assert(np.all(f))
        f, seg_idx = ismember(seg_set, self.seg_set)
        assert(np.all(f))
        model_set = self.model_set[mod_idx]
        set_set = self.seg_set[seg_idx]
        trial_mask = self.trial_mask[np.ix_(mod_idx, seg_idx)]
        return TrialNdx(model_set, seg_set, trial_mask)

    
    def split(self, model_idx, nb_model_parts, seg_idx, nb_seg_parts):
        model_set, model_idx1 = split_list(self.model_set,
                                           model_idx, nb_model_parts)
        seg_set, seg_idx1 = split_list(self.seg_set,
                                       seg_idx, nb_seg_parts)
        trial_mask=self.trial_mask[np.ix_(model_idx1, seg_idx1)]
        return TrialNdx(model_set, seg_set, trial_mask)

    
    def validate(self):
        self.model_set = list2ndarray(self.model_set)
        self.seg_set = list2ndarray(self.seg_set)

        assert(len(np.unique(self.model_set)) == len(self.model_set))
        assert(len(np.unique(self.seg_set)) == len(self.seg_set))
        if self.trial_mask is None:
            self.trial_mask = np.ones((len(model_set), len(seg_set)),
                                      dtype='bool')
        else:
            assert(self.trial_mask.shape ==
                   (len(self.model_set), len(self.seg_set)))


    def __eq__(self, other):
        eq = self.model_set.shape == other.model_set.shape
        eq = eq and np.all(self.model_set == other.model_set)
        eq = eq and (self.seg_set.shape == other.seg_set.shape)
        eq = eq and np.all(self.seg_set == other.seg_set)
        eq = eq and np.all(self.trial_mask == other.trial_mask)
        return eq

    
    def __cmp__(self, other):
        if self.__eq__(oher):
            return 0
        return 1

    
    def test(ndx_file='core-core_det5_ndx.h5'):

        ndx1 = TrialNdx.load(ndx_file)
        ndx1.sort()
        ndx2 = ndx1.copy()

        ndx2.model_set[0] = 'm1'
        ndx2.trial_mask[:] = 0
        assert(np.any(ndx1.model_set != ndx2.model_set))
        assert(np.any(ndx1.trial_mask != ndx2.trial_mask))

        ndx2 = TrialNdx(ndx1.model_set[:10], ndx1.seg_set,
                        ndx1.trial_mask[:10,:])
        ndx3 = TrialNdx(ndx1.model_set[5:], ndx1.seg_set,
                        ndx1.trial_mask[5:,:])
        ndx4 = TrialNdx.merge([ndx2, ndx3])
        assert(ndx1 == ndx4)

        ndx2 = TrialNdx(ndx1.model_set, ndx1.seg_set[:10],
                        ndx1.trial_mask[:,:10])
        ndx3 = TrialNdx(ndx1.model_set, ndx1.seg_set[5:],
                        ndx1.trial_mask[:,5:])
        ndx4 = TrialNdx.merge([ndx2, ndx3])
        assert(ndx1 == ndx4)

        ndx2 = TrialNdx(ndx1.model_set[:5], ndx1.seg_set[:10],
                        ndx1.trial_mask[:5,:10])
        ndx3 = ndx1.filter(ndx2.model_set, ndx2.seg_set, keep=True)
        assert(ndx2 == ndx3)

        nb_parts=3
        ndx_list = []
        for i in xrange(nb_parts):
            for j in xrange(nb_parts):
                ndx_ij = ndx1.split(i+1, nb_parts, j+1, nb_parts)
                ndx_list.append(ndx_ij)
        ndx2 = TrialNdx.merge(ndx_list)
        assert(ndx1 == ndx2)

        
        file_h5 = 'test.h5'
        ndx1.save(file_h5)
        ndx2 = TrialNdx.load(file_h5)
        assert(ndx1 == ndx2)

        file_txt = 'test.txt'
        ndx3.trial_mask[0, :] = True
        ndx3.trial_mask[:, 0] = True
        ndx3.save(file_txt)
        ndx2 = TrialNdx.load(file_txt)
        assert(ndx3 == ndx2)




# class TrialNdx(object):

#     def __init__(self, model_set=None, seg_set=None, trial_mask=None):
#         self.model_set = model_set
#         self.seg_set = seg_set
#         self.trial_mask = trial_mask
#         if (model_set is not None) and (seg_set is not None) and (trial_mask is None):
#             self.validate()
#             self.trial_mask = np.ones((len(model_set), len(seg_set)), dtype='bool')
#         else:
#             self.validate()
        
        
#     def copy(self):
#         return copy.deepcopy(self)

#     def sort(self):
#         self.model_set, m_idx = sort(self.model_set, return_index=True)
#         self.seg_set, s_idx = sort(self.seg_set, return_index=True)
#         self.trial_mask = self.trial_mask[np.ix_(m_idx, s_idx)]
        
        
#     def save(self, file_path):
#         file_base, file_ext = path.splitext(file_path)
#         if file_ext == '.txt' :
#             self.save_txt(file_path)
#         else:
#             self.save_h5(file_path)

            
#     def save_h5(self, file_path):
#         with h5py.File(file_path, 'w') as f:
#             f.create_dataset('ID/row_ids', (len(self.model_set),), dtype='|S11')
#             f.create_dataset('ID/column_ids', (len(self.seg_set),), dtype='|S11')
#             f.create_dataset('trial_mask', self.trial_mask.shape, dtype='uint8')
#             f['ID/row_ids'] = np.array(self.model_set)
#             f['ID/column_ids'] = np.array(self.seg_set)
#             f['trial_mask'] = self.trial_mask.astype('uint8')

            
#     def save_txt(self, file_path):
#         idx=(self.trial_mask.T == True).nonzero()
#         with open(file_path, 'w') as f:
#             for item in idx:
#                 f.write('%s %s\n' % (self.modelset[item[1]], self.modelset[item[0]]))
                    

#     @classmethod
#     def load(cls, file_path):
#         file_base, file_ext = path.splitext(file_path)
#         if file_ext == '.txt' :
#             return TrialNdx.load_txt(file_path)
#         else:
#             return TrialNdx.load_h5(file_path)


#     @classmethod
#     def load_h5(cls, file_path):
#         with h5py.File(file_path, 'r') as f:
#             model_set = [t.decode('utf-8') for t in f['ID/row_ids']]
#             seg_set = [t.decode('utf-8') for t in f['ID/column_ids']]
#             trial_mask = np.asarray(f['trial_mask'], dtype='bool')
#         return cls(model_set, seg_set, trial_mask)


#     @classmethod
#     def load_txt(cls, file_path):
#         with open(file_path, 'w') as f:
#             fields = [line.split() for line in f]
#         models = [i[0] for i in fields]
#         segments = [i[1] for i in fields]
#         model_set, _, model_idx = unique(models, return_index=True, return_inverse=True)
#         seg_set, _, seg_idx = unique(segments, return_index=True, return_inverse=True)
#         trial_mask = np.zeros((len(model_set), len(seg_set)), dtype='bool')
#         for item in zip(model_idx, seg_idx):
#             trial_mask[item[0], item[1]] = True
#         return cls(model_set, seg_set, trial_mask)
            
#     @classmethod
#     def merge(cls, ndx_list):
#         nb_ndx = len(ndx_list)
#         model_set = ndx_list[0].model_set
#         seg_set = ndx_list[0].seg_set
#         trial_mask = ndx_list[0].trial_mask
#         for i in xrange(1, nb_ndx):
#             ndx_i = ndx_list[i]
#             new_model_set = sorted(list(set(model_set+ndx_i.model_set)))
#             new_seg_set = sorted(list(set(seg_set+ndx_i.seg_set)))
#             trial_mask_1 = np.zeros((len(new_model_set), len(new_seg_set)), dtype='bool')
#             _, mi_a, mi_b = intersect(new_model_set, model_set,
#                                       assume_unique=True, return_index=True)
#             _, si_a, si_b = intersect(new_seg_set, seg_set,
#                                       assume_unique=True, return_index=True)
#             trial_mask_1[np.ix_(mi_a, si_a)] = trial_mask[np.ix_(mi_b, si_b)]
            
#             trial_mask_2=np.zeros((len(new_model_set), len(new_seg_set)), dtype='bool')
#             _, mi_a, mi_b = intersect(new_model_set, ndx_i.model_set,
#                                      assume_unique=True, return_index=True)
#             _, si_a, si_b = intersect(new_seg_set, ndx_i.seg_set,
#                                      assume_unique=True, return_index=True)
#             trial_mask_2[np.ix_(mi_a, si_a)] = ndx_i.trial_mask[np.ix_(mi_b, si_b)]

#             model_set = new_model_set
#             seg_set = new_seg_set
#             trial_mask= np.logical_or(trial_mask_1, trial_mask_2)
                            
#         return cls(model_set, seg_set, trial_mask)
                                  

#     def filter(self, model_set, seg_set, keep):
#         if not(keep):
#             model_set=setdiff(self.model_set, model_set)
#             seg_set=setdiff(self.model_set, seg_set)

#         f, mod_idx = ismember(model_set, self.model_set)
#         assert(all(f))
#         f, seg_idx = ismember(seg_set, self.seg_set)
#         assert(all(f))
#         model_set = self.model_set[mod_idx]
#         set_set = self.model_set[seg_idx]
#         trial_mask = self.trial_mask[mod_idx, seg_idx]
#         return TrialNdx(model_set, seg_set, trial_mask)

#     def split(self, model_idx, nb_model_parts, seg_idx, nb_seg_parts):
#         model_set, model_idx1 = split_list(self.model_set, model_idx, nb_model_parts)
#         seg_set, seg_idx1 = split_list(self.seg_set, seg_idx, nb_seg_parts)
#         trial_mask=self.trial_mask(model_idx1, model_idx2)
#         return TrialNdx(model_set, seg_set, trial_mask)

#     def validate(self):
#         assert(isinstance(self.model_set, list))
#         assert(isinstance(self.seg_set, list))
#         assert(len(set(self.model_set)) == len(self.model_set))
#         assert(len(set(self.seg_set)) == len(self.seg_set))
#         if self.trial_mask is not None:
#             assert(self.trial_mask.shape == (len(self.model_set), len(self.seg_set)))

#     @staticmethod
#     def equal(ndx1, ndx2):
#         eq = ndx1.model_set == ndx2.model_set
#         eq = eq and (ndx1.seg_set == ndx2.seg_set)
#         eq = eq and np.all(ndx1.trial_mask == ndx2.trial_mask)
#         print(eq)
#         return eq
        
#     def test(ndx_file):

#         ndx1 = TrialNdx.load(ndx_file)
#         ndx1.sort()
#         ndx2 = ndx1.copy()

#         ndx2.model_set[0] = 'm1'
#         ndx2.trial_mask[:] = 0
#         assert(ndx1.model_set != ndx2.model_set)
#         assert(np.any(ndx1.trial_mask != ndx2.trial_mask))

#         ndx2 = TrialNdx(ndx1.model_set[:10], ndx1.seg_set, ndx1.trial_mask[:10,:])
#         ndx3 = TrialNdx(ndx1.model_set[5:], ndx1.seg_set, ndx1.trial_mask[5:,:])
#         ndx4 = TrialNdx.merge([ndx2, ndx3])
#         assert(TrialNdx.equal(ndx1, ndx4))

#         ndx2 = TrialNdx(ndx1.model_set, ndx1.seg_set[:10], ndx1.trial_mask[:,:10])
#         ndx3 = TrialNdx(ndx1.model_set, ndx1.seg_set[5:], ndx1.trial_mask[:,5:])
#         ndx4 = TrialNdx.merge([ndx2, ndx3])
#         assert(TrialNdx.equal(ndx1, ndx4))

#         ndx2 = TrialNdx(ndx1.model_set[:5], ndx1.seg_set[:10], ndx1.trial_mask[:5,:10])
#         ndx3 = ndx1.filter(ndx2.model_set, ndx2.seg_set, keep=True)
#         assert(TrialNdx.equal(ndx1, ndx3))

#         nb_parts=3
#         ndx_list = []
#         for i in xrange(nb_parts):
#             for j in xrange(nb_parts):
#                 ndx_ij = ndx1.split(i+1, nb_parts, j+1, nb_parts)
#                 ndx_list.append(ndx_ij)
#         ndx2 = TrialNdx.merge(ndx_list)
#         assert(TrialNdx.equal(ndx1, ndx2))
        

#         file_h5 = 'test.h5'
#         ndx1.save(file_h5)
#         ndx2 = TrialNdx.load(file_h5)
#         assert(TrialNdx.equal(ndx1, ndx5))

#         file_h5 = 'test.txt'
#         ndx1.save(file_txt)
#         ndx2 = TrialNdx.load(file_h5)
#         assert(TrialNdx.equal(ndx1, ndx5))