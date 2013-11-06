# -*- coding: utf-8 -*-


# Appsthru.com
# http://appsthru.com
# Contact : aurel@appsthru.com
#
# IPhotoExporter is a python script that exports and synchronizes 
# events or iPhoto albums (MacOSX) simply in folders.
# 

__version__ = "0.1"

import pip
from xml.dom.minidom import parse, parseString, Node
from optparse import OptionParser
import os, time, re,stat, shutil, sys,codecs,locale,unicodedata,datetime

def extract_exif_time(fn):
    if not os.path.isfile(fn):
        return None
    try:
        im = Image.open(fn)
        if hasattr(im, '_getexif'):
            exifdata = im._getexif()
            ctime = exifdata[0x9003]
            #print ctime
            return ctime
    except: 
        _type, value, traceback = sys.exc_info()
        #print "Error:\n%r", value
	return None
    
    return None

def get_exif_prefix(fn):
    ctime = extract_exif_time(fn)
    if ctime is None:
	try:
	    ctime = datetime.datetime.fromtimestamp(os.path.getctime(fn)).strftime('%Y:%m:%d %H:%M:%S')
	except:
	    _type, value, traceback = sys.exc_info()
	    ctime = os.path.basename(fn).split('.',1)[0]
	    return ctime
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
	
	return unicodedata.normalize("NFC",text)

def copyImage( sourceImageFilePath, targetFilePath , doCopy = True, linkFile = False ) : 
	
	bCopyFile = False
	basename = os.path.basename(targetFilePath)
	
	if os.path.exists(targetFilePath):
	# if file already exists, compare modification dates
		targetStat = os.stat(targetFilePath)
		modifiedStat = os.stat(sourceImageFilePath)
     
		printv( "\t\tFile exists : %s , compare : " % (basename) )
		printv( "\t\t - modified: %d %d" % (modifiedStat[stat.ST_MTIME], modifiedStat[stat.ST_SIZE]) )
		printv( "\t\t - target  : %d %d" % (targetStat[stat.ST_MTIME], targetStat[stat.ST_SIZE]) )
	
		#why oh why is modified time not getting copied over exactly the same?
		if abs(targetStat[stat.ST_MTIME] - modifiedStat[stat.ST_MTIME]) > 10 or targetStat[stat.ST_SIZE] != modifiedStat[stat.ST_SIZE]:
			 
			printv( "\t\t --> File modified" )
			bCopyFile = True
			
		else : 
			printv( "\t\t --> File identical" )
			 
	else:
		bCopyFile = True
		
	if bCopyFile and \
	linkFile :
		print "\tLink of %s" % ( basename )
		if doCopy:
			os.link(sourceImageFilePath, targetFilePath)

	elif bCopyFile and \
	not linkFile :
		print "\tCopy of %s" % ( basename ) 
		if doCopy:
			shutil.copy2(sourceImageFilePath, targetFilePath)
	
	
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
        folderName = getElementText(getValueElementForKey(folderDict, "RollName")).encode('utf-8')
    else:
        folderName = getElementText(getValueElementForKey(folderDict, "AlbumName")).encode('utf-8')
        if folderName == 'Photos':
            continue

    #walk through all the images in this roll/event/album
    imageIdArray = getValueElementForKey(folderDict, "KeyList")
    
    #add this event/album in the folderList for later root dir cleaning
    folderName = unormalize( folderName )
    folderList.append( folderName )
	
    print "\n\n*Processing folder : %s" % (folderName.encode('UTF-8'))
    #print repr(folderName)
    #print repr(targetDir)

    #create event/album folder
    targetFileDir = os.path.join(targetDir, folderName).encode('utf-8')
    if not os.path.exists(targetFileDir) :
	
	printv( "\t*Directory does not exist - Creating: %s" % targetFileDir )
	if doCopy:
		os.makedirs(targetFileDir)
    
    #image list for later folder cleaning
    imageList = [] 
    
    for imageIdElement in findChildElementsByName(imageIdArray, 'string'):
    
        imageId = getElementText(imageIdElement)
        imageDict = getValueElementForKey(masterImageListDict, imageId)
        modifiedFilePath = getElementText(getValueElementForKey(imageDict, "ImagePath")).encode('utf-8')
        originalFilePath = getElementText(getValueElementForKey(imageDict, "OriginalPath"))
        caption = getElementText(getValueElementForKey(imageDict, "Caption")).encode('utf-8')

	modfp =  modifiedFilePath.split('.photolibrary/',1)
        modifiedFilePath = unormalize( args[0] ) + '/' + modfp[1]
        
        sourceImageFilePath = modifiedFilePath
        
	basename = os.path.basename(sourceImageFilePath)
	
	#basename = unormalize( basename )
        spname, spext = os.path.splitext(basename)
        spnameOrig = spname + spext

	if useTime :
		spname = get_exif_prefix(sourceImageFilePath)

        # use the caption name if exists
	if spname != caption :
		if useCaption :
        		basename = spname  + "_[" + caption.strip() + "]" + spext
		else :
			basename = spname + spext
       	else :
		basename = spname + spext
 
        basename = unormalize( basename ).encode('utf-8')
        print "Image: %s, ID: %s, Caption: %s, Datestamp: %s" % ( spnameOrig, imageId.encode('utf-8'), caption, get_exif_prefix(sourceImageFilePath) )
        
	targetFilePath = os.path.join(targetFileDir , basename ) 

        #add this image to the imageList for later folder cleaning
         
	imageList.append( basename )
	#print repr(basename)

	copyImage ( sourceImageFilePath, targetFilePath , doCopy , linkFile ) 
	
	# check if there is an original image
	if copyOriginal and originalFilePath != None : 
        	printv( "\t  *There is an original image")
        	basename = os.path.basename(originalFilePath)
        	
		spname, spext = os.path.splitext(basename)
		targetName = spname  + "_[orig]" + spext  
		
		targetName = unormalize( targetName )
		
        	targetFilePath = os.path.join(targetFileDir , targetName.encode('utf-8') )
		imageList.append( targetName )
        	
        	copyImage ( originalFilePath, targetFilePath , doCopy , linkFile )
        	
        
    # Cleaning of this folder
 
    #searches the directory for files and compare to imageList
    #delete files not present in imageList
    print "\n\t*Cleaning of the folder :"
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
			
    print "\tcleaning done."		 



#Cleaning Root Folder
print "\n===================\n"
print "Cleaning Root folder :"

for root, dirs,files in os.walk( targetDir.encode('utf-8') ):
	for name in dirs:
		
		#print "folder ", name 
		#print "type : ",type(name)
		#print "repr : ",repr(name)
		
			
		name = unormalize(name).encode('utf-8')
		
		if name not in folderList : 
			
			printv( "- remove '%s' " % name)
			#print repr(name)
			shutil.rmtree( os.path.join( targetDir.encode('utf-8'), name )  )
	  			
print "cleaning done."
print ""

albumDataDom.unlink()

stopTime = time.time()

elapsedTime = stopTime - startTime

print "Elapsed time : ", datetime.timedelta(seconds=elapsedTime )
print ""



	    
		 
	
	 
	    
 
 
