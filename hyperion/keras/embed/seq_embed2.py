"""
x-vector categorical embeddings
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from six.moves import xrange

import numpy as np

from keras import backend as K
from keras import optimizers
from keras import objectives
from keras.layers import Input, Concatenate
from keras.models import Model, load_model, model_from_json

from .. import objectives as hyp_obj
from ..keras_utils import *
from ..layers import *

from ...hyp_model import HypModel


class SeqEmbed(HypModel):

    def __init__(self, prepool_net, postpool_net,
                 loss='categorical_crossentropy',
                 pooling='mean+std',
                 left_context=0,
                 right_context=0,
                 begin_context=None,
                 end_context=None,
                 prepool_downsampling=None,
                 **kwargs):

        super(SeqEmbed, self).__init__(**kwargs)

        self.prepool_net = prepool_net
        self.postpool_net = postpool_net
        self.pooling = pooling
        self.loss = loss

        self.model = None
        self.pool_net = None
        
        self.left_context = left_context
        self.right_context = right_context
        self.begin_context = left_context if begin_context is None else begin_context
        self.end_context = right_context if end_context is None else end_context
        self._prepool_downsampling = prepool_downsampling
        self.max_seq_length = None

        
    @property
    def x_dim(self):
        return self.prepool_net.get_input_shape_at(0)[-1]

    
    
    @property
    def pool_in_dim(self):
        return self.prepool_net.get_output_shape_at(0)[-1]


    
    @property
    def pool_out_dim(self):
        return self.postpool_net.get_input_shape_at(0)[-1]


    
    @property
    def in_length(self):
        return self.prepool_net.get_input_shape_at(0)[-2]


    
    @property
    def pool_in_length(self):
        return self.prepool_net.get_output_shape_at(0)[-2]


    
    @property
    def prepool_downsampling(self):
        if self.prepool_downsampling is None:
            assert self.in_length is not None
            assert self.pool_in_length is not None
            r = self.in_length/self.pool_in_length
            assert np.ceil(r) == np.floor(r)
            self._prepool_downsampling = int(r)
        return self._prepool_downsampling


    
    def _apply_pooling(self, x, mask):
        
        if self.pooling == 'mean+std':
            pool = Concatenate(axis=-1, name='pooling')(
                GlobalWeightedMeanStdPooling1D(name='mean+std')([x, mask]))
        elif self.pooling == 'mean+logvar':
            pool = Concatenate(axis=-1, name='pooling')(
                GlobalWeightedMeanLogVarPooling1D(name='mean+logvar')([x, mask]))
        elif self.pooling == 'mean':
            pool = GlobalWeightedAveragePooling1D(name='pooling')([x, mask])
        else:
            raise ValueError('Invalid pooling %s' % self.pooling)

        return pool


    
    def compile(self, **kwargs):
        self.model.compile(loss=self.loss, **kwargs)


        
    def build(self, max_seq_length=None):

        if max_seq_length is None:
            max_seq_length = self.prepool_net.get_input_shape_at(0)[-2]
        self.max_seq_length = max_seq_length

        x = Input(shape=(max_seq_length, self.x_dim,))
        mask = CreateMask(0)(x)
        frame_embed = self.prepool_net(x)
        pool = self._apply_pooling(frame_embed, mask)
        y = self.postpool_net(pool)
        self.model = Model(x, y)
        self.model.summary()
        
        

    def build_embed(self, layers):

        frame_embed = Input(shape=(None, self.pool_in_dim,))
        mask = Input(shape=(None,))
        pool = self._apply_pooling(frame_embed, mask)
        
        outputs = []
        for layer_name in layers:
            embed_i = Model(self.postpool_net.get_input_at(0),
                            self.postpool_net.get_layer(layer_name).get_output_at(0))(pool)
            outputs.append(embed_i)

        self.pool_net = Model([frame_embed, mask], outputs)
        self.pool_net.summary()
        
        

    def predict_embed(self, x, **kwargs):

        in_seq_length = self.in_length
        pool_seq_length = self.in_pool_length
        r = self.prepool_downsampling
        
        assert np.ceil(self.left_context/r) == np.floor(self.left_context/r)
        assert np.ceil(self.right_context/r) == np.floor(self.right_context/r)
        assert np.ceil(self.begin_context/r) == np.floor(self.begin_context/r)
        assert np.ceil(self.end_context/r) == np.floor(self.end_context/r) 
        pool_begin_context = self.begin_context/r
        pool_end_context = self.end_context/r
        pool_left_context = self.left_context/r
        pool_right_context = self.right_context/r

        in_length = x.shape[-2]
        pool_length = int(in_length/r)
        in_shift = in_seq_length - self.left_context - self.right_context
        pool_shift = int(in_shift/r)
        
        y = np.zeros((pool_length, self.pool_in_dim), dtype=float_keras())
        mask = np.ones((1, pool_length), dtype=float_keras())
        mask[0,:pool_begin_context] = 0
        mask[0,pool_length - pool_end_context:] = 0

        num_batches = int((in_length-in_seq_length)/in_shift+1)
        j_in = 0
        j_out = 0
        for i in xrange(num_batches):
            x_i = x[None,j_in:j_in+in_seq_length,:]
            y_i = self.prepool_net.predict(x_i, batch_size=1, **kwargs)[0]
            y[j_out:min(j_out+pool_seq_length, pool_length)] = y_i
            
            j_in += in_shift
            j_out += pool_shift
            if i==0:
                j_out += pool_left_context

        y = np.expand_dims(y, axis=0)
        embeds = self.pool_net.predict([y, mask], batch_size=1, **kwargs)
        return np.hstack(tuple(embeds))


    
    @property
    def embed_dim(self):
        if self.pool_net is None:
            return None
        embed_dim=0
        for node in xrange(len(self.pool_net.inbound_nodes)):
            output_shape = self.pool_net.get_output_shape_at(node)
            if isinstance(output_shape, list):
                for shape in output_shape:
                    embed_dim += shape[-1]
            else:
                embed_dim += output_shape[-1]

        return embed_dim

    
    
    def fit(**kwargs):
        self.model.fit(**kwargs)


        
    def fit_generator(self, generator, steps_per_epoch, **kwargs):
        self.model.fit_generator(generator, steps_per_epoch, **kwargs)


        
    def get_config(self):
        config = { 'pooling': self.pooling,
                   'loss': self.loss,
                   'left_context': self.left_context,
                   'right_context': self.right_context,
                   'begin_context': self.begin_context,
                   'end_context': self.end_context}
        base_config = super(SeqEmbed, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


    
    def save(self, file_path):
        file_model = '%s.json' % (file_path)
        with open(file_model, 'w') as f:
            f.write(self.to_json())
        
        file_model = '%s.net1.h5' % (file_path)
        self.prepool_net.save(file_model)
        file_model = '%s.net2.h5' % (file_path)
        self.postpool_net.save(file_model)


            
    @classmethod
    def load(cls, file_path):
        file_config = '%s.json' % (file_path)        
        config = SeqEmbed.load_config(file_config)
        
        file_model = '%s.net1.h5' % (file_path)
        prepool_net = load_model(file_model, custom_objects=get_keras_custom_obj())
        file_model = '%s.net2.h5' % (file_path)
        postpool_net = load_model(file_model, custom_objects=get_keras_custom_obj())

        filter_args = ('loss', 'pooling',
                       'left_context', 'right_context',
                       'begin_context', 'end_context', 'name')
        kwargs = {k: config[k] for k in filter_args if k in config }
        return cls(prepool_net, postpool_net, **kwargs)
    
    
    
    @staticmethod
    def filter_args(prefix=None, **kwargs):
        if prefix is None:
            p = ''
        else:
            p = prefix + '_'
        valid_args = ('pooling', 'left_context', 'right_context',
                      'begin_context', 'end_context')
        return dict((k, kwargs[p+k])
                    for k in valid_args if p+k in kwargs)

        
        
    @staticmethod
    def add_argparse_args(parser, prefix=None):
        if prefix is None:
            p1 = '--'
            p2 = ''
        else:
            p1 = '--' + prefix + '-'
            p2 = prefix + '_'

        parser.add_argument(p1+'pooling', dest=p2+'pooling', default='mean+std',
                            choices=['mean+std', 'mean+logvar', 'mean'])
        parser.add_argument(p1+'left-context', dest=(p2+'left_context'),
                            default=0, type=int)
        parser.add_argument(p1+'right-context', dest=(p2+'right_context'),
                            default=0, type=int)
        parser.add_argument(p1+'begin-context', dest=(p2+'begin_context'),
                            default=None, type=int)
        parser.add_argument(p1+'end-context', dest=(p2+'end_context'),
                            default=None, type=int)
