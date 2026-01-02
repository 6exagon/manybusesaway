'''
Constants and implementations of package interfaces for Community Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

MAIN_URL = 'www.communitytransit.org/maps-and-schedules/'\
    + 'maps-and-schedules-by-route'
ROUTE_PATTERN = re.compile(
    '"route_id":"(\d{3,4})","route_name":"([^"]*) \| ([^"]*)","route_short_name"')
LINK_BASE = 'https://www.communitytransit.org/route/'
LINK_OPTIONS = ('', '/table', '/0/table')

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        if not short_filename.isnumeric():
            raise AttributeError
        self.number = short_filename
        series = int(self.number) // 100
        if series == 5:
            # Some routes shown by ST and CT both, but belong to ST
            raise AttributeError
        elif series == 4:
            series = 9
        self.css_class = str(series)
        super().__init__()

    def displaynum(self):
        if self.css_class == '7':
            return '<p class="community-swift">Swift</p>' + self.number
        return self.number

class DataParser(DataParserInterface):
    AGENCY_FULL_NAME = 'Community Transit'
    ROUTELISTING = RouteListing
    INITIAL_REQUESTS = {MAIN_URL}

    def update(self, resources):
        html = resources[MAIN_URL]
        if not html:
            return
        for match in ROUTE_PATTERN.finditer(html):
            try:
                rl = self.get_add_routelisting(match.group(1))
            except AttributeError:
                # Raised on SoundTransit duplicate
                continue
            rl.existence = 1
            rl.start = match.group(2)
            rl.dest = match.group(3)
            rl.set_links(LINK_BASE + match.group(1), LINK_OPTIONS)
