import sys
import boto.ec2.cloudwatch
import datetime
sys.path.append("alfajor")
from aws_base import AWS_BASE
from boto.exception import BotoServerError


class ElbMetrics(AWS_BASE):
    def init(self):
        self.set_conn(boto.ec2.connect_to_region(**self.get_connection_settings()))

    def get_elb_stats(self, name, metric, namespace, statistic, period=300, region='ap-southeast-2', unit='Count'):
        try:
            cw = boto.ec2.cloudwatch.connect_to_region(region)
            stats = cw.get_metric_statistics(
                period,
                datetime.datetime.utcnow() - datetime.timedelta(seconds=7200),
                datetime.datetime.utcnow(),
                metric,
                namespace,
                statistic,
                dimensions={'LoadBalancerName': [name]},
                unit=unit
            )
            print len(stats)
            # if stats is empty, there is no traffic, therefore sum of requests is zero
            if not stats:
                sum_of_req = 0.0
            else:
                sum_of_req = (stats[0]['Sum'])
            current_value = int(round(sum_of_req))
            print current_value
        except BotoServerError, error:
            print >> sys.stderr, 'Boto API error: ', error