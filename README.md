## vk-album-downloader


A python script for downloading photos from vk.com

### Features
- Higher image resolution priority to download
- Without login
- Multiprocessing

### Requirements
- Python 3
- [ChromeDriver](https://chromedriver.chromium.org/) = Download the driver matching your Chrome browser
  - https://chromedriver.chromium.org/downloads
  - Once downloaded, make it executable (chmod +x in *NIX based OS) and export its path (or move to a location that is already in exported PATH locations)

### Command line usage
```
$ python3 vk_album.py <album URL> -o [folder to save to] 
```
Output folder is optional.
```
$ python3 vk_album.py <album URL>
```
Without output folder, download this album in the current directory called "album-XXXXXXXX_YYYYYYYYY".

**Example:**
```
$ python3 vk_album.py http://vk.com/album-XXXXXXXX_YYYYYYYYY -o /home/album
```

### Issues
- In multiprocessing, it would return error message if photo existed in the destination, but it can still download the whole album.
