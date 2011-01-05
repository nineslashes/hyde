# -*- coding: utf-8 -*-
"""
Implements the hyde entry point commands
"""
from commando import *
from hyde.exceptions import HydeException
from hyde.fs import File, Folder
from hyde.layout import Layout, HYDE_DATA
from hyde.model import Config
from hyde.site import Site
from hyde.version import __version__

import logging
import os
import yaml

HYDE_LAYOUTS = "HYDE_LAYOUTS"

logger = logging.getLogger('hyde.engine')
logger.setLevel(logging.DEBUG)

import sys
logger.addHandler(logging.StreamHandler(sys.stdout))


class Engine(Application):
    """
    The Hyde Application
    """

    @command(description='hyde - a python static website generator',
        epilog='Use %(prog)s {command} -h to get help on individual commands')
    @version('-v', '--version', version='%(prog)s ' + __version__)
    @store('-s', '--sitepath', default='.', help="Location of the hyde site")
    def main(self, args):
        """
        Will not be executed. A sub command is required. This function exists
        to provide common parameters for the subcommands and some generic stuff
        like version and metadata
        """
        pass

    @subcommand('create', help='Create a new hyde site')
    @store('-l', '--layout', default='basic', help='Layout for the new site')
    @true('-f', '--force', default=False, dest='overwrite',
                            help='Overwrite the current site if it exists')
    def create(self, args):
        """
        The create command. Creates a new site from the template at the given
        sitepath.
        """
        sitepath = Folder(Folder(args.sitepath).fully_expanded_path)
        if sitepath.exists and not args.overwrite:
            raise HydeException(
                    "The given site path[%s] is not empty" % sitepath)
        layout = Layout.find_layout(args.layout)
        logger.info(
            "Creating site at [%s] with layout [%s]" % (sitepath, layout))
        if not layout or not layout.exists:
            raise HydeException(
            "The given layout is invalid. Please check if you have the"
            " `layout` in the right place and the environment variable(%s)"
            " has been setup properly if you are using custom path for"
            " layouts" % HYDE_DATA)
        layout.copy_contents_to(args.sitepath)
        logger.info("Site creation complete")

    @subcommand('gen', help='Generate the site')
    @store('-c', '--config-path', default='site.yaml', dest='config',
            help='The configuration used to generate the site')
    @store('-d', '--deploy-path', default='deploy',
                                help='Where should the site be generated?')
    def gen(self, args):
        """
        The generate command. Generates the site at the given
        deployment directory.
        """
        site = self.make_site(args.sitepath, args.config)
        from hyde.generator import Generator
        gen = Generator(site)
        gen.generate_all()

    @subcommand('serve', help='Serve the website')
    @store('-a', '--address', default='localhost', dest='address',
            help='The address where the website must be served from.')
    @store('-p', '--port', type=int, default=8080, dest='port',
            help='The port where the website must be served from.')
    @store('-c', '--config-path', default='site.yaml', dest='config',
            help='The configuration used to generate the site')
    @store('-d', '--deploy-path', default='deploy',
                                help='Where should the site be generated?')
    def serve(self, args):
        """
        The serve command. Serves the site at the given
        deployment directory, address and port. Regenerates
        the entire site or specific files based on ths request.
        """
        sitepath = Folder(Folder(args.sitepath).fully_expanded_path)
        config_file = sitepath.child(args.config)
        site = self.make_site(args.sitepath, args.config)
        from hyde.server import HydeWebServer
        server = HydeWebServer(site, args.address, args.port)
        server.serve_forever()

    def make_site(self, sitepath, config):
        """
        Creates a site object from the given sitepath and the config file.
        """
        sitepath = Folder(Folder(sitepath).fully_expanded_path)
        config_file = sitepath.child(config)
        logger.info("Reading site configuration from [%s]", config_file)
        conf = {}
        with open(config_file) as stream:
            conf = yaml.load(stream)
        return Site(sitepath, Config(sitepath, conf))