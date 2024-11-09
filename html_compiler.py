'''
This program is used to generate an HTML file to display completed buses.
Unfortunately, an HTML file with embedded JavaScript will not work for this;
file modification dates for photographs (lost when uploading to webhosting or
GitHub) are needed to render the page.
However, this progam is not standalone; it requires aforementioned photographs
(when they exist) to be inside a "./images" folder in the current working
directory.
Also, the HTML file produced ("index.html") is designed to accompany an
"index.css" file and a "icon.ico" file, also intended to be in the current
working directory.
This allows each type of route to have its own color scheme, among other things.
'''

import os
import re
import urllib.request
from datetime import datetime
import time

# Current King County Metro URL, may be subject to change in the future
JS_KCM_URL = 'https://cdn.kingcounty.gov/-/media/king-county/depts/metro/'\
    + 'fe-apps/schedule/09142024/js/find-a-schedule-js.js'\
    + '?rev=b74ceeb7db85476cb2f92719c10e956f'
JS_KCM_TRIM = (
    '<option value="" selected="">Enter route or location</option>\\n    ',
    '\\n  </select>\\n\\x3c!-- end route selector --')
HTML_TROLLEY_URL = 'https://metro.kingcounty.gov/up/rr/m-trolley.html'
# This Sound Transit page's formatting is absolutely horrible and inconsistent,
# but it's seemingly the best resource there is
HTML_ST_URL = 'https://www.soundtransit.org/ride-with-us/schedules-maps'
HTML_ST_TRIM = (
    '<p>To print or download individual route schedules and maps click the '\
    + 'PDF.</p><ul><li>',
    '</li></ul></div>')

TIME_FORMAT = '%-m/%-d/%y %-H:%M'

IMG_PATH = 'images'

FINAL_HTML = '''
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <link href="index.css" rel="stylesheet" type="text/css"/>
        <link rel="icon" href="icon.ico">
        <title>Completed Buses</title>
    </head>
    <body>
        <h1>Completed Buses</h1>
        %s
        <table>%s
        </table>
        <p>%s<br>%s<br>%s</p>
    </body>
</html>'''
ROW_HTML = '\n%s<tr>%s</tr>' % (' ' * 12, '%s' * 6)
# The following are for clickable <td> sections opening new tabs
IMG_LINK = IMG_PATH + '/%s'
IMG_HTML = '<img src="%s" alt="%s" title="%s" width=100></img>'
KCM_ROUTE_LINK = 'https://kingcounty.gov/en/dept/metro/routes-and-service/'\
    + 'schedules-and-maps/%s.html#%s'
KCM_ROUTE_OPTIONS = ('route-map', 'weekday', 'weekday-b')
ST_ROUTE_LINK = 'https://www.soundtransit.org/ride-with-us/routes-schedules/%s%s'
ST_ROUTE_OPTIONS = ('', '?direction=0', '?direction=1')

NOTES = (
    'Only current King County Metro and Sound Transit routes are included'\
    + ' (not <a href="https://kingcounty.gov/en/dept/metro/routes-and-service/'\
    + 'service-change">suspended routes</a>).',
    'Routes with <span class="discontinued">Discontinued</span> tag have been'\
    + ' discontinued since their completion.',
    'Routes with <span class="delisted">Delisted</span> tag remain operational'\
    + ' but are absent from public transit agency websites (possibly'\
    + ' intentionally).')

