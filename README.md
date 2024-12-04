# Completed Buses

A tracker website for riding every bus in King County Metro, Sound Transit, Everett Transit, and Community Transit (transit agencies of Washington State, in the Seattle area).

### Structure

This website has an odd structure, because the page's HTML cannot be created on the fly by a JavaScript program. This is because the file creation dates for the images used to generate the page are only stored locally, not on GitHub or other services. So, the necessary format of this project is a collection of images taken on a phone at various times, transferred to a computer, cropped to 500x500 manually to preserve the creation dates, and saved in a folder. Then, a "compiler" of sorts, written in Python, creates the static HTML page (showing completed and incomplete buses) which can be pushed/uploaded to a hosting platform with the new images so the page displays. This compiler scrapes transit agency websites for up-to-date route data when run, though which URLs to check and the format of the data can be very hardcoded and finnicky.

Unfortunately, Everett Transit's website lacks any form of plaintext representation of routes' terminals. As such, the possible options were:
- Including a PDF parsing library as a dependency to scrape Everett Transit's PDF route listing manual (which would need to be downloaded).
- Using a third-party website listing these routes in plain HTML (which was avoided for other transit agencies).
- Including a .csv file in this repository with Everett Transit's route data, which would need to be manually updated.
- Leaving the routes' terminals blank.

Of these, the third option seemed most within the spirit of the project.

The [images](images) folder contains real photographs of buses for each route, taken before, during, or after transportation. Capturing pedestrians in photos was avoided, but inevitable; as there is no reasonable expectation of privacy here, though, this is legal. If you want to try this challenge yourself, though, replacing the contents of the images folder with your own 500x500 .jpg images and then running `python3 html_compiler.py` from the project directory should produce a corresponding index.html file.

### History

This project was originally hosted on 000WebHost; this service was taken down during the summer of 2024. [This](https://web.archive.org/web/20240000000000*/https://6exagon.000webhostapp.com) is the Internet Archive backup of the site, and though incomplete, it shows the gradual completion of all available buses in King County Metro Transit and Sound Transit by February 2024. Unfortunately, some images were not backed up by Internet Archive's crawler. Before the original site was active, a Microsoft Excel spreadsheet was used, which quickly became more difficult to maintain than this automated system in which pictures are added to a folder and a spreadsheet is automatically produced.

In September 2024, all transit agencies updated their routes, adding new routes and deleting many existing ones. This page shows both completed but discontinued routes, and new routes which have since been completed.

In October 2024, the git and GitHub repository for this project was created (after updates to get the compiler working with the updated transit websites), in time to track changes in a major update to include Everett Transit and Community Transit. Such is the reason behind code-related commits in this repository. The old HTML compiler from before September 2024 is not preserved in any form.

In summary, all King County Metro Transit and Sound Transit buses before September 2024 are included in this project, and all King County Metro Transit, Sound Transit, Everett Transit, and Community Transit buses from after this point are also included. In addition, some included edge cases (see below) were formerly not included; though many of these were completed long before this revision of the project, they have been revisited since December 2024 to obtain satisfactory photographs.

### Edge Cases

Most buses are straightfowardly from one of the four transit agencies, and these should be obvious. However, there are many unusual buses or modes of transportation listed on transit agency websites. Internal numbers are used for this project, retrieved from the [King County GIS Open Data map](https://gis-kingcounty.opendata.arcgis.com/datasets/51714753981a4c2695e603832c953551_2647) and other sources, but these may not always be visible on vehicles. Note that the compiler cannot properly parse many of these, as they're named irregularly in menus. Transportation methods not seemingly classified as buses and found in the same listings (Vanpool, Ferry, etc.) are not included.

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

Community Transit:
- `701`, `702`, and `703` are Swift Blue, Green, and Orange, respectively. These are included by number rather than by name.
- Some Sound Transit routes that serve Snohomish County are duplicated here, but these are skipped.
