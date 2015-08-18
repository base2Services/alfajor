import boto
from boto.sts import STSConnection
import boto.sns
from alfajor import config
from config import Config
from pprint import pprint
import datetime
import uuid

class AWS_BASE(object):
  _config = None
  _connection_settings = None
  _conn = None
  _account = None
  _config_file = None
  _debug = None
  _verbose = None
  _description_start = None


  def __init__(self, **kwargs):
    self._config_file = kwargs.get('config_file', 'aws_config.yml')
    self._account = kwargs.get('account', 'default')
    self._notifications = kwargs.get('notifications', False)
    self._config = Config(account = self._account)
    self._connection_settings = self._config.get_connection_dictionary()
    self._debug = kwargs.get('debug', False)
    self._verbose = kwargs.get('verbose', False)
    self._dry_run = kwargs.get('dry_run', False)
    self._description_start = kwargs.get("description_start", "alfajor")
    self._connection_settings = self._generate_settings(self._config.get_connection_dictionary())
    self.init()



  def init(self):
    return None



  def get_date_string(self):
    i = datetime.datetime.now()
    date_string = ("%s%02d%02d_%02d%02d%02d" % (i.year, i.month, i.day, i.hour, i.minute, i.second) )
    return date_string



  def get_make_snapshot_tag(self):
    tag = "MakeSnapshot"
    c = self._config.get_config()
    #pprint(c)
    if "snapshot" in c:
      #pprint(c["snapshot"])
      if "make_snapshot_tag" in c["snapshot"]:
        tag = c["snapshot"]["make_snapshot_tag"]
    return tag



  def get_snapshot_tags(self):
    tags = {}
    c = self._config.get_config()
    #pprint(c)
    if "snapshot" in c:
      #pprint(c["snapshot"])
      if "snapshot_tags" in c["snapshot"]:
        #pprint(c["snapshot"]["snapshot_tags"])
        tags = c["snapshot"]["snapshot_tags"]
    return tags



  def set_tags(self, resource, tags):
    for tag, value in tags.iteritems():
      if not tag.startswith('aws:') and len(tag) < 127:#127 = max len for tag
        resource.add_tag(tag, value)



  def get_connection_settings(self):
    return self._connection_settings



  def set_conn(self, conn):
    self._conn = conn



  def get_conn(self):
    return self._conn



  def __str__(self):
    s = "Class: " + self.__class__.__name__ + "::" + str(self._config.get_config())
    return str(s)



  def dry_run(self):
    return self._dry_run



  def get_config(self):
    return self._config



  def set_notifications(self, on_off):
    self._notifications = on_off
    return true



  def get_notifications(self, on_off):
    return self._notifications



  def concat(self, args):
      s = ""
      for arg in args:
        s = s + str(arg)
      return s



  def log(self, *args):
    s = self.concat(args)
    self.notify(s)
    if self._verbose:
      self.verbose(s)
    elif self._debug:
      self.debug(s)
    else:
      print(s)



  def notify(self, *args):
    s = self.concat(args)
    if self.notifications:
      #TODO: SNS
      print "hi"



  def debug(self, *args):
    print self.concat(args)



  def verbose(self, *args):
    print self.concat(args)
    #TODO: if dict then pprint __dict__



  def get_retention_tag(self):
    #TODO: remove hard coded defaults?
    tag = "Retention"
    c = self._config.get_config()
    #print(c)
    if "snapshot" in c:
      #pprint(c["snapshot"])
      if "retention_tag" in c["snapshot"]:
        tag = c["snapshot"]["retention_tag"]
    self.debug("tar for retention:" + tag)
    return tag



  def get_retention_config(self):
    #TODO: cach result :: if not __retentions then do otherwise return __retentions
    retentions = {}
    c = self._config.get_config()
    #pprint(c)
    if "snapshot" in c:
      #pprint(c["snapshot"])
      if "retentions" in c["snapshot"]:
        #pprint(c["snapshot"]["snapshot_tags"])
        retentions = c["snapshot"]["retentions"]
    #TODO: get hardcoded values from lookup
    if not "default" in retentions:
      retentions["default"] = "month"
    if not "month" in retentions and retentions["default"] == "month":
      retentions["month"] = "28"
    self.verbose(retentions) #{'day': 1, 'default': 'month', 'month': 28, 'week': 7}
    return retentions



  def _generate_settings(self, config):
    if "assumed_role" in config and config["assumed_role"]:
      config = self._add_assumed_role(config)
    return config



  def _add_assumed_role(self, config):
    c = {}
    c['region_name'] = config['region_name']

    assumedRoleObject = STSConnection().assume_role(
      role_arn=config["assumed_role_arn"],
      role_session_name="assumeRole_" + uuid.uuid4().urn[-12:]
    )

    c["aws_access_key_id"] = assumedRoleObject.credentials.access_key
    c["aws_secret_access_key"] = assumedRoleObject.credentials.secret_key
    c["security_token"] = assumedRoleObject.credentials.session_token

    return c



  def get_default_wait(self):
    return 45

  def description_start(self):
    return _description_start

#TODO: assume role with accont connection first
#TODO: support proxy config
