import os
import time
import traceback

import slackweb
from logzero import logger
from slackclient import SlackClient

slack_token = os.environ["SLACK_API_TOKEN"]
webhook_url = os.environ["WEBHOOK_URL"]

sc = SlackClient(slack_token)
slack = slackweb.Slack(url=webhook_url)


def fetch_id2name(api, name):
    res = sc.api_call(api)
    if not res['ok']:
        return {}

    return dict((x['id'], x['name']) for x in res[name])


id2channel = fetch_id2name('channels.list', 'channels')
id2user = fetch_id2name('users.list', 'members')


def convert(msg):
    global id2channel

    subtype = msg['subtype']
    if subtype == 'message_deleted':
        pre = msg['previous_message']
        channel = id2channel[msg['channel']]
        user = id2user[pre['user']]

        return ('{user}さんが{channel}で'
                '「{text}」という発言を削除しました')\
            .format(user=user, channel=channel, text=pre['text'])
    if subtype.startswith('channel'):
        user = msg['user_profile']['name']
        channel = msg['channel']
        if channel not in id2channel:
            id2channel = fetch_id2name('channels.list', 'channels')

        channel = id2channel[channel]
        if subtype == 'channel_join':
            return ('{user}さんが{channel}にjoinしました')\
                .format(user=user, channel=channel)
        elif subtype == 'channel_archive':
            return ('{user}さんが{channel}をアーカイブしました')\
                .format(user=user, channel=channel)

    return msg['text']


def main():
    if sc.rtm_connect(with_team_state=False):
        logger.info('start!')
        while True:
            messages = sc.rtm_read()
            for msg in messages:
                if msg.get('type', '') != 'message':
                    continue
                if 'subtype' not in msg:
                    continue
                if msg['subtype'] == 'bot_message':
                    continue
                logger.info(msg)
                # https://api.slack.com/events/message

                text = convert(msg)
                slack.notify(text=text, username='Big Brother')

            time.sleep(1)
    else:
        print("Connection Failed")


if __name__ == '__main__':
    try:
        main()
    except:  # NOQA
        logger.error(traceback.format_exc())
