# sub_stats_script
A Query Script for Reddit to extract various Data Points from a specified subreddit

## Requirements

[Python 3.9.0 x64](https://www.python.org/downloads/release/python-390/) (might work with older versions but only tested x64 on Win 10)

[praw](https://github.com/praw-dev/praw) 7.1.0 (the Python Reddit API Wrapper) 
```
pip install praw
```
[rich](https://github.com/willmcgugan/rich) 9.6.1 (rich text color formatting to the console) 
```
pip install rich
```
* The praw.ini is required and must be updated with your own free Reddit API and API Key. Details are in the ini.
* The ./output folder is currently required.

## Usage from the help

sub_stats_script.py -h

usage: sub_stats_script [-r subreddit] [-s 1 to 1000)] [-c (1 to 1000)] [-f YYMMDD] [-t YYMMDD] [-m (1-1000] [-e {txt,html}] [-l] [-h] [-out <output_file>] [-v]

sub_stats_script 0.9.9 (2021-01-03): A Query Script for Reddit to extract various Data Points

required arguments:

  -r subreddit, --reddit subreddit   specify the subreddit (default: None)
                        

optional arguments:

  -s (1 to 1000), --submissions (1 to 1000)  num of submissions to retrieve (max: 1000) (default: 100)
                        
  -c (1 to 1000), --comments (1 to 1000)  max num of comments to retrieve per submission (max 1000) (default: 0)
                        
  -f YYMMDD, --from-date YYMMDD   oldest post date as YYMMDD (default: 210104)
                        
  -t YYMMDD, --to-date YYMMDD   newest post date as YYMMDD (default: 210104)
                        
  -m (1-1000), --max-top (1-1000)   maximum top entries per list to output (default: 10)
                        
  -e {txt,html}, --export-console {txt,html}   saves a copy of the console to ./output folder (default: None)
                        
  -l, --logging         switches output to logging format (default: False)
  
  -h, --help            show this help message and exit
  
  -out <output_file>    specify the output filename (example: ./output/reddit_{subreddit}_{today}.txt) (default: None)
  
  -v, --version         print the version and exit
  

Please ensure the praw.ini is updated with your own RedditAPI credentials.


## Example Usage

Top get the top 10 for various stats in the date range of a specified subreddit:
```
sub_stats_script.py -r Fromis -s 200 -c 200 -f 201201 -t 201231 -m 10 -e html
```
This sets the subreddit to Fromis, will retrieve up to the last 200 submissions and up to 200 comments per submission, trim it to posts only between Dec 1 and Dec 31 of 2020, sorts the data and output the Top 10. It will also export the console output to an html file.

The console and -export-console are using the [rich](https://github.com/willmcgugan/rich) module which adds color, formatting, tables, and the progress bars. Setting the -export-console to html will retain the console color and formatting (except the background) while txt won't retain the proper table structure.

The -out file is formatted as markdown so it can be easily copied and pasted into an old.reddit comment or submission with little to no editing.

Note: There are two Reddit API limitations: 1000 max results // Cannot Query by date range

Limit 1: You can retrieve up to a maximum of 1000 submissions and 1000 comments per submission.

Limit 2: Currently, this script only queries 'new' so requesting submissions means it can only go back 1000 posts. This script will retrieve the number of posts requested and trim them to the date range specified.
