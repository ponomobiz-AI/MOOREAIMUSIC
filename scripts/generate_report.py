import os, json, pathlib
import anthropic
from datetime import datetime
from dateutil import tz

MY_CHANNEL_ID = os.environ.get("MY_CHANNEL_ID", "UCbkLhZ5uUnOejyQmtK5GOOw")
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
DENVER_TZ = tz.gettz("America/Denver")
NOW_DENVER = datetime.now(DENVER_TZ)
DATE_STR = NOW_DENVER.strftime("%A, %B %-d %Y")
DATE_FILE = NOW_DENVER.strftime("%Y-%m-%d")
COMPETITOR_IDS = ["@ATPmusic","UCQHqRnIatHGQlxfgXKz5JpQ","UCbwChnjsZXrD7GcWMiR_lBA","UCBZwQbwEAw_cIeWDHVz7Azg","UCLeVJzaHumte98Le_5rOvCQ","UCocdLZMk9veRGuN5JxixAeQ"]
VIDIQ_MCP_URL = "https://mcp.vidiq.com/mcp"
