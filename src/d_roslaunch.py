#!/usr/bin/env python

import roslaunch
import rospy
import rosnode
import rostopic
import rosservice
import rosgraph
from sys import argv
from pprint import pprint

class Topic:
    topic_name = ""
    topic_type = ""
    publishers = []
    subscribers = []
    def __init__(self, _name, _type=""):
        self.topic_name = _name
        self.topci_type = _type
    def print(self):
        print("Name: {}".format(self.topic_name))
        print("Type: {}".format(self.topic_type))
        print("Publishers:")
        for p in self.publishers:
            print(p)
        print("Subscribers:")
        for s in self.subscribers:
            print(s)


if __name__ == '__main__':
    if len(argv) < 2:
        print('Lack argument.')
        exit(1)

    launchfile = argv[1]
    print("Launching {}.".format(launchfile))
    
    uuid = roslaunch.rlutil.get_or_generate_uuid(None, False)
    launch = roslaunch.parent.ROSLaunchParent(uuid, [launchfile])

    launch.start()
    print("------ Start ------")
    rospy.sleep(5)
    print("------ 5 secs ------")

    ID = "dynamic_analyzer"
    master = rosgraph.Master(ID)
    try:
        state = master.getSystemState()
    except socket.error:
        raise ROSNodeIOException("Unable to communicate with master!")
    
    pprint(state)

    topics = {}

    for publishers in state[0]:
        if publishers[0] not in topics:
            topics[publishers[0]] = Topic(publishers[0])
        topics[publishers[0]].publishers.extend(publishers[1])

    for subscribers in state[1]:
        if subscribers[0] not in topics:
            topics[subscribers[0]] = Topic(subscribers[0])
        topics[subscribers[0]].subscribers.extend(subscribers[1])

    for topic in topics:
        topics[topic].print()

    launch.shutdown()
    print("------ Shutdown ------")


