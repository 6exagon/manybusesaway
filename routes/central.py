'''
Constants and implementations of package interfaces for Central Transit.
See __init__.py for documentation.
'''

from json import loads
import re

from . import DataParserInterface, RouteListingInterface

AGENCY = 'Central Transit'
MAIN_URL = 'gtfs-api.trilliumtransit.com/gtfs-api/routes/by-feed/ellensburg-wa-us'
PATH_PATTERN = re.compile(r'(.+?)(?: \(\w+\))? to (.+?)(?: \(\w+\))?(?: via .+)?')
# Allows no options; navigation is all done through JavaScript

class DataParser(DataParserInterface):
    def get_agency_fullname(self):
        return AGENCY

    def get_route_listing_class(self):
        return RouteListing

    def get_initial_requests(self):
        return {MAIN_URL}

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

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'central'
        self.number = short_filename
        self.css_class = ''
        super().__init__()
