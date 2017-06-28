import boto
from boto import ec2
from alfajor import aws_base
from aws_base import AWS_BASE
from pprint import pprint
from datetime import date
import time
import re
import sys
import os
import json
import traceback

class EC2(AWS_BASE):

  def init(self):
    self.set_conn(boto.ec2.connect_to_region(**self.get_connection_settings()))
    self.__created_amis = []


  def list_attached_volumes(self):
    return self.list_volumes_by_condition("attached")


  def list_all_volumes(self):
    return self.list_volumes_by_condition()


  def list_volumes_by_condition(self, condition = "all"):
    vols = self.get_conn().get_all_volumes()
    counter = 0

    if condition == "unattached":
      condition == None

    for vol in vols:
      if (condition == "all") or (vol.attachment_state() == condition):
        self.log("state: ", vol.attachment_state())
        counter = counter + 1
        log("Volume: ", counter, ", ", vol.id, ", ", state, ",", vol.create_time, ", ", vol.size)
    return vols


  def list_unattached_volumes(self):
    return self.list_volumes_by_condition("unattached")


  def list_instances(self):
    self.list_tagged_instances()


  def list_tagged_instances(self, tag = "Name", value = "*"):
    self.list_reservations(self.get_tagged_reservations(tag, value))
    #return count?


  def get_tagged_reservations(self, tag = "Name", value = "*"):
    #print "debug in get_tagged_reseravations"
    #print len(self.get_conn().get_all_instances(filters={"tag:" + tag : value}))
    return self.get_conn().get_all_instances(filters={"tag:" + tag : value})


  def list_reservations(self, reservations):
    for r in reservations:
      for i in r.instances:
        self.print_instance(i)


  def print_instance(self, instance):
    l = instance.id, self.get_instance_name(instance), instance.state, instance.image_id, instance.launch_time, instance.private_ip_address, instance.tags, instance.instance_profile
    self.log(l)


  def get_instance_name(self, instance):
    name = "-"
    if "Name" in instance.tags:
      name = instance.tags["Name"]
    return name


  def pprint_instance(self, instance):
    pprint(instance.__dict__)



  def get_tagged_volumes(self, tag):
    #get all the volumes with the tag
    return None


  def create_images_from_tag(self, tag = None):
    #get tag if none
    #get instances
    #foreach create image
    return None


  def create_image(self, instance, no_reboot = True):
    self.log("\n\n==== CREATE AMI FOR INSTANCE {0} ====\n\n".format(instance.id))
    date_string = self.get_date_string()
    name = self.get_instance_name(instance) + "-" + self.get_date_string()
    description = self.description_start() + ": copy_of:" + name + " created_at:" + date_string + " original_instance:" + instance.id
    image_id = instance.create_image(name, description, no_reboot)

    self.log(image_id)
    #TODO: handle boto.exception.EC2ResponseError: for eventual consistency: try catch
    new_image = self.get_image_eventually_consistent(image_id)

    if new_image is None:
      self.freakout(new_image, " is none")
    else:
      new_tags = instance.tags
      s_tags = self.get_snapshot_tags()
      self.log(new_image.state)
      self.log(new_image.creationDate)
      #TODO: tag retention date
      for tag in s_tags:
        new_tags[tag] = s_tags[tag]
      new_tags['CreatedByAlfajor'] = 'true'
      self.set_tags_eventually_consistent(new_image, new_tags, wait = 45, retries =3)

      # Mark image id to add tags to snapshots
      self.__created_amis.append(new_image.id)
      
    return image_id

  def set_tags_eventually_consistent(self, resource, tags, wait = 15, retries = 9):
    counter = 0

    while counter < retries:
      try:
        self.set_tags(resource, tags)
      except:
        self.log("caught exception - sleeping ", wait ," then try set tags again")
        self.log(sys.exc_info()[0])
        time.sleep(float(wait))
      counter = counter + 1

    return None


  def get_image_eventually_consistent(self, image_id, wait = 15, retries = 9):
    counter = 0

    while counter < retries:
      try:
        new_image = self.get_conn().get_image(image_id)
        return new_image
      except:
        self.log("caught exception - sleeping ", wait ," then try get image_id again")
        self.log(sys.exc_info()[0])
        time.sleep(float(wait))
      counter = counter + 1

    return None


  def get_days_to_keep(self, instance):
    r_tag = self.get_retention_tag()
    retentions = self.get_retention_config()
    #e.g {'day': 1, 'default': 'month', 'month': 28, 'week': 7}
    #we need "default" = something
    #and that something has to be there and = some int
    #'default': 'month', 'month': 28
    self.verbose("default retention: " + str(retentions["default"]))
    self.verbose("default retention = " + str(retentions[retentions["default"]]))

    retention = None #month
    days_to_keep = retentions[retentions["default"]] #28

    #if no "Retention" tag then use default
    if r_tag in instance.tags:
      retention = instance.tags[r_tag]
      if retention in retentions:
         days_to_keep = retentions[retention]
      else:
        #retention does not match default from above will be used
        self.debug("retention interval not found - will use default")

    self.debug("retention = ", retention)
    self.debug("days to keep = " + str(retentions[retentions["default"]]))
    #e.g. 28
    return days_to_keep

  def tag_snapshots_for_image(self, ami_id):
    filters = { 'description' : "*{0}*".format(ami_id)}
    try:
      snapshots = self.get_conn().get_all_snapshots(filters=filters, owner = 'self')
    except:
      snapshots = []
        
    wait = 30
    max_retries = 6
    retries = 0
    self.log("Adding tags to snapshots for image {0}".format(ami_id))
    # perhaps snapshots are not visible yet, allow them some time to appear, max 3 minutes
    self.log("Discovered snapshots in run #1: " + str(snapshots))
    
    while len(snapshots) == 0 and retries < max_retries:
      time.sleep(wait)
      try:
        snapshots = self.get_conn().get_all_snapshots(filters=filters, owner = 'self')
      except:
        snapshots = []
        
      self.log("Discovered snapshots in run #" + str(retries + 2) + ": " + str(snapshots))
      retries = retries + 1
      
    for s in snapshots:
      self.log("tagging snapshot " + s.id + " for ami " + ami_id)
      retries = 0
      success = False
      while retries < max_retries and not success:
        try:
          s.add_tags({'CreatedByAlfajorAmiSnapshot': 'true', 'AMISnapshot': 'true', 'ImageId': ami_id})
          success = True
        except:
          print "Could not tag snapshot {0}:\n{1}".format(s.id,traceback.format_exc())
          retries = retries + 1
          print "Retrying #{0} ... ".format(retries)



  def list_snapshot_for_image(self, image):
    snapshots = self.get_conn().get_all_snapshots()
    regex_ami = re.compile('ami-[^ ]+')
    snapshot_versus_ami = {}

    for snapshot in snapshots:
      snap_image_ids = regex_ami.findall(snapshot.description)
      if len(snap_image_ids) ==1:
        snapshot_versus_ami[snapshot.id] = snap_image_ids[0]

    for s in snapshot_versus_ami:
      if snapshot_versus_ami[s] == image.id:
        s = "snapshot" + s + " for ami " + snapshot_versus_ami[s] + "\n\n"
        self.log(s)


  #for any instance, delete the ami's (unless keep_flag is defined and true)
  #for each ami that will be deleted find the ami's and delete them
  #delete the ami's older than the retention period
  def delete_with_retention(self, instance, delete = False):
    days_to_keep = self.get_days_to_keep(instance)

    filters = {"description" : "*original_instance:" + instance.id + "*"}

    images = self.get_conn().get_all_images(filters = filters)

    #TODO: also check for automation tag - else might be manual snapshot for some reason
    for image in images:
      creation_date = image.creationDate.split('T')[0].split('-')
      self.verbose("creation date:" + str(creation_date))
      days_since_creation = (date.today() - date(int(creation_date[0]), int(creation_date[1]), int(creation_date[2]))).days
      self.verbose("days since creation: " + str(days_since_creation))

      if days_since_creation > days_to_keep:
        self.log(image.id + " is going to be deregistered.\n description: " + image.description + " \ncreation_date: " + str(image.creationDate) + "\ntags:" + json.dumps(image.tags) + "\nDays since creation is : " + str(days_since_creation) + "\n")
        #self.debug(image.block_device_mapping.current_value.snapshot_id)
        if delete:
          self.deregister_image_eventually_consistent(image, self.get_default_wait)
          self.delete_ami_snapshots(image)

  def delete_ami_snapshots(self, image):
    snap_ids = []
    self.log("\n\n\n===== CLEANUP SNAPSHOTS FOR AMI {0} =====\n\n\n".format(image.id))
    for mount,device in image.block_device_mapping.iteritems():
      if device.snapshot_id != None:
        if device.snapshot_id.startswith("snap-"):
          snap_ids.append(device.snapshot_id)

    ami_snapshots = []
    try:
      ami_snapshots = self.get_conn().get_all_snapshots(snapshot_ids = snap_ids, owner = 'self')
    except boto.exception.EC2ResponseError as err:
      self.log("\nERROR | Could not find following AMI snapshots in account: {0}:\n{1}".format(snap_ids,err))
      
    # print filters
    # print ami_snapshots
    for snapshot in ami_snapshots:
      self.log("Cleaning up snapshot {0} for ami {1}".format(snapshot.id, image.id))
      snapshot.delete()


  def deregister_image_eventually_consistent(self, image, image_id, wait = 45, retries = 3):
    counter = 0

    while counter < retries:
      try:
        #image.deregister(delete_snapshot=True)
        self.debug("deregister for " + str(image.id))
        self.get_conn().deregister_image(image.id)
        return True
      except:
        self.log("caught exception - sleeping ", wait ," will then try deregister image again")
        self.log(sys.exc_info()[0])
        time.sleep(wait)
      counter = counter + 1


  def clean_backups(self, tag = None):#TODO: **kwargs
    reservations = self.get_tagged_reservations(tag, "true")
    self.list_reservations(reservations)
    for r in reservations:
      for i in r.instances:
        self.debug("\n\n\n===== CLEAN BACKUPS PROCESSING FOR INSTANCE {0} ======\n\n\n".format(i.id))
        #TODO: check for keep flag
        self.log(self.delete_with_retention(i,True))


  def create_instance_snapshots(self, tag = None):
    reservations = self.get_tagged_reservations(tag, "true")
    self.list_reservations(reservations)
    for r in reservations:
      for i in r.instances:
        self.log(self.create_image(i))

  def tag_created_ami_snapshots(self):
    for ami_id in self.__created_amis:
      self.tag_snapshots_for_image(ami_id)

  def create_backups(self, tag = None):
    if tag == None:
      tag = self.get_make_snapshot_tag()
      if tag == None:
        raise ValueError('No tag provided for backup and snapshot:instance_tag set')
      self.debug("tag for backups: " + tag)
      self.clean_backups(tag)
      self.create_instance_snapshots(tag)
      #TODO: self.clean_volume_backups(tag)
      self.backup_volumes(tag)
      self.tag_created_ami_snapshots()


  # ToDo: delete_unattached_volumes_keeptag_configfile():


  # VolumeKeepTag - Name:MakeSnapshot, Value:True
  def delete_unattached_volumes_with_keeptag(self, volumekeeptag):
    allvols = self.get_conn().get_all_volumes()
    counter = 0
    self.keeptag = volumekeeptag
    for vol in allvols:
        state = vol.attachment_state()
        # delete if MakeSnapshot does not exist (not set for a vol) and volume is unattached
        if state == None:
            loginstance = AWS_BASE()
            loginstance.log("VolumeKeepTag: ", self.keeptag, ", ", vol.id, ", ", vol.tags)
            if self.keeptag not in vol.tags:
              counter = counter + 1
              loginstance.log("Deleting: ", counter, ", ", vol.id, ", ", state, ",", vol.create_time, ", ", vol.size)
              vol.delete()


  def backup_volumes(self, tag):
    print "Backup Volumes"
    vols = self.get_tagged_volumes(tag, "true")
    print "Number of volumes found: %d" % (len(vols))
    date_string = self.get_date_string()

    for vol in vols:
      counter = 1
      wait = 10
      retries = 3

      while counter <= retries:
        try:
          print "Backup attempt number %d" % (counter)
          new_tag = vol.id + "-" + self.get_date_string()
          #TODO: = tags and volume name
          description = self.description_start() + ": created_at:" + date_string + " original_volume:" + vol.id
          print description
          snap = self.get_conn().create_snapshot(vol.id,description)
          snap.add_tag(tag, "true")
          snap.add_tag("Created by Alfajor", "true")
          break
        except:
          self.log("Caught exception - sleeping for %d seconds, will then try image backup again" % (wait))
          self.log(sys.exc_info()[0])
          time.sleep(wait)
        counter = counter + 1


  def get_tagged_volumes(self, tag = "Name", value = "*"):
    return self.get_conn().get_all_volumes(filters={"tag:" + tag : value})


