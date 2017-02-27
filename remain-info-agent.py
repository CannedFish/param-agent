# -*- coding: utf-8 -*-
import sys, logging
import requests, json, base64

# LOG = logging.getLogger(__name__)

K_PRE = "RMINFO_"
K_ENABLE = "RMINFO_ENABLE"

def get_range_end():
    s = bytearray(K_PRE)
    s[-1] += 1
    return bytes(s)

def handle_enable(v):
    logging.warning("%s: %s" % (K_ENABLE, v))
    # Nova, cinder

def start_watch(url):
    logging.warning(url)
    k_pre = base64.b64encode(K_PRE)
    k_range_end = base64.b64encode(get_range_end())
    res = requests.post('http://%s/v3alpha/watch' % url, \
            data=json.dumps({'create_request': {'key': k_pre, 'range_end': k_range_end}}), \
            stream=True)

    for line in res.iter_lines():
        logging.warning(line)
        line = json.loads(line)
        if line['result'].has_key('events'):
            evts = line['result']['events']
            for evt in evts:
                key = base64.b64decode(evt['kv']['key'])
                if key == K_ENABLE:
                    handle_enable(base64.b64decode(evt['kv']['value']))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logging.warning("""
        Usage: remain-info-agent.py $url
        :param $url: The URL of etcd server
        """)
        sys.exit(1)

    start_watch(sys.argv[1])

