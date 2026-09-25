#!/usr/bin/python3

from sys import exit
from catalog import Catalog
from merged_catalog import MergedCatalog
import logging
logger = logging.getLogger(__name__)

ARCH='amd64'

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

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    catalog = Catalog(ARCH)
    catalog.assert_valid()
    # dump_catalog(catalog)
    merged_catalog = MergedCatalog(catalog)
    dump_merged_catalog(merged_catalog)
    merged_catalog.assert_valid()
    exit(0)
