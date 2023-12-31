# Addwatch conversation
ASK_SOURCE, ASK_CITY, ASK_TYPE, ASK_CATEGORY, ASK_AGENCY, ASK_MIN_ROOM, ASK_MAX_ROOM, ASK_MIN_PRIZE, ASK_MAX_PRIZE, \
    ASK_MIN_SURFACE, ASK_MAX_SURFACE, ASK_FLOOR, ASK_NAME = range(13)
CONFIRM, SKIP = range(2)

# Watchlist conversation
WATCH_LIST, WATCH_INFO, EDIT_WATCH, EDIT_NAME, EDIT_TYPE, EDIT_CATEGORY, EDIT_MIN_ROOM, EDIT_MAX_ROOM, EDIT_MIN_PRIZE, EDIT_MAX_PRIZE, \
    EDIT_MIN_SURFACE, EDIT_MAX_SURFACE, EDIT_FLOOR = range(13)
# WATCH_INFO
SELECT, BACK_TO_LIST, SUSPEND, RESUME, EDIT, REMOVE = range(6)
# EDIT_WATCH
NAME, TYPE_FILTER, CATEGORY_FILTER, AGENCY_FILTER, AUCTION_FILTER, MIN_ROOM_FILTER, MAX_ROOM_FILTER, MIN_PRIZE_FILTER, MAX_PRIZE_FILTER, \
    MIN_SURFACE_FILTER, MAX_SURFACE_FILTER, FLOOR_FILTER, BACK_TO_WATCH = range(13)

# Followers conversation
FOLLOWER_LIST = 0
REMOVE = 0
