'''
Constants and implementations of package interfaces for Community Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

AGENCY = 'Community Transit'
MAIN_URL = 'www.communitytransit.org/maps-and-schedules/'\
    + 'maps-and-schedules-by-route'
ROUTE_PATTERN = re.compile(
    '"route_id":"(\d{3})","route_name":"([^"]*) \| ([^"]*)","route_short_name"')
LINK_BASE = 'https://www.communitytransit.org/route/%s%s'
LINK_OPTIONS = ('', '/table', '/0/table')

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
                    # Raised on SoundTransit duplicate
                    continue
                self.routelistings[match.group(1)] = rl
            rl.existence = 1
            rl.start = match.group(2)
            rl.dest = match.group(3)
            rl.set_links(LINK_BASE, match.group(1), LINK_OPTIONS)

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'community'
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