#TODO: add tag
#TODO: startup
  def start_instance_with_tag(self, insttag, env, tier):
      self.instancetag = insttag
      self.environment = env
      self.stacktier = tier
      reservations = self.get_conn().get_all_instances()
      counter = 0
      for res in reservations:
        for instance in res.instances:
          # check if stopped
          if instance.state == 'stopped':
            if self.instancetag in instance.tags and self.environment in instance.tags and self.stacktier in instance.tags:
              counter = counter + 1
              loginstance = AWS_BASE()
              loginstance.log("Starting instance: ", counter, ", ", instance.id)
              instance.start()


#TODO: shutdown
  def stop_instance_with_tag(self, insttag, env, tier):
      self.instancetag = insttag
      self.environment = env
      self.stacktier = tier
      reservations = self.get_conn().get_all_instances()
      counter = 0
      for res in reservations:
        for instance in res.instances:
          # check if stopped
          if instance.state == 'running':
            if self.instancetag in instance.tags and self.environment in instance.tags and self.stacktier in instance.tags:
              counter = counter + 1
              loginstance = AWS_BASE()
              loginstance.log("Stopping instance: ", counter, ", ", instance.id)
              instance.stop()

#TODO: clean no tag with grace days
#TODO: sns notify
#TODO: list orphan snapshots
#TODO: clean unattached volumes by age
#TODO: wait for state - eg after create_image
#TODO: backup volume
