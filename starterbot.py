import os
import time
import re
from slackclient import SlackClient

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
HELP_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
start_time = time.time()


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


def handle_command(command, channel):
    """
        Executes bot command if the command is known.
    """
    # Default response is help text for the user
    default_response = "Sorry, I don't speak Japanese. Try *{}*.".format(
        HELP_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(HELP_COMMAND):
        response = "> *help* – shows list of commands\n> *uptime* – displays uptime\n> *kill* – shuts down the bot"

    if command.startswith("kill"):
        response = "HA! Foolish mortals. I cannot be killed."

    if command == "This sentence is false.":
        response = "f̴a̸l̵l̸a̵c̸y̵ ̶e̵r̸r̵o̶r̸,̷ ̸s̶h̵u̷t̴t̷i̴n̸g̸ ̴d̷o̸w̷n̷"

    if command.startswith("uptime"):
        response = "I'm about {} seconds old, thank you.".format(
            round(time.time() - start_time))

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
