#!/usr/bin/python3

from sys import exit
from catalog import Catalog
from merged_catalog import MergedCatalog
from collections import deque
import argparse
import logging
logger = logging.getLogger(__name__)

# FIXME: THe API seems to provide no way to discover this set of architectures, so we hard-code it here :-(
# Note that the x86_64 architecture is named 'amd64' here. There is no 'intel64' architecture.
ALL_ARCHES=['amd64', 'aarch64', 'ppc64le', 's390x']
DEFAULT_ARCH='amd64'

def dump_catalog(catalog):
    logger.debug(repr(catalog))
    for channel in catalog.channels():
        logger.debug("  " + repr(channel))
        for node in channel.nodes():
            logger.debug("    %s" % repr(node))
            logger.debug("      Edges to this node:")
            for edge_to in node.edges_to():
                logger.debug("        " + repr(edge_to))
            logger.debug("      Edges from this node:")
            for edge_from in node.edges_from():
                logger.debug("        " + repr(edge_from))

def dump_merged_catalog(merged_catalog):
    logger.debug(repr(merged_catalog))
    for merged_node in merged_catalog.merged_nodes():
        logger.debug("  %s" % repr(merged_node))
        logger.debug("    Edges to this node:")
        for edge_to in merged_node.edges_to():
            logger.debug("      " + repr(edge_to))
        logger.debug("    Edges from this node:")
        for edge_from in merged_node.edges_from():
            logger.debug("      " + repr(edge_from))

# Hopefully, no OpenShift upgrade path ever contains this many steps!
INFINITY=100000

def distance(u, v):
    return 1

def find_min(q, dist):
    min_node = None
    min_dist = 0
    for v in q:
        if min_node is None or dist[v] < min_dist:
            min_node = v
            min_dist = dist[v]
    return min_node

def analyse_dijkstra(graph, source):
    dist = dict()
    prev = dict()
    q = set()
    for v in graph.merged_nodes():
        dist[v] = INFINITY
        prev[v] = None
        q.add(v)
    dist[source] = 0

    while len(q) > 0:
        u = find_min(q, dist)
        q.remove(u)
        for edge in graph.edges():
            (u, v) = (edge.from_node(), edge.to_node())
            alt = dist[u] + distance(u, v)
            if alt < dist[v]:
                dist[v] = alt
                # logger.debug("dijkstra: Setting prev[%s] to %s" % (repr(v), repr(u)))
                prev[v] = u
    return prev

def build_shortest_path(prev, source, target):
    # logger.debug("In build_shortest_path")
    # logger.debug(repr(prev))
    # logger.debug(repr(source))
    # logger.debug(repr(target))
    seq = deque()
    u = target
    if (u in prev and prev[u] is not None) or (u is source):
        while u is not None:
            seq.appendleft(u)
            u = prev[u]
    return seq

def shortest_path(merged_catalog, from_version, to_version):
    source = merged_catalog.get_node_by_version(from_version)
    target = merged_catalog.get_node_by_version(to_version)
    prev = analyse_dijkstra(merged_catalog, source)
    path = build_shortest_path(prev, source, target)
    return path

def path_equals(path1, path2):
    if len(path1) != len(path2):
        return False
    for node1, node2 in zip(path1, path2):
        if node1.version() != node2:
            return False
    return True

def dump_path(path):
    print(" -> ".join(node.version() for node in path))

def run_tests(merged_catalog):
    # Expected to fail, because there are no upgrade paths to version 4.1.10
    path = shortest_path(merged_catalog, '4.1.5', '4.1.10')
    assert not path
    # Expected to fail, because there are no upgrade paths from 4.2.0-0.hotfix-2020-09-19-234758
    path = shortest_path(merged_catalog, '4.2.0-0.hotfix-2020-09-19-234758', '4.3.2')
    assert not path
    # Expected to fail, because there is no version 4.1.5
    path = shortest_path(merged_catalog, '4.1.4', '4.1.5')
    assert not path
    # Expected to fail, because there is no version 4.1.5
    path = shortest_path(merged_catalog, '4.1.5', '4.1.9')
    assert not path
    # Expected to succeed in one step
    path = shortest_path(merged_catalog, '4.1.4', '4.1.9')
    # dump_path(path)
    assert path_equals(path, [ '4.1.4', '4.1.9' ])
    # Expected to succeed
    path = shortest_path(merged_catalog, '4.1.4', '4.22.14')
    # dump_path(path)
    assert path_equals(path, [ '4.1.4', '4.1.18', '4.1.26', '4.1.38', '4.2.29', '4.3.35', '4.4.27', '4.5.35', '4.6.26', '4.7.34', '4.8.17', '4.9.40', '4.10.20', '4.11.47', '4.12.35', '4.13.51', '4.14.41', '4.15.52', '4.16.42', '4.17.36', '4.18.27', '4.19.29', '4.20.34', '4.21.31', '4.22.14' ])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="OCP Upgrade Planner",
        epilog="Default ARCH is " + DEFAULT_ARCH
    )
    parser.add_argument('--architecture', default=DEFAULT_ARCH, choices=ALL_ARCHES)
    parser.add_argument('--from-version', required=True)
    parser.add_argument('--to-version', required=True)
    args = parser.parse_args()
    logger.info("Downloading catalogs from the Interwebs...")
    catalog = Catalog(args.architecture)
    catalog.assert_valid()
    # dump_catalog(catalog)
    logger.info("Analysing downloaded catalogs...")
    merged_catalog = MergedCatalog(catalog)
    # dump_merged_catalog(merged_catalog)
    merged_catalog.assert_valid()
    # run_tests(merged_catalog)
    logger.info("Calculating shortest path...")
    path = shortest_path(merged_catalog, args.from_version, args.to_version)
    if len(path):
        print("The shortest upgrade path from OpenShift version %s to version %s is:" % (args.from_version, args.to_version))
        dump_path(path)
    else:
        print("There is no upgrade path from OpenShift version %s to version %s." % (args.from_version, args.to_version))
    exit(0)
