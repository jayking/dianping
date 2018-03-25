import logging
import datetime
import json
import os
import sys
import time
import random
import re
import httplib
import uuid

import helper_string
import lxml.etree
import bs4
import groper.fetcher
import groper.parser.html
import groper.cfg
import groper.store

logger = logging.getLogger(__name__)
logger.addHandler(groper.cfg.log_hdl_steam)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)


def main(args):
    path_data = helper_string.HelperString.to_uni(args.dest)

    fetcher = groper.fetcher.Fetcher(cfg=groper.cfg)

    url = 'http://www.dianping.com/citylist'
    r = fetcher.get(url=url)
    if r.status_code != 200:
        msg = 'fetch content failed, http.code=%d, %s' % (
            r.status_code, url)
        logger.warn(msg)
        return

    result = dict(
        result=[],
        total=0,
        last_update=None,
    )
    items = []

    dom = groper.parser.html.HTMLParser.str_to_dom(r.content)
    xpath = '//a[contains(@class, "onecity")]'
    for e in dom.xpath(xpath):
        url = e.attrib["href"]
        if not e.text:
            continue

        city_name_cn = e.text.strip()
        city_name = url.split('/')[-1].strip()
        url = e.attrib["href"]

        if not url.startswith("http"):
            # "//www.dianping..." => "http://www.dianping..."
            url = "http" + url

        record = dict(
            city_name=city_name.encode('utf8'),
            city_name_cn=city_name_cn.encode('utf8'),
            url=url.encode('utf8'),
        )
        items.append(record)

    result["result"] = sorted(items, key=lambda obj: obj["city_name"])
    result["total"] = len(items)
    result["last_update"] = datetime.datetime.utcnow()

    save_to = os.path.join(path_data, "city_list.json")
    groper.store.Disk.save(save_to=save_to, content=result, auto_sort=False)


if __name__ == '__main__':
    import argparse

    PWD = os.path.dirname(os.path.realpath(__file__))
    save_to_parent = os.path.join(PWD, "data")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dest", help="destination folder of result", default=save_to_parent)
    args = parser.parse_args()
    if args.dest:
        main(args)
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)
