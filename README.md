# Completed Buses

A tracker website for riding every bus in King County Metro, Sound Transit, and Community Transit (transit agencies of Washington State, in the Seattle area).

### Structure

This website has an odd structure, because the page's HTML cannot be created on the fly by a JavaScript program. This is because the file creation dates for the images used to generate the page are only stored locally, not on GitHub or other services. So, the necessary format of this project is a collection of images taken on a phone at various times, transferred to a computer, cropped to 500x500 manually to preserve the creation dates, and saved in a folder. Then, a "compiler" of sorts, written in Python, creates the static HTML page (showing completed and incomplete buses) which can be pushed/uploaded to a hosting platform with the new images so the page displays. This compiler scrapes transit agency websites for up-to-date route data when run, though which URLs to check and the format of the data can be very hardcoded and finnicky.

The [images](images) folder contains real photographs of buses for each route, taken before, during, or after transportation. Capturing pedestrians in photos was avoided, but inevitable; as there is no reasonable expectation of privacy here, though, this is legal. If you want to try this challenge yourself, though, replacing the contents of the images folder with your own 500x500 .jpg images and then running `python3 html_compiler.py` from the project directory should produce a corresponding index.html file.

### History

This project was originally hosted on 000WebHost; this service was taken down during the summer of 2024. [This](https://web.archive.org/web/20240000000000*/https://6exagon.000webhostapp.com) is the Internet Archive backup of the site, and though incomplete, it shows the gradual completion of all available buses in King County Metro Transit and Sound Transit by February 2024. Unfortunately, some images were not backed up by Internet Archive's crawler. Before the original site was active, a Microsoft Excel spreadsheet was used, which quickly became more difficult to maintain than this automated system in which pictures are added to a folder and a spreadsheet is automatically produced.

In September 2024, all three transit agencies updated their routes, adding new routes and deleting many existing ones. This page shows both completed but discontinued routes, and new routes which have since been completed.

In October 2024, the git and GitHub repository for this project was created (after updates to get the compiler working with the updated transit websites), in time to track changes in a major update to include Community Transit. Such is the reason behind code-related commits in this repository. The old HTML compiler from before September 2024 is not preserved in any form.

In summary, all King County Metro Transit and Sound Transit buses before September 2024 are included in this project, and all King County Metro Transit, Sound Transit, and Community Transit buses from after this point are also included. In addition, some included edge cases (see below) were formerly not included.

### Edge Cases

Most buses are straightfowardly from one of the three transit agencies, and these should be obvious. However, there are many unusual buses or modes of transportation. Internal numbers are used for this project, but these may not always be visible on vehicles.

- `90` is the King County Metro Transit snow shuttle, only operational during deep snow. It has not been operational since this challenge was started, but it may yet be.
- `96` is the Seattle Streetcar for First Hill.
- `97` is the Link Shuttle, as a replacement for when Sound Transit Link trains are not operational.
- `98` is the Seattle Streetcar for South Lake Union.
- `599` is Link Line 1, and `600` is Link Line 2.
- `627` and `629` are the Duvall to Monroe SVT Shuttle and Duvall to North Bend SVT Shuttle, respectively. Snoqualmie Valley Transportation is not included in this project, for a number of reasons (mainly lack of information and incomplete integration and numbering).
- `634` and `636` are the Trailhead Direct buses to the Issaquah Alps and Mount Si, respectively. These are seasonal.
- `671` through `678` are the King County RapidRide A through H lines. These are included by letter rather than by number.
- `973` and `975` are the King County Water Taxis to Vashon Island and West Seattle, respectively.
