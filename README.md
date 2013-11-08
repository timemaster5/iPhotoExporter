IPhotoExporter
===

iPhotoExporter is a python script that exports and synchronizes iPhoto events or albums (MacOSX) simply to folders.

In less than 5 minutes*, archive the contents of iPhoto in folders to see them from a NAS, a SmartTV or Windows for example!

It was also easier to identify duplicates with third party software.

*4'30 for 12GB of photos (MBP / SSD) 


###Key features : 

- Exports albums or events
- Synchronization of the elements
- Backup of originals (optional)
- Adds the title of the photo to the file name
- Creates hardlinks for saving space
- Destination file name can be based on exif capture time

Tested with iPhoto 11 9.5 on MacOSX 10.9 Mverick.


Use
-----------
 
* Copy the script (for example in Documents)
* Run a Terminal (Applications> Utilities> Terminal)
* Move to the location of the script
 
		cd $HOME/Documents 

* Run the script like this:

		python iphotoexporter.py [options] "iPhoto Library" "destination-folder"


   Options:
		--version       show program's version number and exit
		-h, --help      show this help message and exit
		-a, --albums    use albums instead of events
		-t, --test      don't actually copy files or create folders
		-l, --link      don't actually copy files, just make hardlinks
		-m, --time      destination file name will be exif time or create time
		-c, --caption   don't add captions to the filenames
		-v, --verbose   display most of the actions
		-o, --original  also copy original photos


See the examples below.

Examples
--------

You want to export all events, with the original images:

    python iphotoexporter.py -o "$HOME/Pictures/iPhoto Library.photolibrary" "$HOME/Pictures/iPhoto Export"

You want to create hardlinks with destination file name based on capture time, without caption 
in the destination file name
    
    python iphotoexporter.py -mcl "$HOME/Pictures/iPhoto Library.photolibrary" "$HOME/Pictures/iPhoto Export"

Results
---------
* By default, iPhotoExporter exports events. To export the albums use the -a option.

* The script created a different folder for each album or event.

* Originals photos are suffixed with [original].

* Photos whose title was edited are suffixed with the caption in brackets.
    
---
###Disclaimer : 
Derived from the script of [Derrick Childers](https://github.com/derrickchilders) on [macosxhints](http://www.macosxhints.com/article.php?story=20081108132735425), the iPhotoExplorer script is characterized by the addition of the synchronization, backup of originals, and works with accented characters. Base idea and code is fork of https://github.com/aurel-appsthru/iPhotoExporter - THANKS
