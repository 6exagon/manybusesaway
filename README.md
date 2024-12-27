# ManyBusesAway

<https://6exagon.github.io/manybusesaway>

A tracker website for riding every bus in King County Metro Transit, Sound Transit, Everett Transit, Pierce Transit, and Community Transit (transit agencies of Washington State, in the Greater Seattle area).

This project takes its name from [OneBusAway](https://onebusaway.org), an app/website serving real-time bus tracking data used _extensively_ in planning journeys in advance and in real time, without which this project would have been impossible.

### Website

This website shows a table of all bus routes from the above transit agencies; see below for more details on which are included. If a route has been completed (by myself), its completion date and a legible photograph from which this is determined are shown. Otherwise, these spaces are blank.

Click on the number of any active bus route to access its map (on its official site). Click on either of its termini to be brought to its schedule in the direction away from that terminus (also on its official site), though this is not always reliable due to inconsistencies within some transit agencies' websites. Click on its image if present to see the full-size image in your browser. Clicking has no effect when JavaScript is disabled.

### Structure

This project has an odd structure, because the webpage's HTML cannot be created on the fly by JavaScript. This is because the file creation dates for the images used to generate the page are only stored locally, not on GitHub or other services. So, the necessary format of this project is a collection of photographs taken on a phone at various times, transferred to a computer, cropped to 500x500 manually to preserve the creation dates, and saved in a folder. Then, a "compiler" of sorts, written in Python, creates the static HTML page (showing completed and incomplete buses) which can be pushed/uploaded to a hosting platform with the new images so the page displays. This compiler scrapes official transit agency websites for up-to-date route data when run, though which URLs to use and the format of the data can be very hardcoded, finnicky, and inconsistent. The official King/Pierce County Trip Planner is also used (these seem to be using identical assets and code), as the Everett Transit and Pierce Transit official websites are lacking.

The [images](images) folder contains real photographs of buses for each route, taken before, during, or after transportation. Capturing pedestrians in photos was avoided, but inevitable; as there is no reasonable expectation of privacy here, though, this is legal.

If you want to try this challenge yourself, replacing the contents of the images folder with any number of your own 500x500 .jpg images whose filenames follow the same naming conventions and then running `python3 manybusesaway.py images` from the project directory should produce a corresponding index.html file. Any directory can be specified instead of `images`; however, this must be a relative path and this script must be executed from the website root directory for image links to work correctly. `-a <agencies>` can be used to specify which agencies to include and their order, with the default being `KSEPC`. Additionally, `-o <file>` can be used to change the filename to output to, and the `-v` flag can be used for verbose output. Please leave a credit link to this repository at the bottom of the generated HTML output.

### History

This project was originally hosted on 000WebHost; this service was taken down during the summer of 2024. [This](https://web.archive.org/web/20240000000000*/https://6exagon.000webhostapp.com) is the Internet Archive backup of the site, and though incomplete, it shows the gradual completion of all available buses in King County Metro Transit and Sound Transit by February 2024. Unfortunately, some images were not backed up by Internet Archive's crawler. Before the original site was active, a Microsoft Excel spreadsheet was used, which quickly became more difficult to maintain than this automated system in which pictures are added to a folder and a spreadsheet is automatically produced.

In September 2024, all transit agencies updated their routes, adding new routes and deleting many existing ones. This page shows both completed but discontinued routes, and new routes which have since been completed.

In October 2024, the git and GitHub repository for this project was created (after updates to get the compiler working with the updated transit websites), in order to track changes for a major update to include Everett Transit, Pierce Transit, and Community Transit. Such is the reason behind code-related commits in this repository. The old HTML compiler from before September 2024 is not preserved in any form.

In summary, all King County Metro Transit and Sound Transit buses before September 2024 are included in this project, and all King County Metro Transit, Sound Transit, Everett Transit, Pierce Transit, and Community Transit buses from after this point are also included. In addition, some included edge cases (see below) were formerly not included; though many of these were completed long before this revision of the project (for example, the Link 2 Line at its opening), they have been revisited since December 2024 to obtain satisfactory photographs.

### Edge Cases

Most buses are straightfowardly from one of the five transit agencies, and these should be obvious. However, there are many unusual buses or modes of transportation listed on transit agency websites. Internal numbers are used for this project, retrieved from the [King County GIS Open Data map](https://gis-kingcounty.opendata.arcgis.com/datasets/51714753981a4c2695e603832c953551_2647) and other sources, but these may not always be visible on vehicles. Note that the compiler cannot properly parse many of these, as they're named irregularly in menus. Transportation methods not seemingly classified as buses and found in the same listings (Vanpool, Ferry, etc.) are not included.

King County Metro Transit:
- `90` is the King County Metro Transit snow shuttle, only operational during deep snow. It has not been operational since this challenge was started, but it may yet be.
- `96` is the First Hill Seattle Streetcar.
- `97` is the Link Shuttle, as a replacement for when Sound Transit Link trains are not operational.
- `98` is the South Lake Union Seattle Streetcar.
- `599` is the Link 1 Line, and `600` is the Link 2 Line, though these are operated by Sound Transit and included by name.
- `627` and `629` are the Duvall to Monroe and Duvall to North Bend SVT Shuttles, respectively. Snoqualmie Valley Transportation is not included in this project, for a number of reasons (mainly lack of information and incomplete integration and numbering for other SVT routes).
- `634` and `636` are the Trailhead Direct buses to the Issaquah Alps and Mount Si, respectively. These are seasonal.
- `671` through `678` are the King County RapidRide A through H lines. These are included by letter rather than by number.
- `973` and `975` are the King County Water Taxis to Vashon Island and West Seattle, respectively.
- `893`, `895`, and `981` through `994` are buses serving high schools in King County, managed by King County Metro Transit. Per the [Lakeside School website](https://www.lakesideschool.org/about-us/transportation), it is permissible to ride these as a non-student.

Sound Transit:
- The Link 1 Line, 2 Line, and T Line are all included by name.
- The Sounder N Line and S Line are both included by name.

Pierce Transit:
- The Stream Community Line is included by name.
- `101` is the Gig Harbor Trolley. It is seasonal and delisted out of season.

Community Transit:
- `701`, `702`, and `703` are Swift Blue, Green, and Orange, respectively. These are included by number rather than by name.
- Some Sound Transit routes that serve Snohomish County are duplicated here, but these are skipped.

### License

This software is distributed under the terms of the GNU General Public License. Please see the [license](LICENSE.txt) for more details.
