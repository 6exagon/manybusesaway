'''
Constants and implementations of package interfaces for Pierce Transit.
See __init__.py for documentation.
'''

from json import loads
import re

from . import DataParserInterface, RouteListingInterface, TP_REQ, TP_PATTERN, CSS_SPECIAL

AGENCY = 'Pierce Transit'
# Used only for the schedule links, inadequate for route descriptions
MAIN_URL = 'piercetransit.org/pierce-transit-routes/'
ROUTE_PATTERN = re.compile(
    r'<a href="([^"]+)">(?:Route )?(Stream|\d+) ([^<]*)<\/a><\/div>')
# Pierce Transit allows no options; navigation is all done through JavaScript
# Gig Harbor Trolley should be special
SPECIAL_ROUTES = ('101',)

class DataParser(DataParserInterface):
    def get_agency_fullname(self):
        return AGENCY

    def get_route_listing_class(self):
        return RouteListing

    def get_initial_requests(self):
        return {MAIN_URL, TP_REQ}

    def update(self, resources):
        html = resources[MAIN_URL]
        tp_json = resources[TP_REQ]
        if not html or not tp_json:
            return
        tp_lines_list = loads(tp_json)['result']['lines']
        # This stores map of string rlid to generator over destination listings
        tp_lines_dict = dict()
        for i in tp_lines_list:
            if i['agencyId'] == 'PT':
                #i['name'] doesn't work for 497
                dirs = tuple(x['signage'] for x in i['directions'])
                tp_lines_dict[dirs[0].partition(' ')[0]] = dirs

        for match in ROUTE_PATTERN.finditer(html):
            if match.group(2) in self.routelistings:
                rl = self.routelistings[match.group(2)]
            else:
                rl = RouteListing(match.group(2))
                self.routelistings[match.group(2)] = rl
            rl.existence = 1
            try:
                dirgen = tp_lines_dict.pop(match.group(2))
                rl.start, rl.dest = (
                    TP_PATTERN.fullmatch(s).group(1) for s in dirgen)
            except KeyError:
                # Something is in the PT HTML but not the trip planner data, probably 101
                rl.start = match.group(3)
            rl.links = tuple(match.group(1) for x in range(3))

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'pierce'
        self.number = short_filename
        self.css_class = ''
        if self.number in SPECIAL_ROUTES:
            self.css_class = CSS_SPECIAL
        super().__init__()

    def position(self):
        if self.number.isnumeric():
            return int(self.number)
        return 0

    def displaynum(self):
        if self.number.isnumeric():
            return self.number
        return '<p class="smallnum">Stream</p>'
