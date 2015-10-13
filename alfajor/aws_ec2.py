import boto
from boto import ec2
from alfajor import aws_base
from aws_base import AWS_BASE
from pprint import pprint
from datetime import date
import time
import re
import sys

class EC2(AWS_BASE):

  def init(self):
    self.set_conn(boto.ec2.connect_to_region(**self.get_connection_settings()))



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
        log("Unattached: ", counter, ", ", vol.id, ", ", state, ",", vol.create_time, ", ", vol.size)
    return vols



  def list_unattached_volumes(self):
    return self.list_volumes_by_condition("unattached")



  def list_instances(self):
    self.list_tagged_instances()



  def list_tagged_instances(self, tag = "Name", value = "*"):
    self.list_reservations(self.get_tagged_reservations(tag, value))
    #return count?



  def get_tagged_reservations(self, tag = "Name", value = "*"):
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
    date_string = self.get_date_string()
    name = self.get_instance_name(instance) + "-" + self.get_date_string()
    description = self.description_start() + ": copy_of:" + name + " created_at:" + date_string + " original_instance:" + instance.id
    image_id = instance.create_image(name, description, no_reboot)
    self.log("backup for:", instance.id)

    self.log(image_id)
    #TODO: handle boto.exception.EC2ResponseError: for eventual consistency: try catch
    new_image = self.get_image_eventually_consistent(image_id, self.get_default_wait)

    if new_image is None:
      self.freakout(new_image, "is none")
    else:
      new_tags = instance.tags
      s_tags = self.get_snapshot_tags()
      self.log(new_image.state)
      self.log(new_image.creationDate)
      #TODO: tag retention date
      for tag in s_tags:
        new_tags[tag] = s_tags[tag]
      self.set_tags(new_image, new_tags)

    return image_id


  def get_image_eventually_consistent(self, image_id, wait = 45, retries = 3):
    counter = 0

    while counter < retries:
      try:
        new_image = self.get_conn().get_image(image_id)
        return new_image
      except:
        self.log("caught exception - sleeping ", wait ," then try get image_id again")
        self.log(sys.exc_info()[0])
        time.sleep(wait)
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
        self.debug(image.id + " is going to be deregistered")
        self.debug("description " + image.description)
        self.debug("creation_date: " + str(image.creationDate))
        self.debug("tags:" + str(image.tags))
        self.debug("Days since creation is : " + str(days_since_creation))
        #self.debug(image.block_device_mapping.current_value.snapshot_id)
        if delete:
          deregister_image_eventually_consistent(image, self.get_default_wait)
          .deregister(delete_snapshot=True)


  def deregister_image_eventually_consistent(image, image_id, wait = 45, retries = 3):
    counter = 0

    while counter < retries:
      try:
        image.deregister(delete_snapshot=True)
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
        self.debug("clean backups processing: " + i.id)
        #TODO: check for keep flag
        self.log(self.delete_with_retention(i,True))



  def create_instance_snapshots(self, tag = None):
    reservations = self.get_tagged_reservations(tag, "true")
    self.list_reservations(reservations)
    for r in reservations:
      for i in r.instances:
        self.log(self.create_image(i))



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



  def delete_unattached_volumes(self):
    counter = 0
    vols = self.get_conn().get_all_volumes()
    for vol in vols:
      state = vol.attachment_state()
      if state == None:
        counter = counter + 1
        loginstance = AWS_BASE()
        loginstance.log("Unattached: ", counter, ", ", vol.id, ", ", state, ",", vol.create_time, ", ", vol.size)
        vol.delete()



  def backup_volumes(self, tag):
    vols = self.get_tagged_volumes(tag, "true")
    date_string = self.get_date_string()
    #name = self.get_instance_name(instance) + "-" + self.get_date_string()
    for vol in vols:
      #new_tag = vol.id + "-" + self.get_date_string()
      #TODO: = tags and volume name
      description = self.description_start() + ": created_at:" + date_string + " original_volume:" + vol.id
      try:
        self.log("creating snapshot for volume:", vol.id)
        new_snapshot = vol.create_snapshot(description)
        #tags
        #get snapshot adn apply tags
      except:
        self.log("caught exception - sleeping ", self.get_default_wait)
        self.log(sys.exc_info()[0])
        time.sleep(self.get_default_wait())


  def get_tagged_volumes(self, tag = "Name", value = "*"):
    return self.get_conn().get_all_volumes(filters={"tag:" + tag : value})




#TODO: add tag
#TODO: startup
#TODO: shutdown
#TODO: clean no tag with grace days
#TODO: sns notify
#TODO: list orphan snapshots
#TODO: clean unattached volumes by age
#TODO: wait for state - eg after create_image
#TODO: backup volume
