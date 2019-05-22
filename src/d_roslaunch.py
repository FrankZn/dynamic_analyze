#!/usr/bin/env python

import roslaunch
import rospy
import rosgraph
import rosservice
import roslaunch.netapi

import psutil
from sys import argv
from pprint import pprint
from xmlrpc.client import ServerProxy


class Topic:
    def __init__(self, _name, _type=""):
        self.name = _name
        self.type = _type
        self.publishers = set()
        self.subscribers = set()

    def print(self):
        print("Name: {}".format(self.name))
        print("Type: {}".format(self.type))
        print("Publishers:")
        print(self.publishers)
        print("Subscribers:")
        print(self.subscribers)


class Service:
    def __init__(self, _name, _type=""):
        self.name = _name
        self.type = _type
        self.providers = set()

    def print(self):
        print("Name: {}".format(self.name))
        print("Type: {}".format(self.type))
        print("Providers:")
        print(self.providers)


class Node:
    def __init__(self, config_node, master=None, caller_id=None):
        self.name = config_node.namespace + config_node.name
        self.package = config_node.package
        self.type = self.package + '/' + config_node.type

        if caller_id is None:
            caller_id = "/dynamic_analyzer"
        if master is None:
            master = rosgraph.Master(caller_id)

        try:
            self.api_uri = master.lookupNode(self.name)
        except:
            raise Exception("Node {} not found in graph.".format(self.name))
        else:
            _, _, self.pid = ServerProxy(self.api_uri).getPid(caller_id)

        self.published_topics = set()
        self.subscribed_topics = set()
        self.provided_services = set()

    def print(self):
        print("Name: {}".format(self.name))
        print("Type: {}".format(self.type))
        print("Api uri: {}".format(self.api_uri))
        print("Pid: {}".format(self.api_uri))
        print("Published topics: {}".format(self.published_topics))
        print("Subscribed topics: {}".format(self.subscribed_topics))
        print("Provided services: {}".format(self.provided_services))

def analyze_graph(launch):
    caller_id = "/dynamic_analyzer"
    master = rosgraph.Master(caller_id)
    try:
        published_topics, subscribed_topics, provided_services = master.getSystemState()
    except socket.error:
        raise ROSNodeIOException("Unable to communicate with master!")

    try:
        topic_types = master.getTopicTypes()
    except socket.error:
        raise ROSNodeIOException("Unable to communicate with master!")

    nodes = {}
    topics = {}
    services = {}

    # Build nodes
    def get_node_name_from_config_node(config_node):
        return config_node.namespace + config_node.name

    for config_node in launch.config.nodes:
        node_name = get_node_name_from_config_node(config_node)
        if node_name in nodes:
            raise Exception("Duplicate node: {}.".format(node_name))
        try:
            nodes[node_name] = Node(config_node)
        except Exception as e:
            print(e)

    # Build services
    for service_name, providers in provided_services:
        service_type = rosservice.get_service_type(service_name)
        services[service_name] = Service(service_name, service_type)
        services[service_name].providers.update(providers)
        # Add service to provider nodes
        for provider in providers:
            if provider in nodes:
                nodes[provider].provided_services.add(service_name)

    # Build topics
    for topic_name, topic_type in topic_types:
        topics[topic_name] = Topic(topic_name, topic_type)

    # Add publisher nodes to topics
    for topic_name, publishers in published_topics:
        if topic_name not in topics:
            raise Exception("Inconsistent topic: {}.".format(topic_name))
        topics[topic_name].publishers.update(publishers)
        # Add topic to publisher nodes
        for publisher in publishers:
            if publisher in nodes:
                nodes[publisher].published_topics.add(topic_name)

    # Add subscriber nodes to topics
    for topic_name, subscribers in subscribed_topics:
        if topic_name not in topics:
            raise Exception("Inconsistent topic: {}.".format(topic_name))
        topics[topic_name].subscribers.update(subscribers)
        # Add topic to subscriber nodes
        for subscriber in subscribers:
            if subscriber in nodes:
                nodes[subscriber].subscribed_topics.add(topic_name)

    return nodes, topics, services


def d_launch(launchfile, time_to_run=5):
    """
    @param launchfile: launch file name
    @type  launchfile: string
    @return: nodes, topics, services
    @rtype: {str: Node}, {str: Topic}, {str: Service}
    """

    uuid = roslaunch.rlutil.get_or_generate_uuid(None, False)
    launch = roslaunch.parent.ROSLaunchParent(uuid, [launchfile])
    print("-" * 80)
    print("INFO: Launch file loaded. uuid: {}".format(uuid))

    launch.start()
    print("-" * 80)
    print("INFO: Launch starts.")
    rospy.sleep(time_to_run)
    print("------ {} secs ------".format(time_to_run))


    nodes, topics, services = analyze_graph(launch)

    launch.shutdown()
    print("------ Shutdown ------")

    return nodes, topics, services


def gen_features(nodes, topics, services):
    """
    @return: dict of (node_type, features)
    @rtype: {str: [str]}
    """
    feature_dict = {}
    for node in nodes.values():
        features = set()
        # Add features of published topic
        for topic_name in node.published_topics:
            if topic_name not in topics:
                raise Exception("Inconsistent topic: {}.".format(topic_name))
            features.add('pub#{}'.format(topics[topic_name].type))

        # Add features of subscribed topic
        for topic_name in node.subscribed_topics:
            if topic_name not in topics:
                raise Exception("Inconsistent topic: {}.".format(topic_name))
            features.add('sub#{}'.format(topics[topic_name].type))

        # Add features of provided service
        for service_name in node.provided_services:
            if service_name not in services:
                raise Exception("Inconsistent service: {}.".format(service_name))
            features.add('srv#{}'.format(services[service_name].type))

        feature_dict[node.type] = list(features)
    return feature_dict

if __name__ == '__main__':
    if len(argv) < 2:
        print('Lack argument.')
        exit(1)

    if len(argv) == 3:
        time_to_run = int(argv[2])
    else:
        time_to_run = 5

    launchfile = argv[1]

    nodes, topics, services = d_launch(launchfile, time_to_run)
    feature_dict = gen_features(nodes, topics, services)

    print()
    for node in nodes.values():
        node.print()
        print()

    for topic in topics.values():
        topic.print()
        print()

    for service in services.values():
        service.print()
        print()

    pprint(feature_dict)
