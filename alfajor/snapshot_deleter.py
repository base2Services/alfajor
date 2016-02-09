import sys
import re
import boto
import os
from boto import ec2
from datetime import date
sys.path.append("alfajor")
from aws_base import AWS_BASE

class SnapShotDeleter(AWS_BASE):
  def init(self):
    self.set_conn(boto.ec2.connect_to_region(**self.get_connection_settings()))

  def get_days(self, str):
    creation_date = str.split('T')[0].split('-')
    days_since_creation = (date.today() - date(int(creation_date[0]), int(creation_date[1]), int(creation_date[2]))).days
    return days_since_creation

  def print_results(self, data):
    for key,value in data.items():
      output = str(key)
      output = output + "\t" + str(self.get_days(value['start_time']))
      for k,v in value.items():
        output = output + "\t" + k + "\t" + str(v)
      print(output)

  def delete_all_orphans(self):
    reAmi = re.compile('ami-[^ ]+')
    reVol = re.compile('vol-[^ ]+')

    images = {}
    volumes = {}

    snapshots_no_info = {}
    snapshots_no_ami = {}
    snapshots_with_ami = {}
    snapshots_with_vol_info = {}
    count_snapshots = None

    #get a list of volumes
    for v in self.get_conn().get_all_volumes():
      name = ""
      if 'Name' in v.tags:
        name = v.tags['Name']
      volumes[v.id] = {'status' : v.status, 'Name' : name}

    #get a list of all our amis for use later
    for image in self.get_conn().get_all_images(owners=['self']):
      images[image.id] = { "Name" : image.name, "description" : str(image.description)}

    all_snapshots = self.get_conn().get_all_snapshots(owner='self')
    count_snapshots = len(all_snapshots)

    #parse snapshots and breakdown into 4 groups
    #1: no info that is useful
    #2: ami missing
    #3: do have their ami still
    #4: volume snapshots
    #Then delete those with the ami missing
    for snapshot in all_snapshots:
      snapshotId = snapshot.id
      #check the description of the snapshot and if
      # it matches the ami regex then we have an ami
      # derived snapshot
      amiIdResult = reAmi.findall(snapshot.description)
      if len(amiIdResult) != 1:
        #this missed the ami check - lets see if it matches
        #the volume regex?
        volIdResult = reVol.findall(snapshot.description)
        if len(volIdResult) != 1:
          #has failed both ami and volume reges add to the weird bucket
          snapshots_no_info[snapshotId] = {"start_time" : snapshot.start_time}
        else:
          #failed ami regex but matched vol regex
          snapshots_with_vol_info[snapshotId] = { 'vol' : volIdResult[0], 'info' : volumes[volIdResult[0]], "start_time" : snapshot.start_time}
      else:
        #extracted amiIdResult above based on regex
        #now lets see if it is in the list of current images
        amiId = amiIdResult[0]
        if amiId in images:
          #found it - add it to list of snaps with existing ami's
          snapshots_with_ami[snapshotId] = { 'ami' : amiId, 'info' : images[amiId], "start_time" : snapshot.start_time}
        else:
          snapshots_no_ami[snapshotId] = { 'ami' : amiId, "start_time" : snapshot.start_time}

    print("Total amis " + str(len(images)) + "\n")
    print("Total snapshots " + str(count_snapshots) + "\n")
    print("Total snapshots_no_info " + str(len(snapshots_no_info)) + "\n")
    print("Total snapshosts_no_ami (but has ami ref) " + str(len(snapshots_no_ami)) + "\n")
    print("Total snapshosts_with_ami (ami exists) " + str(len(snapshots_with_ami)) + "\n")
    print("Total snapshosts_with_vol " + str(len(snapshots_with_vol_info)) + "\n")

    test_result = count_snapshots - (len(snapshots_no_info) + len(snapshots_no_ami) + len(snapshots_with_ami) + len(snapshots_with_vol_info))
    print "snapshots - snapshots not accounted for (should be 0) " + str(test_result)
    self.print_results(snapshots_no_ami)
    #self.delete_snapshots(snapshots_no_ami)
    for key,value in snapshots_no_ami.items():
      print "deleting: " + str(key)
      try:
        snap = self.get_conn().delete_snapshot(key)
      except:
        print("error deleting: " + str(key))
        print(sys.exc_info()[0])
