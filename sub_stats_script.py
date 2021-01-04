#!/usr/bin/python3-64 -X utf8
"""
Author  : u/Red_BW <https://www.reddit.com/user/Red_BW/>
Origin  : 2021-01-02
TODO: Implement the 3 sort functions, new, top, hot (everything is new)
TODO: Add and read args from praw.ini but allow args to overwrite
TODO: Query single submissions by subreddit and ID; retrieve comments from it
TODO: Overwrite file error handling
TODO: Interactive use with user prompts
TODO: Individual user login credentials and stats
TODO: Suppress Table Output
TODO: Error Check dates
TODO: Add Max Entry cap of 1000 to match arg
TODO: Output sub data to file, update file, and retrieve the same data from it
TODO: Check for praw.ini
TODO: Add details on pre-trimmed posts and post trimmed posts
"""

import argparse
import datetime
import praw
from praw import exceptions
from rich.traceback import install
from rich.console import Console
from rich.progress import track
from rich.table import Table
MAIN_COLOR = '#dbbcc3'
B_COLOR = 'blue'
C_COLOR = 'cyan'
G_COLOR = 'green'
M_COLOR = 'magenta'
O_COLOR = '#ff8b3d'
P_COLOR = '#a45ee5'
R_COLOR = '#ff4500'


