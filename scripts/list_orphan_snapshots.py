import sys
import re
import boto
import os
from datetime import date
sys.path.append("alfajor")
from alfajor import aws_ec2

account = "default"
if len(sys.argv) > 1:
  account = sys.argv[1]

ec2 = aws_ec2.EC2(debug = True, verbose = True, account = account)

reAmi = re.compile('ami-[^ ]+')
reVol = re.compile('vol-[^ ]+')

images = {}
volumes = {}
snapshots_no_info = {}
snapshots_no_ami = {}
snapshots_with_ami = {}
snapshots_with_vol_info = {}
count_snapshots = None

f = open('/tmp/orphan_snapshot_report_' + account + '.txt','w')

for v in ec2.get_conn().get_all_volumes():
  name = ""
  if 'Name' in v.tags:
    name = v.tags['Name']
  volumes[v.id] = {'status' : v.status, 'Name' : name}

for image in ec2.get_conn().get_all_images(owners=['self']):
  images[image.id] = { "Name" : image.name, "description" : str(image.description)}

all_snapshots = ec2.get_conn().get_all_snapshots(owner='self')
count_snapshots = len(all_snapshots)

for snapshot in all_snapshots:
  snapshotId = snapshot.id
  amiIdResult = reAmi.findall(snapshot.description)
  if len(amiIdResult) != 1:
    volIdResult = reVol.findall(snapshot.description)
    if len(volIdResult) != 1:
      snapshots_no_info[snapshotId] = {"start_time" : snapshot.start_time}
    else:
      snapshots_with_vol_info[snapshotId] = { 'vol' : volIdResult[0], 'info' : volumes[volIdResult[0]], "start_time" : snapshot.start_time}
  else:
    amiId = amiIdResult[0]
    if amiId in images:
      snapshots_with_ami[snapshotId] = { 'ami' : amiId, 'info' : images[amiId], "start_time" : snapshot.start_time}
    else:
      snapshots_no_ami[snapshotId] = { 'ami' : amiId, "start_time" : snapshot.start_time}

f.write("Total amis " + str(len(images)) + "\n")
f.write("Total snapshots " + str(count_snapshots) + "\n")
f.write("Total snapshots_no_info " + str(len(snapshots_no_info)) + "\n")
f.write("Total snapshosts_no_ami (but has ami ref) " + str(len(snapshots_no_ami)) + "\n")
f.write("Total snapshosts_with_ami (ami exists) " + str(len(snapshots_with_ami)) + "\n")
f.write("Total snapshosts_with_vol " + str(len(snapshots_with_vol_info)) + "\n")

test_result = count_snapshots - (len(snapshots_no_info) + len(snapshots_no_ami) + len(snapshots_with_ami) + len(snapshots_with_vol_info))
print "snapshots - snapshots not accounted for (should be 0) " + str(test_result)

def get_days(str):
  creation_date = str.split('T')[0].split('-')
  days_since_creation = (date.today() - date(int(creation_date[0]), int(creation_date[1]), int(creation_date[2]))).days
  return days_since_creation

def print_results(data):
  for key,value in data.items():
    output = "snapshot: " + str(key)
    for k,v in value.items():
      output = output + " " + k + ": " + str(v)
    output = output + " days: " + str(get_days(value['start_time']))
    f.write(output + "\n")

f.write("""
**************************************************
Snapshots with missing ami
**************************************************
This is based on the ami ref in their description.
When looking up the ami it is not there.
(Orphans)
**************************************************
""")
print_results(snapshots_no_ami)

f.write("""
**************************************************
Snapshots with an ami in their description where
the ami still exists
**************************************************
""")
print_results(snapshots_with_ami)

f.write("""
**************************************************
Snapshots that were based on a volume.
Volume Could exist or not
**************************************************
""")
print_results(snapshots_with_vol_info)

f.write("""
**************************************************
Snapshots with no ami info and no volume info in
description
**************************************************
""")
print_results(snapshots_no_info)
