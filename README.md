# alfajor
boto helper cake

##Python Dependencies
boto
pyyaml

##Usage
git clone ...

cp alfajor/sample_aws_config.yml aws_config.yml

vim aws_config.yml

python alfajor/scripts/list_instances.py [account]
python alfajor/scipts/list_orphan_snapshots.py [account]
