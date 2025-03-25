import requests
import time
import ssl
import os
import json
import uuid
import re
import sys
import gc

from pynostr.event import Event, EventKind
from pynostr.relay_manager import RelayManager
from pynostr.message_type import ClientMessageType
from pynostr.key import PrivateKey
from pynostr.key import PublicKey
from pynostr.filters import FiltersList, Filters
from pynostr.encrypted_dm import EncryptedDirectMessage
from pynostr.utils import get_timestamp

from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, parse_qs


relay_manager = RelayManager(timeout=2)


def extract_parts(url):
    u = urlparse(url)
    q = parse_qs(u.query)
    return u.netloc, q.get('relay',[''])[0], q.get('secret',[''])[0]

def parse_and_print_notification(content):
    notification_type = json.loads(content)["notification_type"]    
    
    if notification_type == "payment_received":
        payment_type = "received"
    elif notification_type == "payment_sent":
        payment_type = "sent"
    else:
        raise Exception("weird notification")
    
    n = json.loads(content)["notification"]
    
    if len(n["description"]) > 0:
        description = "(%s)" % n["description"]
    else:
        description = ""
    output = "⚡️ %1.1f sats %s! %s" % ( d["amount"]/1000.0, payment_type, description)
    print(output)

    
def watch_for_notifications():
    nwc_string = os.environ['NWC']
    wallet_service_public_key, relay, secret = extract_parts(nwc_string)
    private_key = PrivateKey.from_hex(secret)

    relay_manager.add_relay(relay)

    start_timestamp = get_timestamp()-10.0
    filters = FiltersList( [ Filters(
        pubkey_refs=[private_key.public_key.hex()],
        kinds=[23196], limit=10),] )
    
    # List to store previously seen event ids
    messages_done = []
    
    while(True):
        subscription_id = uuid.uuid1().hex
        relay_manager.add_subscription_on_all_relays(subscription_id, filters)
        relay_manager.run_sync()
        
        while relay_manager.message_pool.has_notices():
            notice_msg = relay_manager.message_pool.get_notice()
            print("Notice: " + notice_msg.content)
            
        while relay_manager.message_pool.has_events():
            event_msg = relay_manager.message_pool.get_event()
            
            # Ignore previously seen events
            if(event_msg.event.id in messages_done):
                continue

            # Add this event to the list of seen events
            messages_done.append(event_msg.event.id)

            # According to NIP47, kind 23196 is a notification event
            if event_msg.event.kind == 23196:
                msg_decrypted = EncryptedDirectMessage()
                msg_decrypted.decrypt(private_key_hex=private_key.hex(),
                                      encrypted_message=event_msg.event.content,
                                      public_key_hex=public_key.hex())
            
            gc.collect()

        time.sleep(2)
        relay_manager.close_all_relay_connections()

if __name__ == "__main__":
    try:
        watch_for_notifications()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        relay_manager.close_all_relay_connections()
        exit(1)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        relay_manager.close_all_relay_connections()
        exit(1)
