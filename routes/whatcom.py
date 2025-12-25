'''
Constants and implementations of package interfaces for Whatcom Transportation Authority.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

AGENCY = 'Whatcom Transportation Authority'
MAIN_URL = 'schedules.ridewta.com/data/wta-static-gtfs/routes.txt'
ROUTE_PATTERN = re.compile('\n(.*?)(?:,\w*?){3}(?:([^,]+)&)?([^,]+)')
# The schedule always takes a moment to load, unfortunately, at least on some browsers
LINK_BASE = 'https://schedules.ridewta.com/#route-details?routeNum='
# Whatcom Transportation Authority allows no options; navigation is all done through JavaScript

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
            if match.group(1) in self.routelistings:
                rl = self.routelistings[match.group(1)]
            else:
                try:
                    rl = RouteListing(match.group(1))
                except AttributeError:
                    # Raised on Skagit Transit duplicate
                    continue
                self.routelistings[match.group(1)] = rl
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
            rl.links = tuple(LINK_BASE + match.group(1) for x in range(3))

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'whatcom'
        self.number = short_filename
        self.css_class = ''
        super().__init__()

    def position(self):
        if self.number.isnumeric():
            return int(self.number)
        return int(self.number[:-1]) + 0.5

    def displaynum(self):
        if self.number.endswith('S'):
            return '<p class="mediumnum">%s</p>' % self.number
        return self.number
