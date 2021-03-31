# installation
## 1. git clone
## 2. change branch to perseus
## 3. run "./make_clsp_links.sh" at the root dir (../../..) to set up dependencies in clsp

# actual runs
mkdir -p log
bash run_001_prepare_data.sh 2>&1 | tee log/run_001_prepare_data.log # *** NOTE ***: if wget in local/download_sre04-12_master_key.sh does NOT work, manually download it and untar it. I spent quite a long time to solve this but did NOT work
