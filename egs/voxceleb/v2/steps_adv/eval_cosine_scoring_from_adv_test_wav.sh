#!/bin/bash
# Copyright 2020 Johns Hopkins University (Jesus Villalba)  
# Apache 2.0.
#
nj=20
cmd=run.pl
feat_config=conf/fbank80_stmn_16k.conf
use_gpu=false
#center=true
#norm_var=false
#context=150
#attack_type=fgsm
smooth_sigma=0
#eps=0
#alpha=0
#snr=100
#confidence=0
#lr=1e-2
#max_iter=10
threshold=0
save_wav=false
save_wav_path=""
#c_factor=2
cal_file=""
attack_opts="--attack-attack-type fgsm --attack-eps 1e-3"

if [ -f path.sh ]; then . ./path.sh; fi
. parse_options.sh || exit 1;
set -e

if [ $# -ne 7 ]; then
  echo "Usage: $0 [options] <key> <enroll-file> <test-data-dir> <vector-file> <nnet-model> <output-scores> <output-snr>"
  echo "Options: "
  echo "  --feat-config <config-file>                      # feature extractor config"
  #echo "  --audio-feat <logfb|mfcc>                        # feature type"
  echo "  --nj <nj>                                        # number of parallel jobs"
  echo "  --cmd (utils/run.pl|utils/queue.pl <queue opts>) # how to run jobs."
  #echo "  --center <true|false>                            # If true, normalize means in the sliding window cmvn (default:true)"
  #echo "  --norm-var <true|false>                          # If true, normalize variances in the sliding window cmvn (default:false)"
  echo "  --use-gpu <bool|false>                           # If true, use GPU."
  #echo "  --context <int|150>                              # Left context for short-time cmvn (default: 150)"
  #echo "  --attack-type <str|fgsm>                         # Attack type"
  #echo "  --eps <float|0>                                  # Attack epsilon"
  #echo "  --alpha <float|0>                                # Attack alpha"
  #echo "  --snr <float|100>                                # Attack SNR"
  #echo "  --confidence <float|0>                           # confidence in Carlini-Wagner attack"
  #echo "  --lr <float|1e-2>                                # learning rate for attack optimizer"
  #echo "  --max-iter <int|10>                              # max number of iters for attack optimizer"
  #echo "  --c-factor <int|2>                               # c increment factor"
  echo "  --threshold <float|0>                            # decision threshold"
  echo "  --save-wav-path <str|>                           # path to save adv wavs"
  echo "  --cal-file <str|>                                # calibration params file"
  echo "  --smooth-sigma <float|0>                         # smoothing std"
  echo "  --attack-opts <str>                              # options for the attack"
  exit 1;
fi

key_file=$1
enroll_file=$2
test_data=$3
vector_file=$4
nnet_file=$5
output_file=$6
stats_file=$7

output_dir=$(dirname $output_file)
log_dir=$output_dir/log

mkdir -p $log_dir
name=$(basename $output_file)


wav=$test_data/wav.scp
vad=$test_data/vad.scp

required="$wav $feat_config $key $enroll_file $vector_file $vad"

for f in $required; do
  if [ ! -f $f ]; then
    echo "$0: no such file $f"
    exit 1;
  fi
done

num_gpus=0
args=""
if [ "$use_gpu" == "true" ];then
    cmd="$cmd --gpu 1"
    num_gpus=1
    args="--use-gpu"
fi

if [ "${save_wav}" == "true" ];then
    args="${args} --save-adv-wav-path $save_wav_path --save-adv-wav"
fi

if [ -n "$cal_file" ];then
    args="${args} --cal-file $cal_file"
fi

echo "$0: score $key_file to $output_dir"

$cmd JOB=1:$nj $log_dir/${name}.JOB.log \
    hyp_utils/torch.sh --num-gpus $num_gpus \
    steps_adv/torch-eval-cosine-scoring-from-adv-test-wav.py \
    @$feat_config ${args} \
    --v-file scp:$vector_file \
    --key-file $key_file \
    --enroll-file $enroll_file \
    --test-wav-file $wav \
    --vad scp:$vad \
    --model-path $nnet_file \
    --threshold $threshold \
    --score-file $output_file \
    --stats-file $stats_file \
    --smooth-sigma $smooth_sigma ${attack_opts} \
    --seg-part-idx JOB --num-seg-parts $nj || exit 1

    # --attack-type $attack_type \
    # --attack-snr $snr \
    # --attack-eps $eps \
    # --attack-alpha $alpha \
    # --attack-confidence $confidence \
    # --attack-lr $lr \
    # --attack-max-iter $max_iter \
    # --attack-c-incr-factor $c_factor \


for((j=1;j<=$nj;j++));
do
    cat $output_file-$(printf "%03d" 1)-$(printf "%03d" $j)
done | sort -u > $output_file

for((j=1;j<=$nj;j++));
do
    file_j=$stats_file-$(printf "%03d" 1)-$(printf "%03d" $j)
    if [ $j -eq 1 ];then
	head -n 1 $file_j
    fi
    tail -n +2 $file_j
done > $stats_file



