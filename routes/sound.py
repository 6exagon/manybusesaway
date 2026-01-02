'''
Constants and implementations of package interfaces for Sound Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

# This Sound Transit page's formatting is terrible and inconsistent,
# as seen by the regex, but it's seemingly the best resource there is
MAIN_URL = 'www.soundtransit.org/ride-with-us/schedules-maps'
ROUTE_PATTERN = re.compile(
    r'<a href="[^"]*?([^"\/]+)"[^>]*>(?:Link |Sounder )?(\d+|\w)(?: Line)?'\
    + r'.\(([\w \/\.]+) \W (?:[^)]* ?[^\w\.] )?([\w \/\.]+?) ?\)')
LINK_BASE = 'https://www.soundtransit.org/ride-with-us/routes-schedules/'
LINK_OPTIONS = ('', '?direction=1', '?direction=0')

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
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

class DataParser(DataParserInterface):
    AGENCY_FULL_NAME = 'Sound Transit'
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
            rl.set_links(LINK_BASE + match.group(1), LINK_OPTIONS)
