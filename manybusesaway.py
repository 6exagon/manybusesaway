'''
ManyBusesAway v4.1.b3
This program and its accompanying modules are used to generate an HTML file
to display completed buses from several transit agencies.
Unfortunately, an HTML file with embedded JavaScript will not work for this;
file modification dates for photographs (lost when uploading to webhosting or
GitHub) are needed to render the page.
See project README.md for details and LICENSE.txt for license.
'''

import argparse
from importlib import import_module
import re
from datetime import datetime
from time import time
import locale

from requests import request_all

DEFAULT_AGENCIES_ORDER = (
    'king', 'sound', 'everett', 'community', 'pierce', 'intercity', 'kitsap',
    'skagit', 'whatcom', 'lewis', 'pacific', 'grays', 'central')

FINAL_HTML = '''
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <link href="index.css" rel="stylesheet" type="text/css"/>
    <link rel="icon" href="icon.ico">
    <title>ManyBusesAway</title>
  </head>
  <body>
    <h1>Completed Buses</h1>
    %s
%s
    <p>%s</p>
    <span class="credit" onclick="window.open(\'%s\', \'_blank\')">%s</span>
  </body>
</html>'''

NOTES = '''
Routes with <span class="discontinued">Discontinued</span> tag have been
 discontinued since their completion.<br>
Routes with <span class="delisted">Delisted</span> tag remain operational
 but are absent from public transit agency websites (possibly intentionally).<br>
See project homepage for details:'''

def parse_args():
    '''
    This function uses an argparse.ArgumentParser to parse arguments.
    Returns argparse.Namespace which contains necessary flags and data.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='enable verbose mode')
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        default='index.html',
        help='output filename for HTML')
    parser.add_argument(
        '-i',
        '--images',
        type=str,
        help='relative path to root directory for images')
    parser.add_argument(
        'agencies',
        nargs='*',
        type=str,
        default=DEFAULT_AGENCIES_ORDER,
        help='specify agencies to use and their order of appearance')
    return parser.parse_args()

def completenessHTML(data_parsers):
    '''
    Given all route listings, returns regular Percentage Completeness heading
    if it's less than 100%, but Full Completeness heading when all routes are
    complete.
    '''
    dt = datetime.fromtimestamp(time()).strftime('%-m/%-d/%y')
    total = 0
    completed = 0
    for d in data_parsers:
        d_total, d_completed = d.completed()
        total += d_total
        completed += d_completed
    if completed == total:
        return '<h2>Fully Complete on %s</h2>' % dt
    return '<h2>%d%% Complete, Updated %s</h2>' % (completed * 100 // total, dt)

def main():
    '''
    Entry point of program.
    Parses arguments, gathers route listings, and writes them to output file.
    '''
    # This is necessary for time formatting
    locale.setlocale(locale.LC_TIME, 'en_US')
    args = parse_args()
    # For each agency requested, import its module and create its DataParser
    route_modules = tuple(import_module('routes.' + m) for m in args.agencies)
    if args.images:
        # Each DataParser is constructed with its image directory
        # This will automatically create RouteListings for each image it has
        data_parsers = tuple(
            route_modules[i].DataParser(a, args.verbose, args.images)
            for i, a in enumerate(args.agencies))
    else:
        # Construct DataParsers with no image directory
        data_parsers = tuple(
            route_modules[i].DataParser(a, args.verbose)
            for i, a in enumerate(args.agencies))

    # For each module, get requests it wants performed; see
    # DataParser.get_initial_requests documentation
    # Thus, sets should all be unioned
    # They need to be put into a list, though, for the ordering
    initial_requests = list(
        set().union(*(d.get_initial_requests() for d in data_parsers)))
    # Perform the requests, then turn that into the resources dictionary
    initial_resources = dict(
        zip(initial_requests, request_all(initial_requests, args.verbose)))
    for d in data_parsers:
        d.update(initial_resources)
        d.sanitize_strings()

    if args.verbose:
        print('Writing to %s...' % args.output)
    with open(args.output, 'w') as fp:
        fp.write(FINAL_HTML % (
            completenessHTML(data_parsers),
            '\n'.join([d.to_html() for d in data_parsers]),
            NOTES,
            'https://github.com/6exagon/manybusesaway',
            re.search(r'([^\s]*\sv\d\.\d\..*)\s', __doc__).group(1)))
    if args.verbose:
        print('Done')

if __name__ == '__main__':
    main()
