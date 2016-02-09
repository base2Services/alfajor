import sys
sys.path.append("alfajor")
import boto
from alfajor import snapshot_deleter

sd = snapshot_deleter.SnapShotDeleter(debug = True, verbose = True)
sd.delete_all_orphans()
