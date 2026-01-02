'''
Constants and implementations of package interfaces for Pacific Transit.
See __init__.py for documentation.
'''

import re

from . import DataParserInterface, RouteListingInterface

MAIN_URL = 'pacifictransit.org/route-schedule/'
ROUTE_PATTERN = re.compile(
    r'--route-color:(#\w+)"><summary>(\w+) - ([\w ]+)[\w \/]+?([\w ]+) - ')
LINK_BASE = 'https://pacifictransit.org/%s-line/'
# Allows no options; navigation is all done through JavaScript

class RouteListing(RouteListingInterface):
    # This could be gotten from higher up, but this is a sanity check
    AGENCY = 'pacific'

    def __init__(self, short_filename):
        self.number = short_filename
        self.css_class = ''
        self.color = 'white'
        super().__init__()

    def position(self):
        # Lexicographic ordering is used on website, which is desirable here
        return self.number

    def displaynum(self):
        # Inline style is probably the best here
        return '<p class="smallnum" style="color:%s">%s</p>' % (
            self.color, self.number)

class DataParser(DataParserInterface):
    AGENCY_FULL_NAME = 'Pacific Transit'
    ROUTELISTING = RouteListing
    INITIAL_REQUESTS = {MAIN_URL}

    def update(self, resources):
        html = resources[MAIN_URL]
        if not html:
            return
        for match in ROUTE_PATTERN.finditer(html):
            # Because the HTML contains two copies of each for some reason,
            # we set properties multiple times, which is actually okay here
            rl = self.get_add_routelisting(match.group(2))
            rl.existence = 1
            rl.start = match.group(3)
            rl.dest = match.group(4)
            rl.color = match.group(1)
            rl.set_links(LINK_BASE % rl.number)
