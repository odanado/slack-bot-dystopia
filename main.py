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


def fetch_channel_name(channel_id):
    global id2channel
    if channel_id not in id2channel:
        id2channel = fetch_id2name('channels.list', 'channels')
    return id2channel[channel_id]


def convert(msg):

    subtype = msg['subtype']
    if subtype == 'message_deleted':
        pre = msg['previous_message']
        channel = fetch_channel_name(msg['channel'])
        user = id2user[pre['user']]

        return dict(text=('{user}さんが{channel}で'
                          '「{text}」という発言を削除しました').
                    format(user=user, channel=channel, text=pre['text'])
                    )

    if subtype.startswith('channel'):
        user = msg['user_profile']['name']
        channel = fetch_channel_name(msg['channel'])

        if subtype == 'channel_join':
            return dict(
                text=('{user}さんが{channel}にjoinしました').
                format(user=user, channel=channel)
            )
        elif subtype == 'channel_archive':
            return dict(
                text=('{user}さんが{channel}をアーカイブしました').
                format(user=user, channel=channel)
            )

    if subtype.endswith('pinned_item'):
        user = id2user[msg['user']]
        channel = fetch_channel_name(msg['channel'])
        event = 'ピン留めしました' if subtype == 'pinned_item' else 'ピンを外しました'
        return dict(
            text=('{user}さんが{channel}で{event}').
            format(user=user, channel=channel, event=event),
            attachments=msg['attachments']
        )

    return msg['text']


def main():
    if sc.rtm_connect(with_team_state=False):
        logger.info('start!')
        while True:
            messages = sc.rtm_read()
            for msg in messages:
                logger.info(msg)
                if msg.get('type', '') != 'message':
                    continue
                if 'subtype' not in msg:
                    continue
                if msg['subtype'] == 'bot_message':
                    continue

                # https://api.slack.com/events/message
                data = convert(msg)
                logger.info(data)
                slack.notify(**data, username='Big Brother')

            time.sleep(1)
    else:
        print("Connection Failed")


if __name__ == '__main__':
    try:
        main()
    except:  # NOQA
        logger.error(traceback.format_exc())
