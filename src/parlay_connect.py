import time

import requests
import json
import pysher
import schedule
import threading

from urllib.parse import urljoin
import config
#import config_staging as config
from log import logging
import constants


class ParlayInteractions:
    base_url: str = None
    balance: float = 0
    mm_keys: dict = dict()
    mm_session: dict = dict()
    all_tournaments: dict = dict()    # mapping from string to id
    my_tournaments: dict = dict()
    sport_events: dict = dict()   # key is event id, value is a list of event details and markets
    valid_odds: list = []
    pusher = None

    def __init__(self):
        self.base_url = config.BASE_URL
        self.mm_keys = config.MM_KEYS

    def login(self) -> dict:
        login_url = urljoin(self.base_url, config.URL['mm_login'])
        request_body = {
            'access_key': self.mm_keys.get('access_key'),
            'secret_key': self.mm_keys.get('secret_key'),
        }
        response = requests.post(login_url, data=json.dumps(request_body))
        if response.status_code != 200:
            logging.debug(response)
            raise Exception("login failed")
        mm_session = json.loads(response.content)['data']
        logging.info("\n" + "="*50)
        logging.info("🔐 AUTHENTICATION SUCCESSFUL")
        logging.info("="*50)
        logging.info(f"🎫 Access Token: {mm_session['access_token'][:20]}...")
        logging.info(f"⏰ Access Expires: {mm_session['access_expire_time']}")
        logging.info(f"🔄 Refresh Token: {mm_session['refresh_token'][:20]}...")
        logging.info(f"⏰ Refresh Expires: {mm_session['refresh_expire_time']}")
        logging.info("="*50)
        
        self.mm_session = mm_session
        logging.info("✅ MM session started successfully")
        return mm_session

    def seeding(self):
        # get allowed odds
        logging.info("\n🎯 Fetching allowed odds...")
        self.valid_odds = constants.VALID_ODDS_BACKUP

        # initiate available tournaments/sport_events
        # tournaments
        logging.info("\n🌱 Starting tournament and market seeding...")
        t_url = urljoin(self.base_url, config.URL['mm_tournaments'])
        headers = self.__get_auth_header()
        try:
            all_tournaments_response = requests.get(t_url, headers=headers)
        except Exception as e:
            print(e)
            if len(self.sport_events) == 0:
                return
            else:
                raise Exception("not able to seed tournaments")
        if all_tournaments_response.status_code != 200:
            if len(self.sport_events) == 0:
                # if seeded before, ignore one time failure
                raise Exception("not able to seed tournaments")
            else:
                return
        all_tournaments = json.loads(all_tournaments_response.content).get('data', {}).get('tournaments', {})
        self.all_tournaments = all_tournaments

        # get sportevents and markets of each
        event_url = urljoin(self.base_url, config.URL['mm_events'])
        market_url = urljoin(self.base_url, config.URL['mm_markets'])
        self.sport_events = dict()
        for one_t in all_tournaments:
            if one_t['name'] in config.TOURNAMENTS_INTERESTED or config.LOAD_ALL_TOURNAMENTS:
                self.my_tournaments[one_t['id']] = one_t
                try:
                    events_response = requests.get(event_url, params={'tournament_id': one_t['id']}, headers=headers)
                except Exception as e:
                    if len(self.sport_events) == 0:
                        raise Exception("Error")
                    else:
                        continue
                if events_response.status_code == 200:
                    events = json.loads(events_response.content).get('data', {}).get('sport_events')
                    if events is None:
                        continue
                    for event in events:
                        market_response = requests.get(market_url, params={'event_id': event['event_id']},
                                                       headers=headers)
                        if market_response.status_code == 200:
                            markets = json.loads(market_response.content).get('data', {}).get('markets', {})
                            if markets is None:
                                # this is more like a bug in MM api, as the event actually already closed
                                continue
                            event['markets'] = markets
                            self.sport_events[event['event_id']] = event
                            logging.info(f'✅ {event["name"]} markets loaded')
                        else:
                            logging.warning(f'⚠️  Failed to load markets for {event["name"]} - {market_response.reason}')
                else:
                    logging.warning(f'⚠️  Skipping tournament {one_t["name"]} - API request failed')

        logging.info("\n" + "="*60)
        logging.info("🎉 SEEDING COMPLETED SUCCESSFULLY")
        logging.info("="*60)
        logging.info(f"🏆 Tournaments Found: {len(self.my_tournaments)}")
        logging.info(f"🏟️  Sport Events Loaded: {len(self.sport_events)}")
        logging.info(f"📋 Target Tournaments: {len(config.TOURNAMENTS_INTERESTED)}")
        logging.info("="*60)
        for key in self.sport_events:
            one_event = self.sport_events[key]
            for market in one_event['markets']:
                if 'selections' in market:
                    if len(market['selections']) == 0:
                        raise Exception(f"selection is empty for event {key}")
                    for selection in market['selections']:
                        if len(selection) == 0 or selection[0].get('line_id', None) is None:
                            pass
                            #raise Exception(f'line_id is empty for event {key}')
                        #else:
                        #    print(selection[0]['line_id'])
                elif 'market_lines' in market:
                    for market_line in market['market_lines']:
                        if 'selections' not in market_line or len(market_line['selections']) == 0:
                            raise Exception(f'selections is empty')
                        for selection in market_line['selections']:
                            if len(selection) < 1:
                                #TODO: need to make sure we never get here
                                continue
                            if selection[0].get('line_id', None) is None:
                                raise Exception(f'line_id is empty for event {key}')
                            #print(selection[0]['line_id'])
                else:
                    #raise Exception("no selection, no market_lines")
                    logging.warning("⚠️  Market has no selections or market_lines")
        logging.info("✅ All market data validated successfully")


    def _get_channels(self, socket_id: float):
        # get websocket channels to subscribe to
        auth_endpoint_url = urljoin(self.base_url, config.URL['parlay_websocket_auth'])
        # auth_endpoint_url = "http://localhost:19002/api/v1/mm/pusher"
        channels_response = requests.post(auth_endpoint_url,
                                          data={'socket_id': socket_id},
                                          headers=self.__get_auth_header())
        if channels_response.status_code != 200:
            logging.error("failed to get channels")
            raise Exception("failed to get channels")
        channels = channels_response.json()
        return channels.get('data').get('authorized_channel', [])

    def _get_connection_config(self):
        connection_config_url = urljoin(self.base_url, config.URL['parlay_connection_config'])
        connection_response = requests.get(connection_config_url, headers=self.__get_auth_header())
        if connection_response.status_code != 200:
            logging.error("failed to get connection configs")
            raise Exception("failed to get channels")
        conn_configs = connection_response.json()
        return conn_configs

    def subscribe(self):
        connection_configs = self._get_connection_config()
        auth_endpoint_url = urljoin(self.base_url, config.URL['parlay_websocket_auth'])
        auth_header = self.__get_auth_header()
        auth_headers = {
                           "Authorization": auth_header['Authorization'],
                       }
        self.pusher = pysher.Pusher(key=connection_configs['key'], cluster=connection_configs['cluster'],
                                    auth_endpoint=auth_endpoint_url,
                                    auth_endpoint_headers=auth_headers)

        def public_event_handler(*args, **kwargs):
            logging.info("\n" + "="*60)
            logging.info("📈 PRICE QUOTE REQUEST RECEIVED")
            logging.info("="*60)
            
            try:
                event_received = json.loads(args[0]).get('payload', '{}')
                
                # Extract key information
                parlay_id = event_received.get('parlay_id', 'N/A')
                stake = event_received.get('stake', 'N/A')
                market_lines = event_received.get('market_lines', [])
                
                logging.info(f"🎲 Parlay ID: {parlay_id}")
                logging.info(f"💰 Stake Amount: ${stake}")
                logging.info(f"📊 Number of Lines: {len(market_lines)}")
                
                # Log market lines in a formatted way
                if market_lines:
                    logging.info("\n📋 Market Lines:")
                    for i, line in enumerate(market_lines, 1):
                        line_id = line.get('line_id', 'N/A')
                        market_id = line.get('market_id', 'N/A')
                        outcome_id = line.get('outcome_id', 'N/A')
                        sport_event_id = line.get('sport_event_id', 'N/A')
                        line_value = line.get('line', 'N/A')
                        
                        logging.info(f"  {i}. Line ID: {line_id[:8]}...")
                        logging.info(f"     Market: {market_id} | Outcome: {outcome_id}")
                        logging.info(f"     Event: {sport_event_id} | Line: {line_value}")
                        logging.info("")
                
                self.provide_price(event_received)
                
            except Exception as e:
                logging.error(f"❌ Error processing public event: {str(e)}")
            
            logging.info("="*60)
            """
            {'callback_url': 'https://api-ss-sandbox.betprophet.co/parlay/sp/order/offers', 
            'created_at': 1744210012349577200,
             'market_lines': [
               {'line': 5.5, 'line_id': '4507a1464a5b43289a99f45f53f5af65', 'market_id': 412, 'outcome_id': 13, 'sport_event_id': 30023691},
               {'line': 227, 'line_id': '8056acc62314b6300481536bf3d18121', 'market_id': 225, 'outcome_id': 13, 'sport_event_id': 20022121},
               {'line': 1.5, 'line_id': '708d089509c57f54c115f6562c479115', 'market_id': 256, 'outcome_id': 1715, 'sport_event_id': 10074487},
               {'line_id': 'fc10da901964584da0700e5d78b83904', 'market_id': 1303, 'outcome_id': 5, 'sport_event_id': 9615},
               {'line': 1.5, 'line_id': 'b9c742a2846e8fcb870c9f5e912f7d51', 'market_id': 256, 'outcome_id': 1715, 'sport_event_id': 10074489},
               {'line_id': '200954f9f9accd9754e2283806e991b5', 'market_id': 1303, 'outcome_id': 5, 'sport_event_id': 9617}],
               'parlay_id': '83d790df-1ced-4490-a06a-7cb224faf59b',
               'stake': 3.49}
            """

        def private_event_handler(*args, **kwargs):
            try:
                event_received = json.loads(args[0]).get('payload', '{}')
                
                # Only process if it's a price confirmation request (has callback_url)
                if 'callback_url' in event_received:
                    logging.info("\n" + "="*50)
                    logging.info("✅ PRICE CONFIRMATION REQUEST")
                    logging.info("="*50)
                    
                    parlay_id = event_received.get('parlay_id', 'N/A')
                    odds = event_received.get('odds', 'N/A')
                    logging.info(f"🎲 Parlay ID: {parlay_id}")
                    logging.info(f"📊 Confirmed Odds: {odds}")
                    
                    self.confirm_price(event_received)
                    logging.info("="*50)
                else:
                    # Parse timestamp for health check
                    timestamp = json.loads(args[0]).get('timestamp', 'N/A')
                    logging.info(f"💚 Health check received - System OK (timestamp: {timestamp})")
                    
            except Exception as e:
                logging.error(f"❌ Error processing private event: {str(e)}")

        # We can't subscribe until we've connected, so we use a callback handler
        # to subscribe when able
        def connect_handler(data):
            socket_id = json.loads(data)['socket_id']
            available_channels = self._get_channels(socket_id)
            broadcast_channel_name = None
            private_channel_name = None
            private_events = None
            for channel in available_channels:
                if 'broadcast' in channel['channel_name']:
                    broadcast_channel_name = channel['channel_name']
                    public_events = channel['binding_events']
                else:
                    private_channel_name = channel['channel_name']
                    private_events = channel['binding_events']
            broadcast_channel = self.pusher.subscribe(broadcast_channel_name)
            for event in public_events:
                # 'price.ask.new' is to receive parlay quoting requests
                broadcast_channel.bind(event, public_event_handler)
                logging.info(f"🔗 Subscribed to broadcast channel: {event}")

            private_channel = self.pusher.subscribe(private_channel_name)
            for private_event in private_events:
                # 'price.confirm.new'
                private_channel.bind(private_event, private_event_handler)
                logging.info(f"🔒 Subscribed to private channel: {private_event}")

        self.pusher.connection.bind('pusher:connection_established', connect_handler)
        self.pusher.connect()

    def provide_price(self, price_quote_request):
        # have to be valid for more than 5 seconds
        now_nanno = int((time.time() + 500) * 1000000000)
        lines = price_quote_request['market_lines']
        provide_price_result = requests.post(
            price_quote_request['callback_url'],
            data=json.dumps({
                'parlay_id': price_quote_request['parlay_id'],
                'offers': [
                    {
                        'valid_until': now_nanno,
                        'odds': 100000,
                        'max_risk': 200,
                        "estimated_price": [{'line_id': x['line_id'], 'odds': 200} for x in lines]
                    },
                    {
                        'valid_until': now_nanno,
                        'odds': 800,
                        'max_risk': 2000,
                        "estimated_price": [{'line_id': x['line_id'], 'odds': 200} for x in lines]
                    }
                ]
            }),
            headers=self.__get_auth_header()
        )
        if provide_price_result.status_code == 200:
            logging.info("🚀 Price quote sent successfully!")
        else:
            logging.error(f"❌ Failed to send price quote - Status: {provide_price_result.status_code}")
            logging.error(f"Response: {provide_price_result.text}")

    def confirm_price(self, price_confirm_request):
        # have to be valid for more than 5 seconds
        confirm_price_result = requests.post(
            price_confirm_request['callback_url'],
            data=json.dumps({
                                "action": "accept",  # "reject"
                                "confirmed_odds": price_confirm_request['odds'],
                                #"confirmed_stake": 100.0,  # Optional. If null, no change to the stake
                                "price_probability": [
                                    {
                                        "max_risk": 200.0,
                                        "lines": [
                                            {"line_id": "line_1",
                                             "probability": 0.5
                                             },
                                            {"line_id": "line_2",
                                             "probability": 0.4
                                             }
                                        ]
                                    },
                                    {
                                      "max_risk": 3000.0,
                                      "lines": [
                                        {
                                          "line_id": "line_1",
                                          "probability": 0.4
                                        },
                                        {
                                          "line_id": "line_2",
                                          "probability": 0.5
                                        }
                                      ]
                                    }
                               ]
                            }),
            headers=self.__get_auth_header()
        )
        if confirm_price_result.status_code == 200:
            logging.info("✅ Price confirmation sent successfully!")
        else:
            logging.error(f"❌ Failed to send price confirmation - Status: {confirm_price_result.status_code}")
            logging.error(f"Response: {confirm_price_result.text}")

    def get_balance(self):
        balance_url = urljoin(self.base_url, config.URL['mm_balance'])
        response = requests.get(balance_url, headers=self.__get_auth_header())
        if response.status_code != 200:
            logging.error("failed to get balance")
            return
        self.balance = json.loads(response.content).get('data', {}).get('balance', 0)
        logging.info(f"💰 Current Account Balance: ${self.balance:,.2f}")

    def send_supported_lines(self):
        balance_url = urljoin(self.base_url, config.URL['parlay_supported_lines'])
        ids_supported = []
        if len(self.sport_events) > 0:
            one_event = list(self.sport_events.keys())[0]
            for market in self.sport_events[one_event]['markets']:
                if 'selections' in market:
                    ids_supported.extend([x[0]['line_id'] for x in market['selections']])
        if len(ids_supported) > 0:
            response = requests.post(balance_url,
                                     json={'supported_lines': ids_supported},
                                     headers=self.__get_auth_header())
            if response.status_code != 200:
                logging.error("❌ Failed to send supported lines")
            else:
                logging.info(f"📋 Successfully sent {len(ids_supported)} supported lines")
        else:
            logging.warning("⚠️  No supported lines found to send")

    def schedule_in_thread(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def __auto_extend_session(self):
        # need to use new api, for now just create new session to pretend session extended
        refresh_url = urljoin(self.base_url, config.URL['mm_refresh'])
        response = requests.post(refresh_url, json={'refresh_token': self.mm_session['refresh_token']},
                                 headers=self.__get_auth_header())
        if response.status_code != 200:
            logging.info("Failed to call refresh endpoint")
            self.login()
        else:
            self.mm_session['access_token'] = response.json()['data']['access_token']
            if self.pusher is not None:
                self.pusher.disconnect()
                self.pusher = None
            # self.subscribe()    # need to subscribe again, as the old access token will expire soon

    def keep_alive(self):
        child_thread = threading.Thread(target=self.schedule_in_thread, daemon=False)
        child_thread.start()

    def __get_auth_header(self) -> dict:
        return {
            'Authorization': f'Bearer '
                             f'{self.mm_session["access_token"]}',
        }



