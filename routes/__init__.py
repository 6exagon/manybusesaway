'''
Interfaces for the package that agencies can subclass.
This allows each agency to be handled mostly the same way, rather than having
tons of hardcoded exceptions and idiosyncrasies all over the place.
'''

from abc import ABC, abstractmethod
from json import dumps
import os
import re
from datetime import datetime

# These two constants are imported for Pierce Transit routes
# Though they could be, they're not used for other agencies
# This is because they're less accurate and well-maintained as a source
# For better portability, they should remain here
TP_REQ = ('tripplanner.kingcounty.gov/TI_FixedRoute_Line', dumps(
    {'version': '1.1', 'method': 'GetLines'}))
TP_PATTERN = re.compile(r'.*(?:[Tt]o|-) (?:.*?\/ )*?([^\/]*?)(?: via .*)?')
# This will allow all widely-supported raster image formats while disallowing
# most other files incidentally present
SHORT_FILENAME_PATTERN = re.compile(r'\*?([\w\d]*)\.[abefgijnpvw]+')
TIME_FORMAT = '%-m/%-d/%y %-H:%M'
# This is for RouteListings to export their own HTML, in to_html()
# More notes may be needed in the future
EXISTENCE_NOTES = (
    ('Discontinued', 'discontinued'), ('',), ('Delisted', 'delisted'))
TABLE_HTML = '    <h3>%s</h3>\n    <table>\n%s\n    </table>'
ROW_HTML = '%s<tr>%s</tr>' % (' ' * 6, '%s' * 6)
IMG_HTML = '<img src="%s" alt="%s" title="%s" width=100></img>'
CSS_SPECIAL = 'x'

class DataParserInterface(ABC):
    '''
    Handles the gathering of data for each particular agency implementing it.
    Creates and manages RouteListings.
    '''
    def __init__(self, agency, verbose, image_dir=None):
        '''
        Initializes attributes and RouteListings of self.
        Parameter string image_dir will be the directory in which this agency's
        image files will be found.
        '''
        self.agency = agency
        # This is useful in to_html() and agency-specific requests
        self.verbose = verbose
        # We need this for generating HTML
        if image_dir:
            self.image_dir = os.path.join(image_dir, agency)
            self.images = os.listdir(self.image_dir)
        else:
            self.image_dir = None
            self.images = []
        # Dictionary will have numbers (agency-specific) as keys, and
        # RouteListings as values
        self.routelistings = dict()
        for i in self.images:
            match = SHORT_FILENAME_PATTERN.match(i)
            try:
                # Get the RouteListing class (agency-specific), and instantiate
                rl = self.get_route_listing_class()(match.group(1))
                if i.startswith('*'):
                    rl.existence = 2
                rl.img = os.path.join(self.image_dir, i)
                secs = os.stat(rl.img).st_birthtime
                rl.datetime = datetime.fromtimestamp(secs).strftime(TIME_FORMAT)
                self.routelistings[rl.number] = rl
            # This can fail because match is None, or AttributeError is raised
            # by rl.__init__
            except AttributeError:
                continue

    @abstractmethod
    def get_agency_fullname(self):
        '''
        This method returns the full name of the agency implementing this
        interface, to be rendered in the final HTML.
        '''
        pass

    @abstractmethod
    def get_route_listing_class(self):
        '''
        This method returns the RouteListing class specific to the agency
        implementing this interface. This is needed so this interface code can
        instantiate them properly.
        '''
        pass

    @abstractmethod
    def get_initial_requests(self):
        '''
        This method returns a set whose contents are either strings (URIs
        preceded by DNS names, i.e. website URLs) for GET requests, or tuples
        containing a string URL and a request body for POST requests.
        These are provided to http.client.HTTPSConnection.request,
        though an invariant headers field is added.
        After this first step is handled by main program (because some
        agencies might share resources), DataParsers are free to request
        resources on their own.
        '''
        pass

    @abstractmethod
    def update(self, resources):
        '''
        This function takes a dictionary whose keys are either strings (URIs
        preceded by DNS names, i.e. website URLs) for GET requests, or tuples
        containing a string URL and a request body for POST requests, and whose
        values are what is returned by the server.
        Internal RouteListings are updated using the contents of these.
        DataParsers may request resources on their own in this function.
        '''
        pass

    def sanitize_strings(self):
        '''
        Independently of agency-specific code, makes known string fixes to
        RouteListings.
        '''
        for rl in self.routelistings.values():
            rl.sanitize_strings()

    def completed(self):
        '''
        Returns two integers: the number of total existing routes in
        self.routelistings, and the number of those which are completed.
        '''
        total = 0
        completed = 0
        for rl in self.routelistings.values():
            if rl.existence:
                total += 1
                if rl.img:
                    completed += 1
        return total, completed

    def to_html(self):
        '''
        Returns HTML generated by this DataParser, which will be composed of
        a header and a table made of HTML rows generated by RouteListings in
        self.routelistings.
        If self.verbose is True, prints messages to stdout.
        '''
        if self.verbose:
            print('Sorting %s listings...' % self.agency, end='', flush=True)
        listings = sorted(self.routelistings.values())
        if self.verbose:
            print('Done')
            for l in listings:
                print(l)
        rows = '\n'.join(l.to_html() for l in listings)
        return TABLE_HTML % (self.get_agency_fullname(), rows)

