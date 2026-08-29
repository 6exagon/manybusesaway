'''
Constants and implementations of package interfaces for Everett Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

MAIN_URL = 'everetttransit.org/101/Schedules'
ROUTE_PATTERN = re.compile(r'<a href="([^"]+)".*?>Route (\d+)<\/a><\/h2><p.*?>'\
    + r'<strong.*?>([\w\s&;]*) &mdash; ([\w\s&;]*)')
# Allows no options; we let the user click the PDF link on their own

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
            rl.isdelisted = False
            rl.start = match.group(3)
            rl.dest = match.group(4)
            rl.set_links(match.group(1))
