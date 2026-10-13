#!/usr/bin/python3

"""
planner.py
OpenShift upgrade planner.
Finds the shortest valid upgrade path from one given version of OpenShift
to another.
"""

import sys
from collections import deque
import argparse
import logging
from catalog import Catalog
from merged_catalog import MergedCatalog
logger = logging.getLogger(__name__)

# Do not fail CI merely because of a known issue.
# pylint: disable=fixme
# FIXME: The API seems to provide no way to discover this set of
# architectures, so we hard-code it here :-(
# Note that the x86_64 architecture is named 'amd64' here.
# There is no 'intel64' architecture.
ALL_ARCHES = ['amd64', 'aarch64', 'ppc64le', 's390x']
DEFAULT_ARCH = 'amd64'


def dump_catalog(cat):
    """
    Output a textual representation of the given Catalog.
    """
    logger.debug(repr(cat))
    for channel in cat.channels():
        logger.debug("  %s", repr(channel))
        for node in channel.nodes():
            logger.debug("    %s", repr(node))
            logger.debug("      Edges to this node:")
            for edge_to in node.edges_to():
                logger.debug("        %s", repr(edge_to))
            logger.debug("      Edges from this node:")
            for edge_from in node.edges_from():
                logger.debug("        %s", repr(edge_from))


def dump_merged_catalog(merged_cat):
    """
    Output a textual representation of the given MergedCatalog.
    """
    logger.debug(repr(merged_cat))
    for merged_node in merged_cat.merged_nodes():
        logger.debug("  %s", repr(merged_node))
        logger.debug("    Edges to this node:")
        for edge_to in merged_node.edges_to():
            logger.debug("      %s", repr(edge_to))
        logger.debug("    Edges from this node:")
        for edge_from in merged_node.edges_from():
            logger.debug("      %s", repr(edge_from))


# Hopefully, no OpenShift upgrade path ever contains this many steps!
INFINITY = 100000


def distance(edge):
    """
    Return the 'distance' between the versions of OpenShift represented by
    the given MergedEdge.
    Existence of risks causes a much larger distance.
    """
    return 1000 if edge.risks() else 1


def find_min(q, dist):
    """
    Given a set of MergedNodes q and a set of distances dist,
    find the MergedNode in q with minimal dist[q].
    """
    min_node = None
    min_dist = 0
    for v in q:
        if min_node is None or dist[v] < min_dist:
            min_node = v
            min_dist = dist[v]
    assert min_node is not None
    return min_node


def analyse_dijkstra(graph, source, allow_risks):
    """
    Analyse the given upgrade graph. Find all upgrade paths from starting
    version source.
    This is in preparation for the use of Djikstra's algorithm.
    """
    dist = {}
    prev = {}
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
            if edge.risks() and not allow_risks:
                continue
            (u, v) = (edge.from_node(), edge.to_node())
            alt = dist[u] + distance(edge)
            if alt < dist[v]:
                dist[v] = alt
                logger.debug(
                    "dijkstra: Setting prev[%s] to %s", repr(v), repr(u))
                prev[v] = u
    return prev


def build_shortest_path(prev, source, target):
    """
    Given a previously-analysed upgrade graph, use Djikstra's algorithm
    to find the shortest upgrade path from the OpenShift version represented
    by the MergedNode source, to the OpenShift version represented by the
    MergedNode target.
    """
    seq = deque()
    u = target
    if (u in prev and prev[u] is not None) or (u is source):
        while u is not None:
            seq.appendleft(u)
            u = prev[u]
    return seq


def shortest_path_risks(merged_cat, source, target, allow_risks=False):
    """
    Given a MergedCatalog, use Djikstra's algorithm to find the shortest
    upgrade path from the OpenShift version represented by the MergedNode
    from_version, to the OpenShift version represented by the MergedNode
    to_version, optionally allowing risks to be present.
    """
    prev = analyse_dijkstra(merged_cat, source, allow_risks)
    shortest = build_shortest_path(prev, source, target)
    return shortest