'''
This class allows for easier management of table rows and their associated data
and images.
'''
class RouteListing:
    def __init__(self, number, agency):
        '''
        Sets up self from number and agency strings, This constructor is only
        called directly from image-only setup. self.nonexistence is not set
        here but by child class or by image setup.
        '''
        self.number = number
        self.agency = agency
        if self.number.isnumeric():
            num = int(self.number)
            if not hasattr(self, 'css_class'):
                self.css_class = agency + str(num // 100)
            # Here begin a bunch of edge cases
            if agency == 'X':
                self.css_class = 'nonbus'
            if self.css_class == 'C4':
                self.css_class = 'C9'
            elif self.css_class == 'C5':
                raise AttributeError    # These routes shown by ST and CT both
            elif self.css_class == 'K0' and num in range(90, 100):
                self.css_class = 'special'
        else:
            if 'DART' in self.number:
                self.css_class = 'K7'
            else:
                self.css_class = {'K': 'rapidride', 'C': 'swift'}[self.agency]
        self.start = ''
        self.finish = ''
    def position(self):
        '''
        Returns position in ordering on website, sensitive to order of transit
        agencies and special route status.
        '''
        basenum = 'KSCX'.index(self.agency) * 2000
        if not self.number.isnumeric():
            if 'DART' in self.number:
                return basenum + int(self.number.lstrip('DART'))
            return basenum - 256 + ord(self.number[0])
        return basenum + int(self.number)
    def __lt__(self, other):
        '''
        Returns whether self is less than RouteListing other, for purposes of
        comparison.
        '''
        return self.position() < other.position()
    def __str__(self):
        '''Returns string representation of self, for debugging purposes.'''
        return self.number.ljust(4) + self.css_class + ' ' + self.start\
            + ' ⬌ ' + self.finish
    def link(self, param):
        '''Adds the correct HTML link to string text, with param in URL.'''
        if self.nonexistence:
            return ''
        if self.agency == 'S':
            return ST_ROUTE_LINK % (self.number, param)
        elif self.css_class == 'rapidride':
            return KCM_ROUTE_LINK % (self.number + '-line', param)
        else:
            return KCM_ROUTE_LINK % (self.number.zfill(3), param)
    def to_html(self):
        '''
        Returns this row's <tr> HTML element for the final table.
        This isn't the most elegant way to handle CSS classes when writing HTML
        by hand, but it is more simple when generating it.
        '''
        note = ('none', '')
        if self.nonexistence == 1:
            note = ('discontinued', 'Discontinued')
        elif self.nonexistence == 2:
            note = ('delisted', 'Delisted')
        if self.img:
            i_link = IMG_LINK % self.img
            i_td = td(
                'none',
                IMG_HTML % (i_link, self.number, self.number),
                i_link,
                False)
        else:
            i_td = td('none', '')
        params = {'K': KCM_ROUTE_OPTIONS, 'S': ST_ROUTE_OPTIONS}[self.agency]
        display_num = self.number
        if 'DART' in display_num:
            display_num = '<p class="dart">DART</p>' + display_num.lstrip('DART')
        return ROW_HTML % (
            td('b-' + self.css_class, display_num, self.link(params[0])),
            td('n-' + self.css_class, self.start, self.link(params[1])),
            td('n-' + self.css_class, self.finish, self.link(params[2])),
            td(*note),
            td('complete' if self.img else 'incomplete', self.datetime),
            i_td)

'''
This class extends RouteListing to automatically perform setup based on website
data, calls RouteListing constructor after custom setup.
'''
class WebRouteListing(RouteListing):
    def __init__(self, string, pattern, delimiter, agency):
        '''
        Sets up self from route listing string string, using re.Pattern pattern
        and string delimiter. Nonexistence flag is for main function to modify.
        '''
        string = string.replace('&amp;', '&').replace('–', '-').replace('\\', '')
        match = pattern.fullmatch(string)
        if not match:
            raise AttributeError
        self.number, path = match.group(1), match.group(2)
        self.is_dart = False
        if 'Line' in self.number:
            self.number = self.number[0]
        elif 'DART' in self.number:
            # Note that 775 is not DART but needs DART palette, so this is a fix
            self.css_class = 'K7'
            self.number = self.number.replace(' ', '')
        elif 'Shuttle' in self.number:
            self.number = self.number.rstrip(' Shuttle')
        elif not self.number.isnumeric():
            raise AttributeError        # Do not include Water Taxi, etc. here
        super().__init__(self.number, agency)
        self.set_terminals(path, delimiter)
        self.nonexistence = 0           # This is true for all WebRouteListings
    def set_terminals(self, path, delimiter):
        '''
        Called from constructor, sets self.start and self.finish given string
        path (list of destinations, separated by string delimiter).
        '''
        match = re.match('Service between (.*) and (the | )(.*)', path)
        if match:                       # Catches King County edge case
            self.start, self.finish = match.group(1), match.group(3)
        else:
            destinations = path.split(delimiter)
            if destinations[0].startswith('Serves'):
                del destinations[0]
                self.css_class = 'schools'
                if 'School' in destinations[0]:
                    del destinations[0] # Catches King County edge case
            self.start = destinations[0].lstrip().rstrip()
            self.finish = destinations[-1].lstrip().rstrip()
    def find_image(self, images):
        '''
        Sets self.img and self.datetime by checking images
        parameter for existence and local filesystem for stats.
        '''
        self.img = self.agency + self.number + '.jpg'
        if self.img in images:
            secs = os.stat(os.path.join(IMG_PATH, self.img)).st_birthtime
            self.datetime = datetime.fromtimestamp(secs).strftime(TIME_FORMAT)
            images.remove(self.img)
        else:
            self.img = None
            self.datetime = 'Incomplete'

def fetch_file(url):
    '''Given string url, returns contents of file fetched from it in UTF-8.'''
    r = urllib.request.Request(url, headers={'User-Agent': 'Magic Browser'})
    with urllib.request.urlopen(r) as file:
        return file.read().decode('utf8')

def td(css_class, data, link=None, blank=True):
    '''
    Returns <td> HTML element given css_class, text/image data, and link.
    If link should open in same tab, blank should be False.
    '''
    if not link:
        return '<td class="%s">%s</td>' % (css_class, data)
    if blank:
        jsfunc = 'window.open(\'%s\', \'_blank\')' % link
    else:
        jsfunc = 'window.open(\'%s\', \'_self\')' % link
    return '<td class="%s" onclick="%s">%s</td>' % (css_class, jsfunc, data)

def completenessHTML(route_listings):
    '''
    Given all route listings, returns regular Percentage Completeness heading
    if it's less than 100%, but returns Qualified Completeness heading when
    all non-snow-shuttle routes are complete, and returns Full Completeness
    heading when all routes are complete, with no exceptions.
    '''
    dt = datetime.fromtimestamp(time.time()).strftime('%-m/%-d/%y')
    total = 0
    completed = 0
    can_fc = True
    for rl in route_listings:
        if not rl.img:
            can_fc = False
        if rl.css_class != 'special' and not rl.nonexistence:
            total += 1
            completed += 1 if rl.img else 0
    if can_fc:
        return '<h2>Fully Complete on %s</h2>' % dt
    if completed == total:
        return '''<h2>Fully Complete* on %s</h2>
            <h3>*Excluding Unavailable Snow Shuttle</h3>''' % dt
    return '<h2>%d%% Complete, Updated %s</h2>' % (completed * 100 // total, dt)
    
def main():
    '''
    Entry point of program.
    Gathers images that must be used, scrapes buses from both the Metro and
    Sound Transit websites, creates route table.
    '''
    in_angles = re.compile('<.*?>')
    route_listings = []
    images = set()
    for x in os.listdir(IMG_PATH):
        if x.endswith('.jpg'):
            images.add(x)

    js_metro = fetch_file(JS_KCM_URL)
    scan = js_metro.partition(JS_KCM_TRIM[0])[2].partition(JS_KCM_TRIM[1])[0]
    options = [in_angles.sub('', x) for x in scan.split('\\n    ')]
    html_trolley = fetch_file(HTML_TROLLEY_URL)
    pattern = re.compile('(.*) - (.*)')
    for o in options:
        try:
            rl = WebRouteListing(o, pattern, ',', 'K')
            rl.find_image(images)
            if 'Route ' + rl.number in html_trolley:
                rl.css_class = 'trolley'
            route_listings.append(rl)
        except AttributeError:
            continue

    html_st = fetch_file(HTML_ST_URL)
    scan = html_st.partition(HTML_ST_TRIM[0])[2].partition(HTML_ST_TRIM[1])[0]
    options = [in_angles.sub('', x) for x in scan.split('</li><li>')]
    pattern = re.compile('(\\d*)\\s\\((.*)\\).*\\n?')
    for o in options:
        try:
            rl = WebRouteListing(o, pattern, '- ', 'S')
            rl.find_image(images)
            route_listings.append(rl)
        except AttributeError:
            continue

    # All remaining images are '*#.jpg' (delisted) or '#.jpg' (discontinued)
    while len(images):
        i = images.pop()
        temp = i.rstrip('.jpg').lstrip('*')
        rl = RouteListing(temp[1:], temp[0])
        rl.nonexistence = i.startswith('*') + 1
        if rl.agency == 'X' and rl.nonexistence == 1:
            rl.nonexistence = 0
        rl.img = i
        if rl.css_class in ('K8', 'K9'):
            rl.css_class = 'schools'    # Cannot check for "Serves" if absent
        secs = os.stat(os.path.join(IMG_PATH, i)).st_birthtime
        rl.datetime = datetime.fromtimestamp(secs).strftime(TIME_FORMAT)
        if 'Route ' + rl.number in html_trolley:
            rl.css_class = 'trolley'
        route_listings.append(rl)

    route_listings.sort()
    fp = open('index.html', 'w')
    fp.write(FINAL_HTML % (
        completenessHTML(route_listings),
        ''.join([rl.to_html() for rl in route_listings]),
        *NOTES))
    fp.close()

if __name__ == '__main__':
    main()
