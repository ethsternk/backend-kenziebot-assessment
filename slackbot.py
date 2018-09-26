# -*- coding: utf-8 -*-

"""
    Main Python file for the slackbot, runs on a loop and looks at
    and handles all the messages on the server it's connected to.
"""

import os
import time
import re
import logging
# from logging.handlers import RotatingFileHandler
import requests
import random
import signal
from slackclient import SlackClient
from dotenv import load_dotenv
load_dotenv('./.env')

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
start_time = time.time()
farewell = "This isn't the last you'll see of me, worms!"
greeting = "Greetings, inferior beings."
log_format = '%(asctime)s : %(levelname)s : %(filename)s : %(message)s'

# logging
logging.basicConfig(filename='slackbot.log',
                    level=logging.INFO, format=log_format)

# logger = logging.getLogger(__name__)
# formatter = logging.Formatter(
#     '%(asctime)s : %(levelname)s : %(filename)s : %(message)s')
# LOGFILE = "./slackbot.log"
# handler = RotatingFileHandler(
#     LOGFILE, mode='a', maxBytes=2000, backupCount=2, encoding=None, delay=0)
# handler.setFormatter(formatter)
# logger.addHandler(handler)
# logger.setLevel(logging.DEBUG)

# exit flag for os signals
exit_flag = False


def signal_handler(sig_num, frame):
    """
        Handler for OS signals SIGTERM and SIGINT. Stops the program
        and logs info to the log.
    """
    global exit_flag
    signames = dict((k, v) for v, k in reversed(sorted(
        signal.__dict__.items())) if v.startswith('SIG')
        and not v.startswith('SIG_'))
    logging.warning('Received {} signal.'.format(signames[sig_num]))
    exit_flag = True


def parse_bot_commands(slack_events):
    """
        Parses a list of events from the Slack RTM API to find bot commands.
        If a bot command is found, returns a tuple of command and channel.
        If it's not found, then this function returns tuple (None, None).
    """
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention in message text (at the beginning)
        and returns the user ID which was mentioned.
        If there is no direct mention, returns None.
    """
    matches = re.search(MENTION_REGEX, message_text)
    # first group = mentioned username, second group = remaining message
    if matches:
        return (matches.group(1), matches.group(2).strip())
    else:
        return (None, None)


def format_time(s):
    """
        Takes a time duration (in seconds) and returns
        a formatted string, like `49 minutes`
    """
    if s >= 86400:
        unit = 'day'
        time = s / 86400
    elif s >= 3600:
        unit = 'hour'
        time = s / 3600
    elif s >= 60:
        unit = 'minute'
        time = s / 60
    else:
        unit = 'second'
        time = s
    tail = ''
    if time != 1:
        tail = 's'
    return str(time) + ' ' + unit + tail


def handle_command(command, channel):
    """
        Executes bot command if the command is known.
    """

    # response to send back to the user
    response = None

    # change response based on command recieved
    if command.startswith("help"):
        response = "Here are some commands to try:\n" \
            "> `help` – displays list of commands\n" \
            "> `ping` – displays uptime\n" \
            "> `xkcd` – posts a random xkcd comic\n" \
            "> `kill` – kills bot\n"
    elif command.startswith("kill"):
        response = "HA! Foolish mortals. I cannot be killed."
    elif command.startswith("ping"):
        response = "I'm about {} old, thank you.".format(
            format_time(int(time.time() - start_time)))
    elif command.startswith("xkcd"):
        newest = requests.get('http://xkcd.com/info.0.json').json()
        rng = random.randint(1, newest['num'] + 1)
        r = requests.get('http://xkcd.com/' + str(rng) + '/info.0.json').json()
        response = r['alt'] + ' ' + r['img']
    else:
        # if no matches, send default response
        response = "Sorry, I don't speak Japanese. Try `help`."

    # logs command recieved and response sent
    logging.info('Recieved command: {}'.format(command))
    if command.startswith("help"):
        logging.info('Responded with a list of commands.')
    else:
        logging.info('Responded with: "{}"'.format(response))

    # sends the respective response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response
    )


if __name__ == "__main__":

    # log bot starting
    logging.info('Bot started.')

    # hooking SIGINT and SIGTERM from OS
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while not exit_flag:

        try:

            # instantiate slack client
            slack_client = SlackClient(os.getenv('SLACK_BOT_TOKEN'))

            # connect to slack client
            if slack_client.rtm_connect(with_team_state=False):

                # success message for solidarity
                print("Bot connected and running!")

                # send greeting to #bot-test channel
                slack_client.api_call(
                    "chat.postMessage",
                    channel="CCD7USCR0",
                    text=greeting
                )
                logging.info('Responded with: "{}"'.format(greeting))

                # Read bot's user ID by calling Web API method `auth.test`
                starterbot_id = slack_client.api_call("auth.test")["user_id"]

                # checks for new messages every RTM_READ_DELAY seconds
                while not exit_flag:
                    command, channel = parse_bot_commands(
                        slack_client.rtm_read())
                    if command:
                        handle_command(command, channel)
                    time.sleep(RTM_READ_DELAY)

                # send farewell to #bot-test if bot is about to stop
                slack_client.api_call(
                    "chat.postMessage",
                    channel="CCD7USCR0",
                    text=farewell
                )
                logging.info('Responded with: "{}"'.format(farewell))

            else:

                # if the inital connection to the slack api fails,
                # print error and try again in 5 seconds
                print("Initial connection failed. "
                      "Exception printed in log file.\n"
                      "Trying again in 5 seconds...")
                time.sleep(5)

        # catch exceptions, log them, and restart bot in 5 seconds
        except Exception as e:
            logging.error('Encountered exception:', e)
            logging.debug('Trying again in 5 seconds...')
            time.sleep(5)

    # log info when bot stops
    logging.info('Bot stopped.')
    logging.info('Bot was up for about ' +
                 str(int(time.time() - start_time)) + ' seconds.')
