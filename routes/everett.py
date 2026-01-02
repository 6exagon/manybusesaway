'''
Constants and implementations of package interfaces for Everett Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

MAIN_URL = 'everetttransit.org/101/Schedules'
ROUTE_PATTERN = re.compile(r'<a href="([^"]+)".*?>Route (\d+)<\/a>'\
    + r'(?:(?:<span.*?<\/span>)|(?:: ))([\w\s&;]*) &mdash; ([\w\s&;]*)<\/li>')
LINK_OPTIONS = ('#page=1', '#page=2', '#page=2')

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        self.number = short_filename
        self.css_class = ''
        super().__init__()

class DataParser(DataParserInterface):
    AGENCY_FULL_NAME = 'Everett Transit'
    ROUTELISTING = RouteListing
    INITIAL_REQUESTS = {MAIN_URL}

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
