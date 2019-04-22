#!/usr/bin/env python

import roslaunch
import rospy
from sys import argv

if __name__ == '__main__':
    if len(argv) < 2:
        print('Lack argument.')
        exit(1)

    launchfile = argv[1]
    print("Launching {}.".format(launchfile))
    
    uuid = roslaunch.rlutil.get_or_generate_uuid(None, False)
    launch = roslaunch.parent.ROSLaunchParent(uuid, [launchfile])
    launch.start()
    rospy.loginfo("started")

    rospy.sleep(3)
    launch.shutdown()


