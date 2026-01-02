'''
Constants and implementations of package interfaces for Central Transit.
See __init__.py for documentation.
'''

from json import loads
import re

from . import DataParserInterface, RouteListingInterface

MAIN_URL = 'gtfs-api.trilliumtransit.com/gtfs-api/routes/by-feed/ellensburg-wa-us'
PATH_PATTERN = re.compile(r'(.+?)(?: \(\w+\))? to (.+?)(?: \(\w+\))?(?: via .+)?')
# Allows no options; navigation is all done through JavaScript

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        self.number = short_filename
        self.css_class = ''
        super().__init__()

class DataParser(DataParserInterface):
    AGENCY_FULL_NAME = 'Central Transit'
    ROUTELISTING = RouteListing
    INITIAL_REQUESTS = {MAIN_URL}

    def update(self, resources):
        json = resources[MAIN_URL]
        if not json:
            return
        json_list = loads(json)
        for i in json_list:
            rl = self.get_add_routelisting(i['route_short_name'])
            rl.existence = 1
            match = PATH_PATTERN.fullmatch(i['route_long_name'])
            rl.start = match.group(1)
            rl.dest = match.group(2)
            rl.set_links(i['route_url'])
