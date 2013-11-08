# -*- coding: utf-8 -*-


# Appsthru.com
# http://appsthru.com
# Contact : aurel@appsthru.com
#
# IPhotoExporter is a python script that exports and synchronizes 
# events or iPhoto albums (MacOSX) simply in folders.
#

__version__ = "0.2"

from unidecode import unidecode
from PIL import Image
from xml.dom.minidom import parse, parseString, Node
from optparse import OptionParser
import os, time, re,stat, shutil, sys,codecs,locale,datetime

def extract_exif_time(fn):
    if not os.path.isfile(fn):
	return None
    try:
        im = Image.open(fn)
        if hasattr(im, '_getexif'):
            exifdata = im._getexif()
            ctime = exifdata[0x9003]
	    if ctime == '0000:00:00 00:00:00' :
		return None
            return ctime
    except: 
        _type, value, traceback = sys.exc_info()
        #print "Error:\n%r", value
	return None

    return None

def get_exif_prefix(fn):
    fn = unormalize(fn)
    ctime = extract_exif_time(fn)
    if ctime is None:
	    return spname
    ctime = ctime.replace(':', '')
    ctime = re.sub('[^\d]+', '_', ctime)

    return ctime


def findChildElementsByName(parent, name):
    result = []
    for child in parent.childNodes:
        if child.nodeName == name:
            result.append(child)
    return result

def getElementText(element):
    if element is None: return None
    if len(element.childNodes) == 0: return None
    else: return element.childNodes[0].nodeValue

def getValueElementForKey(parent, keyName):
    for key in findChildElementsByName(parent, "key"):
        if getElementText(key) == keyName:
            sib = key.nextSibling
            while(sib is not None and sib.nodeType != Node.ELEMENT_NODE):
                sib = sib.nextSibling
            return sib

def unormalize (text ) :
    if type(text) is not unicode :
	#print ">>converting text",text,"(repr:", repr(text) , " )to unicode"
	text =   text.decode("utf-8")

    return unidecode(text)

def copyImage( sourceImageFilePath, targetFilePath , doCopy = True, linkFile = False ) : 

	sourceImageFilePath =  unormalize( args[0] ) + '/' + sourceImageFilePath.split('.photolibrary/',1)[1]

	bCopyFile = False
	basename = os.path.basename(targetFilePath)

	if os.path.exists(targetFilePath):
	# if file already exists, compare modification dates
		targetStat = os.stat(targetFilePath)
		modifiedStat = os.stat(sourceImageFilePath)

		printv( "- File exists : %s , compare : " % (basename) )
		printv( "  * modified: %d %d" % (modifiedStat[stat.ST_MTIME], modifiedStat[stat.ST_SIZE]) )
		printv( "  * target  : %d %d" % (targetStat[stat.ST_MTIME], targetStat[stat.ST_SIZE]) )

		#why oh why is modified time not getting copied over exactly the same?
		if abs(targetStat[stat.ST_MTIME] - modifiedStat[stat.ST_MTIME]) > 10 or targetStat[stat.ST_SIZE] != modifiedStat[stat.ST_SIZE]:
			printv( "\t --> File modified" )
			bCopyFile = True
		else : 
			printv( "\t --> File identical" )
	else:
		bCopyFile = True
	if bCopyFile and \
	linkFile :
		print "- Link of %s will be %s" % (os.path.basename(sourceImageFilePath) ,os.path.basename(targetFilePath) )
		if doCopy:
			try:
			    os.link(sourceImageFilePath, targetFilePath)
			except:
			    _type, value, traceback = sys.exc_info()
			    print 'unable to link file: ' + basename

	elif bCopyFile and \
	not linkFile :
		print "- Copy of %s will be %s" % ( os.path.basename(sourceImageFilePath) ,os.path.basename(targetFilePath)  )
		if doCopy:
			try:
			    shutil.copy2(sourceImageFilePath, targetFilePath)
			except:
			    _type, value, traceback = sys.exc_info()
			    print 'unable to copy file: ' + basename
	return

def printv(*args):
	if verbose :
		# Print each argument separately so caller doesn't need to
		# stuff everything to be printed into a single string
		for arg in args:
		   print arg,
		print

# -----  MAIN  ----------

usage   = "Usage: %prog [options] <iPhoto Library dir> <destination dir>"
version = "iPhotoExporter version %s" % __version__

option_parser = OptionParser(usage=usage, version=version)
option_parser.set_defaults(
        albums=False,
        test=False,
        verbose=False,
        original=True
)

option_parser.add_option("-a", "--albums",
                             action="store_true", dest="albums",
                             help="use albums instead of events"
)
option_parser.add_option("-t", "--test",
                             action="store_true", dest="test",
                             help="don't actually copy files or create folders"
)

option_parser.add_option("-l", "--link",
                             action="store_true", dest="link",
                             help="don't actually copy files, just make hardlinks"
)

option_parser.add_option("-m", "--time",
                             action="store_true", dest="time",
                             help="destination file name will be exif time or create time"
)

option_parser.add_option("-c", "--caption",
                             action="store_true", dest="caption",
                             help="don't add captions to the filenames"
)

option_parser.add_option("-v", "--verbose",
                             action="store_true", dest="verbose",
                             help="display most of the actions"
)

option_parser.add_option("-o", "--original",
                             action="store_true", dest="original",
                             help="also copy original photos"
)

