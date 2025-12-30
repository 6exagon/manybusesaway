'''
Constants and implementations of package interfaces for Whatcom Transportation Authority.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

AGENCY = 'Whatcom Transportation Authority'
MAIN_URL = 'schedules.ridewta.com/data/wta-static-gtfs/routes.txt'
ROUTE_PATTERN = re.compile('\n(.*?)(?:,\w*?){3}(?:([^,]+)&)?([^,]+)')
# The schedule takes time to load, at least on some browsers
LINK_BASE = 'https://schedules.ridewta.com/#route-details?routeNum='
# Allows no options; navigation is all done through JavaScript

class DataParser(DataParserInterface):
    def get_agency_fullname(self):
        return AGENCY

    def get_route_listing_class(self):
        return RouteListing

    def get_initial_requests(self):
        return {MAIN_URL}

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

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'whatcom'
        self.number = short_filename
        self.css_class = ''
        super().__init__()

    def displaynum(self):
        if self.number.endswith('S'):
            return '<p class="mediumnum">%s</p>' % self.number
        return self.number
