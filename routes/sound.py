'''
Constants and implementations of package interfaces for Sound Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

AGENCY = 'Sound Transit'
# This Sound Transit page's formatting is terrible and inconsistent,
# as seen by the regex, but it's seemingly the best resource there is
MAIN_URL = 'www.soundtransit.org/ride-with-us/schedules-maps'
ROUTE_PATTERN = re.compile(r'<a href="[^"]*?([^"\/]+)"[^>]*>(?:Link |Sounder )?'\
    + r'(\d+|\w)(?: Line)?.\(([\w \/\.]+) \W (?:[^)]* ?\W )?([\w \/\.]+?) ?\)')
LINK_BASE = 'https://www.soundtransit.org/ride-with-us/routes-schedules/%s%s'
LINK_OPTIONS = ('', '?direction=1', '?direction=0')

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
            if match.group(2) in self.routelistings:
                rl = self.routelistings[match.group(2)]
            else:
                rl = RouteListing(match.group(2))
                self.routelistings[match.group(2)] = rl
            rl.existence = 1
            rl.start = match.group(3)
            rl.dest = match.group(4)
            rl.set_links(LINK_BASE, match.group(1), LINK_OPTIONS)

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'sound'
        self.number = short_filename
        if short_filename.isnumeric():
            self.css_class = str(int(self.number) // 100)
        else:
            # Trains have 0 palette
            self.css_class = '0'
        super().__init__()

    def displaynum(self):
        if len(self.number) != 1:
            return self.number
        return '<span class="circle" id="sound-c%s">%s</span>' % (
            self.number, self.number)
