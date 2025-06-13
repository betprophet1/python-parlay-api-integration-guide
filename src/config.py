import json
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
user_info_path = os.path.join(script_dir, 'user_info.json')

with open(user_info_path) as fp:
    user_info_dict = json.load(fp)

MM_KEYS = {
    'access_key': user_info_dict['access_key'],
    'secret_key': user_info_dict['secret_key'],
}

TOURNAMENTS_INTERESTED = user_info_dict['tournaments']
LOAD_ALL_TOURNAMENTS = user_info_dict['load_all_tournaments']

BASE_URL = 'https://api-ss-sandbox.betprophet.co'
URL = {
    'mm_login': 'partner/auth/login',
    'mm_refresh': 'partner/auth/refresh',
    'mm_ping': 'partner/mm/pusher/ping',
    'mm_tournaments': 'partner/mm/get_tournaments',
    'mm_events': 'partner/mm/get_sport_events',
    'mm_markets': 'partner/mm/get_markets',
    'mm_balance': 'partner/mm/get_balance',
    'parlay_connection_config': 'parlay/sp/websocket/connection-config',
    'parlay_websocket_auth': 'parlay/sp/websocket/register',
    'parlay_supported_lines': 'parlay/sp/supported-lines'
}