class RouteListingInterface(ABC):
    '''
    Classes implementing this interface allows for easier management of
    table rows and their associated data and images.
    '''
    @abstractmethod
    def __init__(self, short_filename=None):
        '''
        Initializes self from most of an image's filename (just not the leading
        * or file extension), a process which might differ depending on the
        agency. Does not initialize all attributes to proper values yet.
        Raises AttributeError on failure; object should not be used after this.
        self.agency, self.number, and self.css_class (at least) must be set by
        overriding method.
        '''
        self.position = self.position()
        # These attributes are all default values, set later on if applicable
        self.start = ''
        self.dest = ''
        self.links = (None, None, None)
        # Python doesn't have C-style enums, so 0 = discontinued, 1 = normal,
        # 2 = delisted
        if not hasattr(self, 'existence'):
            self.existence = 0
        self.datetime = 'Incomplete'
        self.img = None

    def __str__(self):
        '''Returns string representation of self, for debugging or -v.'''
        return ' '.join((
            'i–'[not self.img] + '! *'[self.existence],
            self.agency,
            self.number,
            '(' + self.css_class + ')',
            self.start,
            '⬌',
            self.dest))

    def __lt__(self, other):
        '''
        Returns whether self is less than RouteListing other, for purposes of
        comparison. Only valid within this agency.
        '''
        return self.position < other.position

    def position(self):
        '''
        Sets position value relative to other RouteListings from this agency.
        This is used for comparisons. Default may be commonly used, but if any
        route for this agency has an unusual name, it will need overriding.
        In particular, if an agency uses only route numbers in the form of
        \d*\w, or if portions after the first letter in alphabetical numbers
        need not be discriminated, this method will suffice.
        '''
        if self.number.isnumeric():
            return int(self.number)
        numerical_part_maybe = self.number[:-1]
        # ''.isnumeric() is False
        if numerical_part_maybe.isnumeric():
            # This allows '10' < '10N' < '10S' for example
            return int(numerical_part_maybe) + ord(self.number[-1]) / 256
        # This allows 'A' < 'B' < '1'
        return ord(self.number[0]) - 256

    def set_links(self, linkbase, linkpiece, linkoptions):
        '''
        Sets tuple self.links to string linkbase formatted with string linkpiece
        and each of the strings in tuple linkoptions.
        This allows each td in this RouteListing's tr to have a different but
        related link.
        '''
        self.links = tuple(linkbase % (linkpiece, o) for o in linkoptions)

    def sanitize_strings(self):
        '''Sanitizes self.start and self.dest to fix known inconsistencies.'''
        # The rstrip is just in case, but it should be covered previously
        self.start = self.start.replace('\\', '').replace('amp;', '').rstrip()
        self.dest = self.dest.replace('\\', '').replace('amp;', '').rstrip()

    def to_html(self):
        '''
        Returns this row's <tr> HTML element for the final table.
        Handles special cases for visuals.
        Sanitizes self.start and self.dest "P&R" cases to output correct
        HTML ampersands in HTML.
        '''
        if self.img:
            # This needs to output correct "/" HTML on Windows as well
            i_link = self.img.replace(os.path.sep, '/')
            i_td = td(
                IMG_HTML % (i_link, self.number, self.number),
                link=i_link,
                blank=False)
        else:
            i_td = td('')
        # Most CSS classes are agency-specific, there's only one that isn't
        if self.css_class == CSS_SPECIAL:
            final_class = CSS_SPECIAL
        else:
            final_class = self.agency + '-' + self.css_class
        displaystart = self.start.replace('&', '&amp;')
        if len(self.dest):
            displaydest = self.dest.replace('&', '&amp;')
            start_td = td(displaystart, 'n-' + final_class, link=self.links[1])
            dest_td = td(displaydest, 'n-' + final_class, link=self.links[2])
        else:
            start_td = td(
                displaystart, 'n-' + final_class, link=self.links[1], span=True)
            # There is no destination, so this is what will be substituted in
            dest_td = ''
        return ROW_HTML % (
            td(self.displaynum(), 'b-' + final_class, link=self.links[0]),
            start_td,
            dest_td,
            td(*EXISTENCE_NOTES[self.existence]),
            td(self.datetime, 'complete' if self.img else 'incomplete'),
            i_td)

    def displaynum(self):
        '''
        Returns this RouteListing's HTML number, which could be the simple
        number in plaintext or contain more complicated HTML.
        This will almost always be overridden.
        '''
        return self.number

def td(data, css_class=None, **kwargs):
    '''
    Returns <td> HTML element given text/image data and specific parameters
    related to its HTML attributes.
    If td should have a CSS class, string css_class should be set to that.
    If td should link to something, string link should be set to the location
    (and if link should open in same tab, bool blank should be False).
    If td should span an extra column, bool span should be True.
    '''
    td_elem = ['td']
    if css_class:
        td_elem.append('class="%s"' % css_class)
    if kwargs.get('link', None):
        behavior = '_blank' if kwargs.get('blank', True) else '_self'
        td_elem.append(
            'onclick="window.open(\'%s\', \'%s\')"' % (kwargs['link'], behavior))
    if kwargs.get('span', False):
        td_elem.append('colspan="2"')
    return '<%s>%s</td>' % (' '.join(td_elem), data)
