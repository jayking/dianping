import datetime
import logging
import json
import os
import sys
import time
import random
import re
import httplib
import uuid
import re

import lxml.etree
import bs4
import helper_string
import groper.fetcher
import groper.store
import groper.cfg

logger = logging.getLogger(__name__)
logger.addHandler(groper.cfg.log_hdl_steam)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)


def main(args):
    path_data = helper_string.HelperString.to_uni(args.dest)

    headers = {
        "Referer": "http://www.dianping.com/",
    }
    fetcher = groper.fetcher.Fetcher(cfg=groper.cfg, headers=headers)

    city_list = get_city_list(path_data=path_data)
    
    result = dict(
        result=[],
        total=0,
        last_update=None,
    )
    items = []

    pattern = "_DP_HeaderData = { 'cityId': '(?P<city_id>\d+)', 'cityChName"

    for record in city_list["result"]:
        url = 'http://www.dianping.com/{city_name}/food'.format(
            city_name=record['city_name'])
        try:
            r = fetcher.get(url=url)
        except Exception as ex:
            msg = 'fetch content failed, %s, %s' % (ex, url)
            logger.warn(msg)
            time.sleep(random.random() * 1.5)
            continue

        if r.status_code != 200:
            msg = 'fetch content failed, http.code=%d, %s' % (
                r.status_code, url)
            logger.warn(msg)
            time.sleep(random.random() * 1.5)
            continue

        m = re.search(pattern, r.content, re.UNICODE)
        if not m:
            msg = 'parse city_id failed, %s' % url
            logger.warn(msg)
            continue

        record["id"] = int(m.group('city_id'))
        items.append(record)

        msg = "parse city name:%s id:%s" % (record["city_name"], record["id"])
        logger.debug(msg)

    items = sorted(items, key=lambda obj: obj["id"])
    result["result"] = items
    result["total"] = len(items)
    result["last_update"] = datetime.datetime.utcnow()

    save_to = os.path.join(path_data, "city_id_list.json")
    groper.store.Disk.save(save_to=save_to, content=result)


def get_city_list(path_data):
    save_to = os.path.join(path_data, "city_list.json")
    with open(save_to) as f:
        return json.loads(f.read())


def get_city_id_list(path_data):
    save_to = os.path.join(path_data, "city_id_list.json")
    with open(save_to) as f:
        return json.loads(f.read())

if __name__ == '__main__':
    import argparse

    PWD = os.path.dirname(os.path.realpath(__file__))
    save_to_parent = os.path.join(PWD, "data")

    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", help="destination folder of result", default=save_to_parent)
    args = parser.parse_args()
    if args.dest:
        main(args)
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

