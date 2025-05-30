from src import parlay_connect
from src.log import logging


if __name__ == '__main__':
    logging.info("testing MM api")
    mm_instance = parlay_connect.ParlayInteractions()
    mm_instance.login()
    # mm_instance.cancel_all_wagers()
    mm_instance.get_balance()
    mm_instance.seeding()
    mm_instance.subscribe()
    mm_instance.send_supported_lines()
    mm_instance.keep_alive()
    # Jun 21, 2024, start with $908,637.13, then test batch bet/cancel to make sure all money are returned
