'''
Constants and implementations of package interfaces for Whatcom Transportation Authority.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

MAIN_URL = 'schedules.ridewta.com/data/wta-static-gtfs/routes.txt'
ROUTE_PATTERN = re.compile('\n(.*?)(?:,\w*?){3}(?:([^,]+)&)?([^,]+)')
# The schedule takes time to load, at least on some browsers
LINK_BASE = 'https://schedules.ridewta.com/#route-details?routeNum='
# Allows no options; navigation is all done through JavaScript

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        self.number = short_filename
        self.css_class = ''
        super().__init__()

    def displaynum(self):
        if self.number.endswith('S'):
            return '<p class="mediumnum">%s</p>' % self.number
        return self.number

class DataParser(DataParserInterface):
    AGENCY_FULL_NAME = 'Whatcom Transportation Authority'
    ROUTELISTING = RouteListing
    INITIAL_REQUESTS = {MAIN_URL}

    def update(self, resources):
        html = resources[MAIN_URL]
        if not html:
            return
        for match in ROUTE_PATTERN.finditer(html):
            rl = self.get_add_routelisting(match.group(1))
            rl.existence = 1
            if match.group(2):
                rl.start = match.group(2)
                rl.dest = match.group(3)
            else:
                try:
                    rl.start, rl.dest = match.group(3).split('/')
                except ValueError:
                    # Only one terminus is the best we can do for some
                    rl.start = match.group(3)
            rl.set_links(LINK_BASE + match.group(1))
