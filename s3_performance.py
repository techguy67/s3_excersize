#!/usr/bin/python

import boto.s3.connection
from boto.s3.key import Key
from optparse import OptionParser
import logging
import time
import sys
import os

# cofigparser in python 2.x is camel case and changed for python3 to be pep 8 compliant
# Using try and except will allow this app to run on either version

try:
    from configparser import SafeConfigParser
except:
    from ConfigParser import SafeConfigParser

try:
    parser = SafeConfigParser()
    parser.read('s3_performance.config')
except:
    print("Could not open config file")
    
    


log_filename = 's3_performance.log'
logging.basicConfig(filename=log_filename,
            level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p'
	                    )
try:
    conn = boto.connect_s3(
        aws_access_key_id = parser.get('connection_info', 'accessid'),
        aws_secret_access_key = parser.get('connection_info', 'secretkey'),
        host = parser.get('connection_info', 'host'),
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
	   )
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

""" Option parser """
logging.info('========================')
logging.info('New session')
logging.info('========================')
logging.info('Parsing options')

parser = OptionParser(usage='''
	 %prog [options] filename
	        
	        s3_performance is a simple tool to measure the performance of PUT and GET commands for demo.scality.com.
	        Given the number and size of the files to perform one of the operations on, it will output the average, minimum
	        and maximum time of each operation, operations per seconds and their speed in Mb/s.  E.g.
	
	        500 1024KB GET's performed:
	        ------------------------------------
	          Avg: 60.0 seconds;    133.36 Mb/s
	          Min: 332.3 seconds;   24.0 Mb/s
	          Max: 48.3 seconds;    165.6 Mb/s
	          ''',
	        version="%prog 1.0")
     
parser.add_option("-b", "--bucket", action="store", dest="bucketname",
                 help="Name of the bucket to perform operations on. \
                 If no bucket name is specified a random name will be used.")
parser.add_option("-o", "--operation", action="store", dest="operation",
                 help="Values can be put or get")
parser.add_option("-n", "--numfiles", action="store", dest="numfiles",
	             help="Number of files to perform operations on")
parser.add_option("-s", "--size", action="store", dest="filesize",
	             help="The size of files in KB")

(options, _) = parser.parse_args()
    
logging.info('Validating options')
    
if len(sys.argv[1:]) == 0:
    parser.print_help()
    exit(1)
       
if options.bucketname is None:
    try:
        logging.info('Creating bucket with format month-day-year-hour-minute-second-s3perf')
        bucketname=time.strftime("%m-%d-%Y-%H-%M-%S-s3perf")
        bucket = conn.create_bucket(bucketname)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
    
else:
    logging.info('Bucket already exists, moving on...')
    bucketname=options.bucketname

if options.numfiles is None:
    print("please specify number of files with -n")
    exit(1)

if options.filesize is None:
    print("please specify file size in KB to test with -s")
    exit(1)

if options.operation is None:
    print("please specify file operation you wish to use")
    exit(1)

def main():
    try:    
        logging.info("Creating a file to use for put's")
        print("Creating a file to use for testing's")
        filesize = float(options.filesize)
        bitsize = int(filesize * 1024)
        f = open('tmpfile',"wb")
        f.seek(bitsize)
        f.write(b'{\x03\xff\x00d')
        f.close()
        if options.operation == 'put':
            put_data(bitsize)
        elif options.operation == 'PUT':
            put_data(bitsize)
        elif options.operation == 'get':
            get_data(bitsize)
        elif options.operation == 'GET':
            get_data(bitsize)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
        
