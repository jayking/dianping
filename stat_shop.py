#coding:utf8
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

import lxml.etree
import bs4
import helper_string
import groper.fetcher
import groper.cfg
import city_id_list

logger = logging.getLogger(__name__)
logger.addHandler(groper.cfg.log_hdl_steam)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)



def parse_result(content):
    max_total = 0
    for line in content["msg"]["shop"]:
        result = re.search(pattern=u"约(?P<total>\d+)个结果", string=line, flags=re.UNICODE)
        if result:
            total = int(result.group("total"))
            if total > max_total:
                max_total = total
    return max_total

def main(args):
    path_data = helper_string.HelperString.to_uni(args.dest)
    keyword = helper_string.HelperString.to_uni(args.key)

    fetcher = groper.fetcher.Fetcher(cfg=groper.cfg)
    DP_OK = 101

    result = dict(
        keyword=keyword,
        result=[],
        total=0,
        last_update=None,
    )
    items = []

    for record in city_id_list.get_city_id_list(path_data=path_data)["result"]:
        city_id = record["id"]
        url = u'http://www.dianping.com/ajax/json/suggest/search?do=hsc&c={city_id}&s=30&q={keyword}'.format(
            city_id=city_id,
            keyword=keyword,
        )
        r = fetcher.get(url=url)
        if r.status_code != 200:
            msg = u'fetch content failed, %s' % url
            logger.warn(msg)
            continue

        content = r.json()
        if content["code"] != DP_OK:
            msg = u'expected code=%s(ok), got %s' % (DP_OK, content["code"])
            logger.warn(msg)
            continue

        total = parse_result(content)
        msg = u"%s %s" % (record["city_name"], total)
        logger.debug(msg)

        if not total:
            continue

        record["total"] = total
        items.append(record)

    result["result"] = sorted(items, key=lambda obj: obj["total"], reverse=True)    
    result["total"] = len(items)
    result["last_update"] = datetime.datetime.utcnow()

    save_to = os.path.join(path_data, u"stat_shop.{keyword}.json".format(keyword=keyword))
    groper.store.Disk.save(save_to=save_to, content=result)


if __name__ == '__main__':
    import argparse

    PWD = os.path.dirname(os.path.realpath(__file__))
    save_to_parent = os.path.join(PWD, "data")

    parser = argparse.ArgumentParser()
    parser.add_argument("--key", help="stat shops by keyword")
    parser.add_argument("--dest", help="path to folder data", default=save_to_parent)
    args = parser.parse_args()
    if args.key and args.dest:
        main(args)
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

    