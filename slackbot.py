# -*- coding: utf-8 -*-

"""
    Main Python file for the slackbot, runs on a loop and looks at
    and handles all the messages on the server it's connected to.
"""

import os
import time
import re
import logging
import requests
import random
import signal
from slackclient import SlackClient
from dotenv import load_dotenv
load_dotenv('./.env')

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
HELP_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
start_time = time.time()

# logging
logging.basicConfig(filename='slackbot.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')

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
    # first group = username, second group = remaining message
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
    # Default response is help text for the user
    default_response = "Sorry, I don't speak Japanese. Try `{}`.".format(
        HELP_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(HELP_COMMAND):
        response = "Here are some commands to try:\n" \
            "> `help` – displays list of commands\n" \
            "> `ping` – displays uptime\n" \
            "> `xkcd` – posts a random xkcd comic\n" \
            "> `kill` – kills bot\n"

    if command.startswith("kill"):
        response = "HA! Foolish mortals. I cannot be killed."

    if command.startswith("ping"):
        response = "I'm about {} old, thank you.".format(
            format_time(int(time.time() - start_time)))

    if command.startswith("xkcd"):
        newest = requests.get('http://xkcd.com/info.0.json').json()
        rng = random.randint(1, newest['num'] + 1)
        r = requests.get('http://xkcd.com/' + str(rng) + '/info.0.json').json()
        response = r['alt'] + ' ' + r['img']

    # logs command
    logging.debug('Recieved command: {}'.format(command))
    if command.startswith(HELP_COMMAND):
        logging.debug('Responded with a list of commands.')
    else:
        logging.debug('Responded with: {}'.format(response))

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


if __name__ == "__main__":

    logging.info('Started bot.')

    # hooking SIGINT and SIGTERM from OS
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while not exit_flag:
        try:
            # instantiate Slack client
            slack_client = SlackClient(os.getenv('SLACK_BOT_TOKEN'))
            # starterbot's user ID in Slack (actually assigned on startup)
            starterbot_id = None
            if slack_client.rtm_connect(with_team_state=False):
                print("Bot connected and running!")
                slack_client.api_call(
                    "chat.postMessage",
                    channel="CCD7USCR0",
                    text="Greetings, inferior beings."
                )
                # Read bot's user ID by calling Web API method `auth.test`
                starterbot_id = slack_client.api_call("auth.test")["user_id"]
                while not exit_flag:
                    # tests connection, raises exception on failure
                    slack_client.api_call("api.test")
                    command, channel = parse_bot_commands(
                        slack_client.rtm_read())
                    if command:
                        handle_command(command, channel)
                    time.sleep(RTM_READ_DELAY)
                slack_client.api_call(
                    "chat.postMessage",
                    channel="CCD7USCR0",
                    text="This isn't the last you'll see of me, worms!"
                )
            else:
                print("Connection failed. Exception traceback printed above.")
                time.sleep(5)
        except Exception as e:
            logging.error('Encountered exception:', e)
            logging.debug('Trying again in 5 seconds...')
            time.sleep(5)
    logging.info('Bot stopped')
    logging.info('Bot was up for about ' +
                 str(int(time.time() - start_time)) + ' seconds.')
