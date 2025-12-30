'''
Constants and implementations of package interfaces for Everett Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

AGENCY = 'Everett Transit'
MAIN_URL = 'everetttransit.org/101/Schedules'
ROUTE_PATTERN = re.compile(r'<a href="([^"]+)".*?>Route (\d+)<\/a>'\
    + r'(?:(?:<span.*?<\/span>)|(?:: ))([\w\s&;]*) &mdash; ([\w\s&;]*)<\/li>')
LINK_OPTIONS = ('#page=1', '#page=2', '#page=2')

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
            rl = self.get_add_routelisting(match.group(2))
            rl.existence = 1
            rl.start = match.group(3)
            rl.dest = match.group(4)
            rl.set_links(match.group(1), LINK_OPTIONS)

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'everett'
        self.number = short_filename
        self.css_class = ''
        super().__init__()