def put_data(bitsize):
    num = int(options.numfiles)
    count = 1
    fileprefix='put_file-'
    filename=fileprefix+str(count)
    results =[]
    logging.info("Uploading %s %sKB files ...." % (num, options.filesize))
    print("Uploading %s %sKB files ...." % (num, options.filesize))
    
    while num > 0:
        
        starttime = time.time()
        #print("uploading file %s of %s ......" % (count, options.numfiles))
        b = conn.get_bucket(bucketname)
        k = Key(b)
        k.key = filename
        k.set_contents_from_filename('tmpfile')
        endtime = time.time()
        totaltime = endtime - starttime 
        results.append(round(totaltime, 2))
        mbps = (bitsize * 8 / totaltime / 1000000)
        
        logging.info('File upload %s of %s' % (count, options.numfiles))
        #logging.info('File upload took %s at a speed of %s' % totaltime, mbps)
        print("File upload {count} of {numfiles} took {totaltime} seconds at a speed of {mbps} Mbps".format(totaltime = round(totaltime,2),
                mbps = round(mbps,2), count=count, numfiles=options.numfiles)
             )
        num -= 1
        count += 1
        filename = fileprefix+str(count)
    
    print("\n============================================================")
    print("%s %sKB PUT's performed:" % (options.numfiles, options.filesize))
    print("------------------------------------------------------------")
    print("The minimum time was %s seconds at a speed of %s Mbps" % (min(results), round(bitsize * 8 / min(results) /1000000, 2)))
    print("The Maximum time was %s seconds at a speed of %s Mbps" % (max(results), round(bitsize * 8 / max(results) /1000000, 2)))
    ttime = sum(results)/len(results)
    print("The Average time was %s seconds at a speed of %s Mbps" % (round(ttime, 2), round(bitsize * 8 / ttime / 1000000, 2)))
    
# Let's clean things up
    if options.bucketname is None:
        # If a bucket name wasn't supplied, then we created our own
        logging.info('Removing temp files')
        print("Removing bucket ...")
        b = conn.get_bucket(bucketname)
        logging.info('Removing temp bucket')
        for key in b.list():
            key.delete()
        conn.delete_bucket(bucketname)
        os.remove('tmpfile')
    else:
        # Used an existing bucket, so cleaning up the files we created for test
        logging.info('Deleting temp files')
        files=int(options.numfiles) + 1
        for x in range(1, files):
            k.key = 'put_file-'+str(x)
            b.delete_key(k)
        os.remove('tmpfile')
            
def get_data(bitsize):
    num = int(options.numfiles)
    count = 1
    results =[]
    filename=('tmpfile')
    
    try:
        logging.info('Uploading test file')
        print("Uploading file to use for test")
        b = conn.get_bucket(bucketname)
        k = Key(b)
        k.key = filename
        k.set_contents_from_filename(filename)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
   
    try:
        logging.info("Downloading %s %sKB files ...." % (num, options.filesize))
        print("Downloading %s %sKB files ...." % (num, options.filesize))   
        
        while num > 0:
            starttime = time.time()
            key = b.get_key('tmpfile')
            fp = open("tmpfile", "wb")
            key.get_file(fp)
            endtime = time.time()
            totaltime = endtime - starttime
            results.append(round(totaltime, 2))
            
            mbps = (bitsize * 8 / totaltime / 1000000)
            logging.info('File %s of %s downloaded' % (count, options.numfiles))
            print("File download {count} of {numfiles} took {totaltime} seconds at a speed of {mbps} Mbps".format(totaltime = round(totaltime,2),
                   mbps = round(mbps,2), count=count, numfiles=options.numfiles)
                  )
            
            num -= 1
            count += 1
    
        print("\n============================================================")
        print("%s %sKB GET's performed:" % (options.numfiles, options.filesize))
        print("------------------------------------------------------------")
        print("The minimum time was %s seconds at a speed of %s Mbps" % (min(results), round(bitsize * 8 / min(results) /1000000, 2)))
        print("The Maximum time was %s seconds at a speed of %s Mbps" % (max(results), round(bitsize * 8 / max(results) /1000000, 2)))
        ttime = sum(results)/len(results)
        print("The Average time was %s seconds at a speed of %s Mbps" % (round(ttime, 2), round(bitsize * 8 / ttime / 1000000, 2)))

# Let's clean things up
        if options.bucketname is None: 
            # If a bucket name wasn't supplied, then we created our own
            logging.info('Removing temp files')
            print("Removing bucket ...")
            b = conn.get_bucket(bucketname)
            logging.info('Removing temp bucket')
            for key in b.list():
                key.delete()
            conn.delete_bucket(bucketname)
            os.remove('tmpfile')
        else:
            #Used an existing bucket, so cleaning up the file we created for test
            logging.info('Deleting temp files')
            k.key = 'tmpfile'
            b.delete_key(k)
            os.remove('tmpfile')
    
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise    
    
    
if __name__ == '__main__':
    main()
