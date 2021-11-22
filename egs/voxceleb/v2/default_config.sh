# Default parameters
# LResNet34 x-vector without mixed precision training

# acoustic features
feat_config=conf/fbank80_stmn_16k.yaml
feat_type=fbank80_stmn

#vad
vad_config=conf/vad_16k.yaml

# x-vector training 
nnet_data=voxceleb2_train
nnet_num_augs=1
aug_opt="--train-aug-cfg conf/reverb_noise_aug.yaml --val-aug-cfg conf/reverb_noise_aug.yaml"

batch_size_1gpu=128
eff_batch_size=512 # effective batch size
ipe=$nnet_num_augs
min_chunk=4
max_chunk=4
lr=0.05

nnet_type=lresnet34 #light resnet
dropout=0
embed_dim=256

s=30
margin_warmup=20
margin=0.3

nnet_opt="--resnet-type $nnet_type --in-feats 80 --in-channels 1 --in-kernel-size 3 --in-stride 1 --no-maxpool"

opt_opt="--optim.opt-type adam --optim.lr $lr --optim.beta1 0.9 --optim.beta2 0.95 --optim.weight-decay 1e-5 --optim.amsgrad"
lrs_opt="--lrsched.lrsch-type exp_lr --lrsched.decay-rate 0.5 --lrsched.decay-steps 8000 --lrsched.hold-steps 40000 --lrsched.min-lr 1e-5 --lrsched.warmup-steps 1000 --lrsched.update-lr-on-opt-step"

nnet_name=${feat_type}_${nnet_type}_e${embed_dim}_arcs${s}m${margin}_do${dropout}_adam_lr${lr}_b${eff_batch_size}.v1
nnet_num_epochs=70
nnet_dir=exp/xvector_nnets/$nnet_name


# back-end
nnet=$nnet_dir/model_ep0070.pth
state_dict_key=model_teacher_state_dict
plda_num_augs=0
plda_data=voxceleb1_test_train
plda_type=splda
lda_dim=200
plda_y_dim=150
plda_z_dim=200