(options, args) = option_parser.parse_args()

if len(args) != 2:
        option_parser.error(
            "Please specify an iPhoto library and a destination."
        )


iPhotoLibrary = unormalize( args[0] )
targetDir = unormalize( args[1] )

useCaption = not options.caption
useTime = options.time
doCopy = not options.test
linkFile = options.link
useEvents = not options.albums
verbose = options.verbose
copyOriginal = options.original

albumDataXml = os.path.join( iPhotoLibrary , "AlbumData.xml")

print ("Parsing AlbumData.xml")
startTime = time.time()

#minidom.parse produce Unicode strings
albumDataDom = parse(albumDataXml)
topElement = albumDataDom.documentElement
topMostDict = topElement.getElementsByTagName('dict')[0]
masterImageListDict = getValueElementForKey(topMostDict, "Master Image List")
folderList = []

if useEvents:
	listOfSomethingArray = getValueElementForKey(topMostDict, "List of Rolls")
else:
	listOfSomethingArray = getValueElementForKey(topMostDict, "List of Albums")


#walk through all the rolls (events) / albums

for folderDict in findChildElementsByName(listOfSomethingArray, 'dict'):
    if useEvents:
        folderName = getElementText(getValueElementForKey(folderDict, "RollName"))
    else:
        folderName = getElementText(getValueElementForKey(folderDict, "AlbumName"))
        if folderName == 'Photos':
            continue

    #walk through all the images in this roll/event/album
    imageIdArray = getValueElementForKey(folderDict, "KeyList")

    #add this event/album in the folderList for later root dir cleaning
    folderName = unormalize( folderName )
    folderList.append( folderName )

    print "\n*Processing folder : %s" % (folderName)
    #print repr(folderName)
    #print repr(targetDir)

    #create event/album folder
    targetFileDir = os.path.join(targetDir, folderName)
    if not os.path.exists(targetFileDir) :
	printv( "\t*Directory does not exist - Creating: %s" % targetFileDir )
	if doCopy:
		os.makedirs(targetFileDir)

    #image list for later folder cleaning
    imageList = [] 

    for imageIdElement in findChildElementsByName(imageIdArray, 'string'):

        imageId = getElementText(imageIdElement)
        imageDict = getValueElementForKey(masterImageListDict, imageId)
        modifiedFilePath = getElementText(getValueElementForKey(imageDict, "ImagePath"))
        originalFilePath = getElementText(getValueElementForKey(imageDict, "OriginalPath"))
        caption = getElementText(getValueElementForKey(imageDict, "Caption"))

        sourceImageFilePath = unormalize(args[0] + '/' + modifiedFilePath.split('.photolibrary/',1)[1])

	basename = os.path.basename(sourceImageFilePath)

        spname, spext = os.path.splitext(basename)
        spnameOrig = spname + spext

	#deal with caption and time in filename
	if useCaption :
	    if useTime :
		basename = get_exif_prefix(unormalize(sourceImageFilePath))  + "_[" + caption.strip() + "]" + spext
	    else:
		basename = caption.strip() + spext
	else :
	    if useTime :
		basename = get_exif_prefix(unormalize(sourceImageFilePath)) + spext
	    else:
		basename = spname + spext

        basename = unormalize( basename )
        print "Image: %s, ID: %s, Caption: %s, Datestamp: %s" % ( unormalize(spnameOrig), imageId, unormalize(caption), get_exif_prefix(unormalize(sourceImageFilePath)) )

	targetFilePath = os.path.join(unormalize(targetFileDir) , basename )

        #add this image to the imageList for later folder cleaning

	imageList.append( basename )
	#print repr(basename)

	copyImage ( unormalize(sourceImageFilePath), targetFilePath , doCopy , linkFile ) 
	
	# check if there is an original image
	if copyOriginal and originalFilePath != None : 
        	printv( "\t  *There is an original image")
        	basename = os.path.basename(originalFilePath)
        	
		spname, spext = os.path.splitext(basename)
		targetName = spname  + "_[orig]" + spext  
		
		targetName = unormalize( targetName )
		
        	targetFilePath = os.path.join(targetFileDir , targetName )
		imageList.append( targetName )
        	
        	copyImage ( originalFilePath, targetFilePath , doCopy , linkFile )
        	
    # Cleaning of this folder
    #searches the directory for files and compare to imageList
    #delete files not present in imageList
    print "\nCleaning of the folder :"
    for root, dirs, files in os.walk( targetFileDir ):
	for name in files:
		
		#print "file ", name 
		#print "type : ",type(name)
		#print "repr : ",repr(name)
		name = unormalize(name)
		#print repr(name)
		
		if name not in imageList : 
			printv( "\t - remove image : ",  name)
			
			os.remove( targetFileDir + "/" + name )
			
    print " done"

#Cleaning Root Folder
print "\nCleaning Root folder :"

for root, dirs,files in os.walk( targetDir ):
	for name in dirs:
		#print "folder ", name 
		#print "type : ",type(name)
		#print "repr : ",repr(name)
		name = unormalize(name)
		if name not in folderList : 
			printv( "- remove '%s' " % name)
			#print repr(name)
			shutil.rmtree( os.path.join( targetDir, name )  )
print " done"

albumDataDom.unlink()

stopTime = time.time()

elapsedTime = stopTime - startTime
print ""
print "Elapsed time : ", datetime.timedelta(seconds=elapsedTime )
