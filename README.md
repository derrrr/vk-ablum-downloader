## vk-album-downloader


A python script for downloading photos from vk.com

### Features
- Higher image resolution priority to download
- Without login
- Multiprocessing

### Requirements
- Python 3
- [PhantomJS](https://github.com/ariya/phantomjs) = 2.5.0-beta
  - https://bitbucket.org/ariya/phantomjs/downloads/

### Command line usage
```
$ python3 vk_album.py <album URL> -P <PhantomJS path> -o [folder to save to] 
```
Album URL and PhantomJS path are required, output folder is optional.
```
$ python3 vk_album.py <album URL> -P <PhantomJS path>
```
Without output folder, download this album in the current directory called "album-XXXXXXXX_YYYYYYYYY".

**Example:**
```
$ python3 vk_album.py http://vk.com/album-XXXXXXXX_YYYYYYYYY -P <PhantomJS path> -o /home/album
```

### Issues
- In multiprocessing, it would return error message if photo existed in destination, but it can still download the whole album.
