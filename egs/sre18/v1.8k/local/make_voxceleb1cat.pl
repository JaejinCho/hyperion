#!/usr/bin/perl
#
# Copyright 2018  Ewald Enzinger
#           2018  David Snyder
#           2018  Jesus Villalba
#
# Apache 2.0
# Usage: make_voxceleb1cat.pl /export/voxceleb1 data/
# Note that this script also downloads a list of speakers that overlap
# with our evaluation set, SITW.  These speakers are removed from VoxCeleb1
# prior to preparing the dataset.
# Files from the same video are concatenated into 1 segment

if (@ARGV != 3) {
  print STDERR "Usage: $0 <path-to-voxceleb1> fs <path-to-data-dir>\n";
  print STDERR "e.g. $0 /export/voxceleb1 16 data/\n";
  exit(1);
}

($data_base, $fs, $out_dir) = @ARGV;
my $out_dir = "$out_dir/voxceleb1cat";

if (system("mkdir -p $out_dir") != 0) {
  die "Error making directory $out_dir";
}

# This file provides the list of speakers that overlap between SITW and VoxCeleb1.
if (! -e "$out_dir/voxceleb1_sitw_overlap.txt") {
  system("wget -O $out_dir/voxceleb1_sitw_overlap.txt http://www.openslr.org/resources/49/voxceleb1_sitw_overlap.txt");
}

# sitw_overlap contains the list of speakers that also exist in our evaluation set, SITW.
my %sitw_overlap = ();
open(OVERLAP, "<", "$out_dir/voxceleb1_sitw_overlap.txt") or die "Could not open the overlap file $out_dir/voxceleb1_sitw_overlap.txt";
while (<OVERLAP>) {
  chomp;
  my $spkr_id = $_;
  $sitw_overlap{$spkr_id} = ();
}

opendir my $dh, "$data_base/voxceleb1_wav" or die "Cannot open directory: $!";
my @spkr_dirs = grep {-d "$data_base/voxceleb1_wav/$_" && ! /^\.{1,2}$/} readdir($dh);
closedir $dh;


my %rec2utt = ();
my %rec2spk = ();
foreach (@spkr_dirs) {
  my $spkr_id = $_;
  # Only keep the speaker if it isn't in the overlap list.
  if (not exists $sitw_overlap{$spkr_id}) {
    opendir my $dh, "$data_base/voxceleb1_wav/$spkr_id/" or die "Cannot open directory: $!";
    my @files = map{s/\.[^.]+$//;$_}grep {/\.wav$/} readdir($dh);
    closedir $dh;
    foreach (@files) {
      my $filename = $_;
      my $rec_id = substr($filename, 0, 11);
      my $segment = substr($filename, 12, 7);
      my $wav = "$data_base/voxceleb1_wav/$spkr_id/$filename.wav";
      my $utt_id = "$spkr_id-$rec_id";
      if (not exists $rec2utt{$utt_id}) {
	  $rec2spk{$utt_id} = $spkr_id;
	  $rec2utt{$utt_id} = $wav
      }
      else {
	  $rec2utt{$utt_id} = $rec2utt{$utt_id} . " " . $wav
      }
    }
  }
}

open(SPKR, ">", "$out_dir/utt2spk") or die "Could not open the output file $out_dir/utt2spk";
open(WAV, ">", "$out_dir/wav.scp") or die "Could not open the output file $out_dir/wav.scp";

foreach my $utt_id (keys %rec2spk) {
    my $wav = "";
    if($fs == 8){
	$wav = "sox " . $rec2utt{$utt_id} . " -t wav -r 8k - |";
    }
    else{
	$wav = "sox " . $rec2utt{$utt_id} . " -t wav - |";
    }
    my $spkr_id = $rec2spk{$utt_id};
    print WAV "$utt_id", " $wav", "\n";
    print SPKR "$utt_id", " $spkr_id", "\n";
}

close(SPKR) or die;
close(WAV) or die;

if (system(
  "utils/utt2spk_to_spk2utt.pl $out_dir/utt2spk >$out_dir/spk2utt") != 0) {
  die "Error creating spk2utt file in directory $out_dir";
}
system("env LC_COLLATE=C utils/fix_data_dir.sh $out_dir");
if (system("env LC_COLLATE=C utils/validate_data_dir.sh --no-text --no-feats $out_dir") != 0) {
  die "Error validating directory $out_dir";
}

if (system(
  "utils/utt2spk_to_spk2utt.pl $out_dir/utt2spk >$out_dir/spk2utt") != 0) {
  die "Error creating spk2utt file in directory $out_dir";
}

system("env LC_COLLATE=C utils/fix_data_dir.sh $out_dir");
if (system("env LC_COLLATE=C utils/validate_data_dir.sh --no-text --no-feats $out_dir") != 0) {
  die "Error validating directory $out_dir";
}