def shortest_path(merged_cat, from_version, to_version, allow_risks=False):
    """
    Given a MergedCatalog, use Djikstra's algorithm to find the shortest
    upgrade path from the OpenShift version represented by the MergedNode
    from_version, to the OpenShift version represented by the MergedNode
    to_version.
    First try to find a path without risks. If one is found, return it.
    If no path without risks can be found, try again allowing risks.
    """
    source = merged_cat.get_node_by_version(from_version)
    target = merged_cat.get_node_by_version(to_version)
    logger.debug("Looking for a risk-free path...")
    path = shortest_path_risks(merged_cat, source, target, allow_risks=False)
    if path:
        return path
    logger.debug("No risk-free path found. Trying again allowing risks...")
    return shortest_path_risks(merged_cat, source, target, allow_risks=False)


def path_equals(path1, path2):
    """
    Compare two upgrade paths.
    """
    if len(path1) != len(path2):
        return False
    for node1, node2 in zip(path1, path2):
        if node1.version() != node2:
            return False
    return True


def dump_risk(risk):
    print(f"Risk {risk.name()}: {risk.description()}. See: {risk.url()}")


def dump_path(merged_cat, p):
    """
    Output a textual representation of the given upgrade path.
    """
    for i in range(1, len(p)):
        source = p[i - 1]
        dest = p[i]
        edge = source.get_edge_to_node(dest)
        channel_names = edge.channel_names()
        if len(channel_names) == 1:
            print(f"Set channel to {channel_names[0]}")
        else:
            print(f"Set channel to any one of: {' '.join(channel_names)}")
        risks = edge.risks()
        print(f"Upgrade from {source.version()} to {dest.version()}")
        for risk in risks:
            dump_risk(risk)


def run_tests(merged_cat):
    """
    Run inline tests.
    """
    # Expected to fail, because there are no upgrade paths to version 4.1.10
    shortest = shortest_path(merged_cat, '4.1.5', '4.1.10')
    assert not shortest
    # Expected to fail, because there are no upgrade paths
    # from 4.2.0-0.hotfix-2020-09-19-234758
    shortest = shortest_path(
        merged_cat, '4.2.0-0.hotfix-2020-09-19-234758', '4.3.2'
    )
    assert not shortest
    # Expected to fail, because there is no version 4.1.5
    shortest = shortest_path(merged_cat, '4.1.4', '4.1.5')
    assert not shortest
    # Expected to fail, because there is no version 4.1.5
    shortest = shortest_path(merged_cat, '4.1.5', '4.1.9')
    assert not shortest
    # Expected to succeed in one step
    shortest = shortest_path(merged_cat, '4.1.4', '4.1.9')
    # dump_path(path)
    assert path_equals(shortest, ['4.1.4', '4.1.9'])
    # Expected to succeed
    shortest = shortest_path(merged_cat, '4.1.4', '4.22.14')
    dump_path(shortest)
    # FIXME: This is a valid and identical-length path:
    # 4.1.4 -> 4.1.14 -> 4.1.25 -> 4.1.41 -> 4.2.34 -> 4.3.38 -> 4.4.27 -> 4.5.20 -> 4.6.32 -> 4.7.21 -> 4.8.22 -> 4.9.50 -> 4.10.39 -> 4.11.27 -> 4.12.17 -> 4.13.24 -> 4.14.24 -> 4.15.24 -> 4.16.16 -> 4.17.16 -> 4.18.19 -> 4.19.19 -> 4.20.15 -> 4.21.25 -> 4.22.14
    assert path_equals(
        shortest,
        [
            '4.1.4',   '4.1.18',  '4.1.26',  '4.1.38',  '4.2.29',  '4.3.35',
            '4.4.27',  '4.5.35',  '4.6.26',  '4.7.34',  '4.8.17',  '4.9.40',
            '4.10.20', '4.11.47', '4.12.35', '4.13.51', '4.14.41', '4.15.52',
            '4.16.42', '4.17.36', '4.18.27', '4.19.29', '4.20.34', '4.21.31',
            '4.22.14'
        ]
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="OCP Upgrade Planner",
        epilog="Default ARCH is " + DEFAULT_ARCH
    )
    parser.add_argument(
        '--architecture', default=DEFAULT_ARCH, choices=ALL_ARCHES
    )
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
        print(
            "One of the (possibly many) shortest upgrade paths from OpenShift version "
            f"{args.from_version} to version {args.to_version} is:"
        )
        dump_path(merged_catalog, path)
    else:
        print(
            "There is no upgrade path from OpenShift version "
            f"{args.from_version} to version {args.to_version}."
        )
    sys.exit(0)
