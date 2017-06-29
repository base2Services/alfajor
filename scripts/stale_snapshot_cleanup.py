import sys
import os

pwd = os.environ['PWD']
alfajor_path = "{0}".format(pwd)  # if running from alfajor root
alfajor_path2 = "{0}/..".format(pwd)  # if running from scripts folder
alfajor_path3 = "{0}/alfajor".format(pwd)  # if running from folder above alfajor

for path in [alfajor_path, alfajor_path2, alfajor_path3]:
    sys.path.append(path)

from alfajor import stale_snapshot_cleanup

# requires explicit delete command, otherwise will only list the EBS Snapshots

if 'DO_DELETE' in os.environ:
    dry_run = not os.environ['DO_DELETE'] == str(1)
else:
    dry_run = True

account = sys.argv[1]
sd = stale_snapshot_cleanup.SnapShotCleanup(debug=True, verbose=True,account=account)
sd.cleanup_stale_snapshots(dry_run=dry_run)
