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

# Scripts

## Backup (scripts/backup.py)

Backups script will

### 1 - Cleanup previous AMIs

- Collect all instances tagged with given tag (defaults to `MakeSnapshot`)
- For each instance collect all AMI's created from that instance
- Calculate retention period based on instance tags
- For each of collected AMI's, compare retention period with creation date,
    and deregister AMI and delete backing EBS snapshots if required
- Repeat the process for EBS snapshots

### 2 - Create new AMIs and EBS snapshots

#### AMI

- Collect all instances tagged with given tag (defaults to `MakeSnapshot`)
- Create new AMI with appropriate name
- Tag AMI with all tags from `snapshot/snapshot_tags` map and `created_by_alfajor=true`
- Tag EBS snapshot that are backing ami with `created_by_alfajor=true` and `image_id=$amiid` tags

#### EBS

- Collect all volumes tagged with given tag (defaults to `MakeSnapshot`)
- Create new EBS snapshot with appropriate name