__prog__ = 'sub_stats_script'
__purpose__ = 'A Query Script for Reddit to extract various Data Points'
__version__ = '0.9.9'
__version_date__ = '2021-01-03'
__version_info__ = tuple(int(i) for i in __version__.split('.') if i.isdigit())
# setting the console variable globally so it can be used everywhere
console = Console()
# Get and format today's date so it can be used everywhere
today_raw = datetime.datetime.today()
today = today_raw.strftime('%y%m%d')
ver = f'{__prog__} {__version__} ({__version_date__})'


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def get_args() -> argparse.Namespace:
    """
    See the help sections of each command.
    :return: Return all arguments passed in at the CLI
    """
    parser = argparse.ArgumentParser(
        prog=__prog__,
        description=f'{ver}: {__purpose__}',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='Please ensure the praw.ini is updated with your own Reddit'
               'API credentials.',
        add_help=False)

    r_args = parser.add_argument_group('required arguments')
    o_args = parser.add_argument_group('optional arguments')
    r_args.add_argument('-r',
                        '--reddit',
                        help='specify the subreddit',
                        metavar='subreddit',
                        type=str)
    # o_args.add_argument('-sort',
    #                     '--sort',
    #                     help='sort by "new", "top", or "hot"',
    #                     metavar='sort',
    #                     type=str)
    o_args.add_argument('-s',
                        '--submissions',
                        help='num of submissions to retrieve (max: 1000)',
                        metavar='(1 to 1000)',
                        type=int,
                        default=100)
    o_args.add_argument('-c',
                        '--comments',
                        help='max num of comments to retrieve per submission'
                             ' (max 1000)',
                        metavar='(1 to 1000)',
                        type=int,
                        required=False,
                        default=0)
    o_args.add_argument('-f',
                        '--from-date',
                        help='oldest post date as YYMMDD',
                        metavar='YYMMDD',
                        type=int,
                        default=today)
    o_args.add_argument('-t',
                        '--to-date',
                        help='newest post date as YYMMDD',
                        metavar='YYMMDD',
                        type=int,
                        default=today)
    o_args.add_argument('-m',
                        '--max-top',
                        help='maximum top entries per list to output',
                        metavar='(1-1000)',
                        type=int,
                        default=10)
    o_args.add_argument('-e',
                        '--export-console',
                        help='saves a copy of the console to ./output folder',
                        choices=['txt', 'html'],
                        required=False)
    o_args.add_argument('-l',
                        '--logging',
                        help='switches output to logging format',
                        action='store_true')
    o_args.add_argument('-h',
                        '--help',
                        help='show this help message and exit',
                        action='help')
    o_args.add_argument('-out',
                        metavar='<output_file>',
                        help='specify the output filename (example: '
                             './output/reddit_{subreddit}_{today}.txt)',
                        required=False)
    o_args.add_argument('-v',
                        '--version',
                        help='print the version and exit',
                        action='version',
                        version=f'{ver}')
    args = parser.parse_args()
    # This overrides an argument: parser.set_defaults(bar=42, baz='badger')
    return args


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def rp(var_to_print, rule: bool = False, style: str = MAIN_COLOR,
       log_locals: bool = False):
    """
    rp = rich print()
    All rich console print() functions in this script are redirected into this
    function. This is to allow one command to print as "rp()". This function
    then implements logging and rule if requested. It takes the rich variables.

    :param log_locals: allows printing of local variables with logging
    :param style: passes along the rich style parameter
    :param var_to_print: (str, required) -- string to print
    :param rule: (bool, optional, disabled) -- print a divider line
    :return: None
    """
    args = get_args()
    # if type(var_to_print) is str:
    #     if 'reddit' in var_to_print:
    #         var_to_print.replace('reddit', '[{R_COLOR}]reddit[/{R_COLOR}]')
    #     if 'BlackPink' in var_to_print:
    #         var_to_print.replace('BlackPink', '[black on #dbbcc3]BlackPink'
    #                              '[/black on #dbbcc3]')
    if rule:
        console.rule(f'{var_to_print}', style=style)
    # Enable logging
    elif args.logging:
        console.log(var_to_print, style=style, log_locals=log_locals)
    # Standard rich printing without logging
    else:
        console.print(var_to_print, style=style)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def date_range_loop(post_lists: list, args: argparse.Namespace) -> list:
    """
    Loop through the Submissions and discard everything not within the date
    range. Return them as a list.
    :param post_lists: All posts retrieved
    :param args: argparse args
    :return: Trimmed List of only posts within the requested date range
    """
    rp(f'\nAnalyzing dates and attempting to clean the submissions list to the'
       f' range specified: From: {args.from_date} To: {args.to_date}')
    # This sorts the list of post lists with oldest date first
    rp(f'Sorting all posts by date.')
    post_lists.sort(key=lambda x: x[0])
    rp(f'Oldest submission date is {post_lists[0][0]}, newest submission date '
       f'is {post_lists[-1][0]}')
    # Warn the customer if there are no posts older than the from date
    if int(post_lists[0][0]) > args.from_date:
        rp('\nWarning: Not enough posts were retrieved to reach the requested '
           f'from date: {args.from_date}\n', style=R_COLOR)
    rp(f'Starting submission post trimming.')
    date_range_loop_list = []
    # Iterate through the posts, stripping posts not within the date range
    for post_list in post_lists:
        if args.from_date <= int(post_list[0]) <= args.to_date:
            date_range_loop_list.append(post_list)
    rp(f'{len(post_lists)} submissions were retrieved. Trimmed down to'
       f' {len(date_range_loop_list)} submissions.')
    # Check the number of posts. If trimmed to 0, notify customer and exit
    if not date_range_loop_list:
        rp('Attention: The number of posts was trimmed to 0. Please adjust '
           'the date range or number of submissions to retrieve, to continue. '
           '\n Exiting Application.', style=R_COLOR)
        exit()
    rp(f'Oldest submission date is {date_range_loop_list[0][0]}, newest'
       f' submission date is {date_range_loop_list[-1][0]}')
    # This sorts the list of post lists with oldest date first
    rp('Sorting all submissions by Score')
    date_range_loop_list.sort(key=lambda x: x[3])
    return date_range_loop_list


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def sub_submissions(r: praw.Reddit, args: argparse.Namespace)\
        -> list:
    """
    This uses praw to query the specified subreddit to return a list of posts
    with various information. Each list contains: (YYMMDD, title, number of
    comments, score, ratio, award_count, permalink (aka 'r/'), author,
    submission ID (aka 'kopc8z' to reference this post), and YYYY-MM-DD).

    :param r: a praw.Reddit config object with the Reddit API credentials
    :param args: argparse arguments
    :return: List of submissions
    """
    post_list = []
    rp("")
    rp('Submissions', rule=True, style=f'{B_COLOR} bold')
    rp("")
    try:
        rp('Testing connection to reddit.\n')
        for sub_test in r.subreddit('announcements').new(limit=1):
            utc_date = datetime.datetime.utcfromtimestamp(sub_test.created_utc)
            date = utc_date.strftime('%y%m%d')
            rp(f'Successfully retrieved:', style=G_COLOR)
            rp(f'\n\tTitle:\t\t[{P_COLOR}]{sub_test.title}[/{P_COLOR}]\n'
               f'\tTitle Flair:\t[{P_COLOR}]{sub_test.link_flair_text}[/{P_COLOR}]'
               f'\n\tPermalink:\t[{P_COLOR}]{sub_test.permalink}[/{P_COLOR}]'
               f'\n\tSubreddit:\t[{P_COLOR}]{sub_test.subreddit}[/{P_COLOR}]'
               f'\n\tAuthor:\t\t[{P_COLOR}]u/{sub_test.author}[/{P_COLOR}]'
               f'\n\tAuthor Flair:\t[{P_COLOR}]{sub_test.author_flair_text}'
               f'[/{P_COLOR}]\n\tDate: \t\t{date}\n')
    except praw.exceptions.RedditAPIException as e:
        rp('\nWarning: Reddit API Exception Encountered', style=R_COLOR)
        rp(e)
        rp('Exiting application')
        exit()
    try:
        rp(f'Attempting to retrieve {args.submissions} submissions from'
           f' r/{args.reddit}\n')
        # rich 'track' function creates a progress bar on the cli in for loops
        for sub in track(r.subreddit(args.reddit).new(limit=args.submissions),
                         total=args.submissions):
            # Date Coding
            utc_date = datetime.datetime.utcfromtimestamp(sub.created_utc)
            date = utc_date.strftime('%y%m%d')
            alt_date = utc_date.strftime('%Y-%m-%d')
            # Post Title
            title = sub.title
            # Number of Comments under this Post
            num_com = int(sub.num_comments)
            # The Post Score or Karma
            score = int(sub.score)
            # Ratio of Up Votes to Down Votes
            ratio = float(sub.upvote_ratio)
            # Count the number of Awards given to the post
            award_count = int(sub.total_awards_received)
            # Permalink to the Post
            permalink = sub.permalink
            # Post Author
            author = sub.author
            sub_list = [date, title, num_com, score, ratio, award_count,
                        permalink, author, sub, alt_date]
            post_list.append(sub_list)
        rp(f'\nSuccessfully retrieved {len(post_list)} submissions from'
           f' r/{args.reddit}', style=G_COLOR)
    except praw.exceptions.RedditAPIException as e:
        rp('\nWarning: Reddit API Exception Encountered', style=R_COLOR)
        rp(e)
        rp('Please confirm the subreddit name.\nExiting application',
           style=R_COLOR)
        exit()

    return post_list


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def sub_comments(r: praw.Reddit, post_lists: list, args: argparse.Namespace)\
        -> tuple:
    """
    Use PRAW to grab all comments within the requested subreddit.
    :param r: a praw.Reddit config object with the Reddit API credentials
    :param post_lists: the trimmed posts of all Submissions
    :param args: argparse arguments
    :return: a tuple of 6 lists
    """
    rp("")
    rp('Comments', rule=True, style=f'{B_COLOR} bold')
    rp("")
    try:
        rp(f'Attempting to retrieve a maximum of {args.comments} comments each'
           f'from {len(post_lists)} submissions in the r/{args.reddit} sub.\n')
        # local lists to build and return
        sub_counts, com_counts, com_dates, tot_scores = {}, {}, {}, {}
        sub_dates, com_awards = {}, {}
        # Count the number of comments iterating through
        count = 0
        # Iterate through each post
        for post_list in track(post_lists, total=len(post_lists)):
            # Fill tot_scores dict with submission scores
            if str(post_list[7]) in tot_scores:
                tot_scores[str(post_list[7])] += post_list[3]
            else:
                tot_scores[str(post_list[7])] = post_list[3]
            # Fill sub_dates dict with submission dates
            if post_list[9] in sub_dates:
                sub_dates[post_list[9]] += 1
            else:
                sub_dates[post_list[9]] = 1
            # Fill sub_count dict with count of author posts
            if str(post_list[7]) in sub_counts:
                sub_counts[str(post_list[7])] += 1
            else:
                sub_counts[str(post_list[7])] = 1
            # open a reddit connection to the specified submission post
            submission = r.submission(id=post_list[8])
            submission.comments.replace_more(limit=args.comments)
            # Iterate through the comments list
            for com in submission.comments.list():
                if str(com.author) in tot_scores:
                    tot_scores[str(com.author)] += com.score
                else:
                    tot_scores[str(com.author)] = com.score
                if str(com.author) in com_awards:
                    com_awards[str(com.author)] += com.total_awards_received
                else:
                    com_awards[str(com.author)] = com.total_awards_received
                if str(com.author) in com_counts:
                    com_counts[str(com.author)] += 1
                else:
                    com_counts[str(com.author)] = 1
                utc_date = datetime.datetime.utcfromtimestamp(com.created_utc)
                date = utc_date.strftime('%Y-%m-%d')
                if date in com_dates:
                    com_dates[date] += 1
                else:
                    com_dates[date] = 1
                count += 1
        rp(f'\nSuccessfully retrieved and iterated through {count} comments.',
           style=G_COLOR)
    except praw.exceptions.RedditAPIException as e:
        rp('\nWarning: Reddit API Exception Encountered', style=R_COLOR)
        rp(e)
        rp('Exiting application', style=R_COLOR)
        exit()

    # Convert the dictionaries to list
    rp('\nConverting the comment dictionaries to lists.')
    com_awards_l = [(key, value) for key, value in com_awards.items()]
    com_counts_l = [(key, value) for key, value in com_counts.items()]
    com_dates_l = [(key, value) for key, value in com_dates.items()]
    sub_counts_l = [(key, value) for key, value in sub_counts.items()]
    sub_dates_l = [(key, value) for key, value in sub_dates.items()]
    tot_scores_l = [(key, value) for key, value in tot_scores.items()]
    # Sort the Lists
    rp('Sorting the comment lists.')
    com_awards_l.sort(key=lambda x: x[1], reverse=True)
    com_counts_l.sort(key=lambda x: x[1], reverse=True)
    com_dates_l.sort(key=lambda x: x[1], reverse=True)
    sub_counts_l.sort(key=lambda x: x[1], reverse=True)
    sub_dates_l.sort(key=lambda x: x[1], reverse=True)
    tot_scores_l.sort(key=lambda x: x[1], reverse=True)
    return com_counts_l, com_dates_l, sub_counts_l, sub_dates_l, tot_scores_l,\
        com_awards_l


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def args_print(args: argparse.Namespace):
    pass


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def main():
    """
    See the program purpose at the top of this script.
    """
    global console
    # Calls and returns all commandline arguments.
    args = get_args()
    # Enable rich console export and traceback handler, 'install()', if allowed
    if args.export_console:
        console = Console(record=True)
    install()
    rp("")
    rp('Initialization', rule=True, style=f'{B_COLOR} bold')
    rp("")
    # Reddit API Limit warning and Trim
    if args.submissions > 1000:
        rp(f'Warning: The Reddit API is limited to 1000 requests on an object.'
           f' Requested maximum of {args.submissions} submissions (-sub-lim, '
           f'--sub-limit) will be trimmed to 1000.')
        args.submissions = 1000
    if args.comments > 1000:
        rp(f'Warning: The Reddit API is limited to 1000 requests on an object.'
           f' Requested maximum of {args.comments} comments (-com-lim, --'
           f'com-limit) retrieved per post will be trimmed to 1000 per post.')
        args.comments = 1000

    if not args.out:
        args.out = f'./output/reddit_{args.reddit}_{today}.txt'
    # Print out the CLI Arguments to use
    args_print(args)

    # Print the Program Name, Version, and Purpose
    rp(f'{ver}: {__purpose__}\n', style=O_COLOR)
    rp(f'Outputting to Rich Console: {console}\n')
    # Print the runtime arguments/variables used
    rp(f'Using this configuration:'
       f'\n\tSubreddit:\t\t[{P_COLOR}]r/{args.reddit}[/{P_COLOR}]'
       f'\n\tNum of Submissions:\t[{P_COLOR}]{args.submissions}[/{P_COLOR}]'
       f'\n\tNum of Comments:\t[{P_COLOR}]{args.comments}[/{P_COLOR}]'
       f'\n\tFrom Date:\t\t[{P_COLOR}]{args.from_date}[/{P_COLOR}]'
       f'\n\tTo Date:\t\t[{P_COLOR}]{args.to_date}[/{P_COLOR}]'
       f'\n\tMax List Output:\t[{P_COLOR}]{args.max_top}[/{P_COLOR}]'
       f'\n\tOutput File:\t\t[{P_COLOR}]{args.out}[/{P_COLOR}]'
       f'\n\tEnable Logging Output:\t[{P_COLOR}]{args.logging}[/{P_COLOR}]'
       f'\n\tExport Console:\t\t[{P_COLOR}]{args.export_console}[/{P_COLOR}]')
    if args.export_console == 'html':
        rp(f'\tExport Console File:\t[{P_COLOR}]./output/console_{today}.html'
           f'[/{P_COLOR}]\n')
    elif args.export_console == 'txt':
        rp(f'\tExport Console File:\t[{P_COLOR}]./output/console_{today}.txt'
           f'[/{P_COLOR}]\n')

        # Establish read-only reddit variable using PRAW and config_file variables
    try:
        reddit = praw.Reddit('read_only')
        rp('Successfully loaded the reddit information from ./praw.ini',
           style=G_COLOR)
    except FileNotFoundError:
        rp('Warning: Could not load reddit information from config file.\n'
           'Terminating program.')
        exit()
    # retrieve a list of submissions
    submission_list, comments_list, submissions_date_list = [], [], []
    if args.submissions:
        submission_list = sub_submissions(reddit, args)
    # Trim the submissions to the date range specified
    submissions_date_list = date_range_loop(submission_list, args)
    total_comments, total_awards, sub_awards, com_awards = 0, 0, 0, 0
    # Create the t_awd_post_l
    awd_post_list = submissions_date_list[:]
    # Converting awd lists to dicts to get unique entries
    awd_sub_dict = {}
    for x_var in awd_post_list:
        if str(x_var[7]) in awd_sub_dict:
            awd_sub_dict[str(x_var[7])] += x_var[5]
        else:
            awd_sub_dict[str(x_var[7])] = x_var[5]
        total_awards += x_var[5]
        sub_awards += x_var[5]
    awd_post_list = [(key, value) for key, value in awd_sub_dict.items()]
    awd_post_list.sort(key=lambda x: x[1], reverse=True)
    # Retrieve comments if requested
    if args.comments:
        rp('Attempting reddit connection for comments.')
        f_tuple = sub_comments(reddit, submissions_date_list, args)
        # Unpack the f_tuple
        com_counts_l, com_awards_l = f_tuple[0], f_tuple[5]
        com_dates_l, sub_counts_l = f_tuple[1], f_tuple[2]
        sub_dates_l, tot_scores_l = f_tuple[3], f_tuple[4]
        # Trim the lists to the maximum requested
        rp(f'Attempting to trim the output lists to the maximum requested: {args.max_top}')
        t_com_counts_l = com_counts_l[:args.max_top]
        t_com_dates_l = com_dates_l[:args.max_top]
        t_sub_counts_l = sub_counts_l[:args.max_top]
        t_sub_dates_l = sub_dates_l[:args.max_top]
        t_tot_scores_l = tot_scores_l[:args.max_top]
        # Get Total Comments
        for value in com_dates_l:
            total_comments += value[1]
        # Get Comment Awards
        for entry in com_awards_l:
            if str(entry[0]) in awd_sub_dict:
                awd_sub_dict[str(entry[0])] += entry[1]
            else:
                awd_sub_dict[str(entry[0])] = entry[1]
            total_awards += entry[1]
            com_awards += entry[1]

        awd_post_list = [(key, value) for key, value in awd_sub_dict.items()]
        awd_post_list.sort(key=lambda x: x[1], reverse=True)

    submissions_date_list.sort(key=lambda x: x[3], reverse=True)
    t_submissions_date_list = submissions_date_list[:args.max_top]
    awd_post_list_two = submissions_date_list[:]
    awd_post_list_two.sort(key=lambda x: x[5], reverse=True)
    total_submissions = len(awd_post_list_two)
    t_awd_post_l = awd_post_list_two[:args.max_top]

    # Output the data
    rp("")
    rp('Output File', rule=True, style=f'{B_COLOR} bold')
    rp("")
    # Build Tables
    rp('Structuring Tables.')
    s_d_l_table = Table(title='Most Popular Posts')
    s_d_l_table.add_column('Upvotes', justify='right', style=C_COLOR, no_wrap=True)
    s_d_l_table.add_column('Awards', justify='right', style=G_COLOR, no_wrap=True)
    s_d_l_table.add_column('Titles', style=M_COLOR)
    s_d_l_table.add_column('Author', justify='right', style=B_COLOR, no_wrap=True)
    a_p_l_table = Table(title='Top Awarded Posts')
    a_p_l_table.add_column('Awards', justify='right', style=G_COLOR, no_wrap=True)
    a_p_l_table.add_column('Titles', style=M_COLOR)
    a_p_l_table.add_column('Author', justify='right', style=B_COLOR, no_wrap=True)
    t_s_table = Table(title='Top Submitters by Author')
    t_s_table.add_column('Submissions', justify='right', style=G_COLOR, no_wrap=True)
    t_s_table.add_column('Author', style=M_COLOR)
    t_c_table = Table(title='Top Comments by Author')
    t_c_table.add_column('Comments', justify='right', style=G_COLOR, no_wrap=True)
    t_c_table.add_column('Author', style=M_COLOR)
    c_u_table = Table(title='Top Upvotes by Author')
    c_u_table.add_column('Upvotes', justify='right', style=G_COLOR, no_wrap=True)
    c_u_table.add_column('Author', style=M_COLOR)
    s_a_table = Table(title='Submissions by Date')
    s_a_table.add_column('Submissions', justify='right', style=G_COLOR, no_wrap=True)
    s_a_table.add_column('Date', style=M_COLOR)
    c_a_table = Table(title='Comments by Date')
    c_a_table.add_column('Comments', justify='right', style=G_COLOR, no_wrap=True)
    c_a_table.add_column('Date', style=M_COLOR)
    # TODO: add a check if file exists
    rp(f'Attempting to output in Markdown to {args.out} and build tables.')
    with open(args.out, 'w') as f:
        f.write(f'# r/{args.reddit} Subreddit Stats for {args.from_date}-'
                f'{args.to_date}\n\n')
        f.write((f'## Generic Stats:\nTotal Submissions: **{total_submissions:,}**'
                 f'\n\nTotal Comments: **{total_comments:,}**\n\nTotal Awards: '
                 f'**{total_awards}**\n\n'))
        f.write(f'## Most Popular Posts\n\n')
        for index, t_sub in enumerate(t_submissions_date_list):
            f.write(f'{index + 1}. **{t_sub[3]:,}** upvotes: [{t_sub[1]}]'
                    f'({t_sub[6]}), posted by u/{t_sub[7]}\n')
            s_d_l_table.add_row(str(t_sub[3]), str(t_sub[5]), str(t_sub[1]),
                                str(t_sub[7]))
        if args.comments:
            f.write('\n## Top Posts by Awards\n\n')
            for index, t_sub in enumerate(t_awd_post_l):
                f.write(f'{index + 1}. **{t_sub[5]}** award(s) for [{t_sub[1]}]'
                        f'({t_sub[6]}), submitted by u/{t_sub[7]}\n')
                a_p_l_table.add_row(str(t_sub[5]), str(t_sub[1]), str(t_sub[7]))
            f.write('\n## Top Submitters\n\n')
            for index, t_sub in enumerate(t_sub_counts_l):
                f.write(f'{index + 1}. **{t_sub[1]:,}** submissions by u/{t_sub[0]}\n')
                t_s_table.add_row(str(t_sub[1]), str(t_sub[0]))
            f.write('\n## Top Commenters\n\n')
            for index, t_sub in enumerate(t_com_counts_l):
                f.write(f'{index + 1}. **{t_sub[1]:,}** comments by u/{t_sub[0]}\n')
                t_c_table.add_row(str(t_sub[1]), str(t_sub[0]))
            f.write('\n## Cumulative Upvotes (Post & Comments) within this sub'
                    ' by Author\n\n')
            for index, t_sub in enumerate(t_tot_scores_l):
                f.write(f'{index + 1}. **{t_sub[1]:,}** upvotes to u/{t_sub[0]}\n')
                c_u_table.add_row(str(t_sub[1]), str(t_sub[0]))
            f.write(f'\n## Submission Activity - Most Active Days:\n')
            for index, t_sub in enumerate(t_sub_dates_l):
                f.write(f'{index + 1}. **{t_sub[1]:,}** submissions on **{t_sub[0]}**\n')
                s_a_table.add_row(str(t_sub[1]), str(t_sub[0]))
            f.write(f'\n## Comments Activity - Most Active Days:\n')
            for index, t_sub in enumerate(t_com_dates_l):
                f.write(f'{index + 1}. **{t_sub[1]:,}** comments on **{t_sub[0]}**\n')
                c_a_table.add_row(str(t_sub[1]), str(t_sub[0]))
    rp('\nSuccessfully completed writing to file.\n', style=G_COLOR)
    rp('Printing Tables')
    rp("")
    rp('Output Tables', rule=True, style=f'{B_COLOR} bold')
    rp("")
    rp(f'\tTotal Submissions:\t{total_submissions:,}'
       f'\n\tTotal Comments:\t\t{total_comments:,}\n\tTotal Awards:\t\t'
       f'{total_awards}\n\tSubmission Awards:\t{sub_awards}\n\t'
       f'Comment Awards:\t\t{com_awards}\n')
    rp(s_d_l_table)
    rp(a_p_l_table)
    rp(t_s_table)
    rp(t_c_table)
    rp(c_u_table)
    rp(s_a_table)
    rp(c_a_table)
    rp('Tables Complete.', style=G_COLOR)

    # At the end, dump console output to console.txt if requested
    if args.export_console == 'html':
        console.save_html(f'./output/console_{today}.html')
    elif args.export_console == 'txt':
        console.save_text(f'./output/console_{today}.txt')
    rp('Exiting Application.')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
if __name__ == '__main__':
    main()
