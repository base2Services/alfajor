import sys
import boto
import dateutil.parser
from datetime import datetime
from datetime import timedelta
import time
import traceback
from dateutil.relativedelta import relativedelta

sys.path.append("alfajor")
from aws_base import AWS_BASE
from boto import ec2
from alfajor import aws_base

class SnapShotCleanup(AWS_BASE):
    def init(self):
        self.set_conn(boto.ec2.connect_to_region(**self.get_connection_settings()))
    
    ##
    # Cleanup EBS snapshots created by aws_ec2.backup_volumes method. Snapshot discovery is done using
    #  'Created by Alfajor' tag in user's AWS Account
    # Will keep last n daily snapshots, based on volume 'Retention' tag. Defaults to last 28 days
    # Will keep last config.snapshot.keep_weekly_ebs weekly snapshots (created on Sunday)
    # Will keep last config.snapshot.keep_monthly_ebs monthly snapshots (created on 1st of the month)
    # Will tag all survived snapshots with expiry time and retention period type, if they aren't tagged already
    #    with this information
    ##
    def cleanup_stale_snapshots(self):

        # collect snapshots based on alfajor tag
        keep_weekly = self._config.get_config()['snapshot']['keep_weekly_ebs']
        keep_monthly = self._config.get_config()['snapshot']['keep_monthly_ebs']
        
        snapshots = self.get_conn().get_all_snapshots(owner='self', filters={'tag-key': 'Created by Alfajor'})
        delete_snapshots = []
        i=0
        for snapshot in snapshots:
            i = i + 1
            print "\n\n=== Processing snapshot {0} ({1}/{2}) \n".format(snapshot.id,i,len(snapshots))
            
            # get retention period, defaulting to 28 days
            if 'Retention' in snapshot.tags:
                retention_config = self.get_retention_config()
                retention = snapshot.tags['Retention']
                retention = retention_config[retention]
            else:
                retention = 28
            
            # calculate expire date
            date_created = dateutil.parser.parse(snapshot.start_time)
            keep_until = date_created + timedelta(days=retention)
            is_weekly = False
            is_monthly = False
            
            if date_created.weekday() == 6:
                keep_until = date_created + relativedelta(weeks=keep_weekly)
                print "WEEKLY SNAPSHOT"
                is_weekly = True
            elif date_created.day == 1:
                keep_until = date_created + relativedelta(months=keep_monthly)
                print "MOHTLY SNAPSHOT"
                is_monthly = True
            else:
                print "DAILY SNAPSHOT"
            
            now = datetime.now(keep_until.tzinfo)
            do_delete = now > keep_until
            
            if is_weekly:
                print "Retention for weekly snaps is {0} weeks".format(keep_weekly)
            elif is_monthly:
                print "Retention for monthly snaps is {0} months".format(keep_monthly)
            else:
                print "Retention for snap is {0} days".format(retention)
                
            print "Creation date for snap is {0}".format(snapshot.start_time)
            print "Snapshot expiry date is {0}".format(keep_until)
            print "Snapshot {0} be deleted".format("SHOULD" if do_delete else "SHOULD NOT")
            
            if is_weekly:
                type = 'weekly'
            elif is_monthly:
                type = 'monthly'
            else:
                type = 'daily'
            
            if do_delete:
                delete_snapshots.append(snapshot.id)
                if 'DeleteMarker' not in snapshot.tags:
                    snapshot.add_tag('DeleteMarker', 'true')
                    
            else:
                # set metadata about expiration date
                if 'KeepUntil' not in snapshot.tags:
                    snapshot.add_tag('KeepUntil', keep_until)
                    
                # set metadata about expiration retention period type
                if 'RetentionType' in snapshot.tags:
                    snapshot.add_tag('RetentionType', type)
                
                # implicitly set expiration retention period type in snapshot name
                if 'Name' not in snapshot.tags or not snapshot.tags['Name'].endswith("-{0}".format(type)):
                    name = snapshot.tags['Name'] if 'Name' in snapshot.tags else 'alfajor-volume-backup'
                    if name is not None:
                        snapshot.remove_tag('Name')
                    snapshot.add_tag('Name', '{0}-{1}'.format(name, type))
            
            
        print "\n\nTotal of {0} snapshots found for deletion".format(len(delete_snapshots))
        
        for snap_id in snapshots:
            self.delete_snapshot(snap_id)
    
    def delete_snapshot(self, snap_id, retry_times=8, sleep=15):
        count = 0
        # try deleting several times with sleep before giving up
        while True:
            try:
                print "\n\nDeleting snapshot {0}".format(snap_id)
                self.get_conn().delete_snapshot(snap_id)
                return
            except:
                print "Could not delete snapshot {0}:\n{1}".format(snap_id,traceback.format_exc())
                if count == retry_times:
                    print "Failing silently after {0} retries".format(retry_times)
                    return
                count = count + 1
                time.sleep(sleep)
                print "Retrying #{0}".format(count)
