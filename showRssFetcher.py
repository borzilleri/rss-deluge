import feedparser
import json
import util
import pytz
import os

from datetime import datetime
from dateutil.parser import parse
from deluge_client import DelugeRPCClient


BASEDIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(BASEDIR, "config.json")
STATUS_FILE = os.path.join(BASEDIR, "status.json")
CONFIG = json.load(open(CONFIG_FILE, 'r'))

client = DelugeRPCClient(CONFIG['deluge']['host'], CONFIG['deluge']['port'],
    CONFIG['deluge']['user'], CONFIG['deluge']['pass'])
client.connect()

status = None
if os.path.isfile(STATUS_FILE):
    status = json.load(open(STATUS_FILE, 'r'), object_pairs_hook=util.json_deserialize)
if status is None:
    status = {"lastFetchTime": datetime.min.replace(tzinfo=pytz.UTC), "shows": {}}

showrss = feedparser.parse(CONFIG['feedUrl'])
now = datetime.now()

def download_episode(item):
    print "Adding New Episode: {}".format(item.title)
    torrent_id = client.call('core.add_torrent_magnet', item.link, {})
    print "Added torrent: "+torrent_id

def is_new_episode(show_status, item):
    pub_date = parse(item.published)
    if pub_date > show_status['lastPubDate']:
        return True
    if item.guid not in show_status['recentGuids']:
        return True
    if item.tv_info_hash not in show_status['recentHashes']:
        return True
    return False

def update_show_status(show_status, item):
    show_status['name'] = item.tv_show_name
    pub_date = parse(item.published)
    if show_status['lastPubDate'] < pub_date:
        show_status['lastPubDate'] = pub_date
    if item.guid not in show_status['recentGuids']:
        show_status['recentGuids'] = ([item.guid] + show_status['recentGuids'])[:CONFIG['recentItemsCount']]

    if item.tv_info_hash not in show_status['recentHashes']:
        show_status['recentHashes'] = ([item.tv_info_hash] + show_status['recentHashes'])[:CONFIG['recentItemsCount']]
    return show_status

for item in showrss.entries:
    show_status = status['shows'].get(item.tv_show_id,
        {"name": "", "lastPubDate": datetime.min.replace(tzinfo=pytz.UTC), "recentGuids": [], "recentHashes": []})
    is_new = is_new_episode(show_status, item)
    if is_new:
        download_episode(item)
    else:
        print "Skipping old episode: "+item.title
    status['shows'][item.tv_show_id] = update_show_status(show_status, item)


with open(STATUS_FILE, 'w') as f:
    f.write(json.dumps(status, indent=2, default=util.json_serialize))
