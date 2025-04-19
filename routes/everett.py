'''
Constants and implementations of package interfaces for Everett Transit.
See __init__.py for documentation.
'''

from json import loads
import re

from . import DataParserInterface, RouteListingInterface, TP_REQ, TP_PATTERN

# Used only for the schedule links, inadequate for route descriptions
MAIN_URL = 'everetttransit.org/101/Schedules'
ROUTE_PATTERN = re.compile(r'<a href="([^"]+)".*>Route (\d+)<\/span><\/a>')
LINK_BASE = '%s#page=%s'
LINK_OPTIONS = ('1', '2', '2')

class DataParser(DataParserInterface):
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
            if i['agencyId'] == 'ET':
                rlid = i['lineAbbr'][2:]
                tp_lines_dict[rlid] = (x['signage'] for x in i['directions'])

        for match in re.finditer(ROUTE_PATTERN, html):
            if match.group(2) in self.routelistings:
                rl = self.routelistings[match.group(2)]
            else:
                rl = RouteListing(match.group(2))
                self.routelistings[match.group(2)] = rl
            rl.existence = 1
            dirgen = tp_lines_dict.pop(match.group(2))
            rl.start, rl.dest = (
                TP_PATTERN.fullmatch(s).group(1) for s in dirgen)
            # This error must be patched; again, Trip Planner data isn't great
            if rl.number == '6':
                rl.start = 'Waterfront'
            rl.set_links(LINK_BASE, match.group(1), LINK_OPTIONS)

class RouteListing(RouteListingInterface):
    def __init__(self, short_filename):
        # This could be gotten from higher up, but this is a sanity check
        self.agency = 'everett'
        self.number = short_filename
        self.css_class = ''
        super().__init__()
