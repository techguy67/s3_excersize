# s3_excersize
This application will perform performance testing against an s3 object store

fill out s3_performance.config with your connection information. It should look like this

[connection_info]
host = your_domain
accessid = your_access_id
secretkey = your_secretkey

Usage:
   s3_performance.py [options] filename

          s3_performance is a simple tool to measure the performance of PUT and GET commands for demo.scality.com.
          Given the number and size of the files to perform one of the operations on, it will output the average, minimum
          and maximum time of each operation, operations per seconds and their speed in Mb/s.  E.g.

          500 1024KB GET's performed:
          ------------------------------------
            Avg: 60.0 seconds;    133.36 Mb/s
            Min: 332.3 seconds;   24.0 Mb/s
            Max: 48.3 seconds;    165.6 Mb/s


Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -b BUCKETNAME, --bucket=BUCKETNAME
                        Name of the bucket to perform operations on.
                        If no bucket name is specified a random name will be
                        used.
  -o OPERATION, --operation=OPERATION
                        Values can be put or get
  -n NUMFILES, --numfiles=NUMFILES
                        Number of files to perform operations on
  -s FILESIZE, --size=FILESIZE
                        The size of files in KB
