import json
import logging
import re

logger = logging.getLogger(__name__)


class RtmEventHandler(object):
    def __init__(self, slack_clients, msg_writer, configurator):
        self.clients = slack_clients
        self.msg_writer = msg_writer
        self.configurator = configurator

    def handle(self, event):

        if 'type' in event:
            self._handle_by_type(event['type'], event)

    def _handle_by_type(self, event_type, event):
        # See https://api.slack.com/rtm for a full list of events
        if event_type == 'error':
            # error
            self.msg_writer.write_error(event['channel'], json.dumps(event))
        elif event_type == 'message':
            # message was sent to channel
            self._handle_message(event)
        elif event_type == 'channel_joined':
            # you joined a channel
            self.msg_writer.write_help_message(event['channel'])
        elif event_type == 'group_joined':
            # you joined a private group
            self.msg_writer.write_help_message(event['channel'])
        else:
            pass

    def _handle_message(self, event):
        # Filter out messages from the bot itself, and from non-users (eg. webhooks)
        if ('user' in event) and (not self.clients.is_message_from_me(event['user'])):

            msg_txt = event['text']
            current_channel = event['channel']
            current_user = event['user']

            if self.clients.is_bot_mention(msg_txt) or self._is_direct_message(current_channel):
                if 'help' in msg_txt:
                    self.msg_writer.write_help_message(current_channel)
                elif re.search('hi|hey|hello|howdy', msg_txt):
                    self.msg_writer.write_greeting(current_channel, current_user)
                elif 'create' in msg_txt:
                    self.configurator.create_configuration(current_user, current_channel, self.msg_writer)
                elif 'start' in msg_txt:
                    print event
                    self.msg_writer.send_message(current_channel, "So, you want to start the tunnel, eh?")
                    response = self.configurator.start_container(current_user, current_channel, self.msg_writer)
                    self.msg_writer.send_message(current_channel, response)
                elif 'stop' in msg_txt:
                    self.msg_writer.send_message(current_channel, "I'll see about shutting down the tunnel...")
                    self.configurator.stop_container(current_user, current_channel, self.msg_writer)
                elif 'status' in msg_txt:
                    self.configurator.container_status(current_user, current_channel, self.msg_writer)
                else:
                    self.msg_writer.write_prompt(current_channel)

    def _is_direct_message(self, channel):
        """Check if channel is a direct message channel

        Args:
            channel (str): Channel in which a message was received
        """
        return channel.startswith('D')
