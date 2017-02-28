# -*- coding: utf-8 -*-
import sys, logging
import requests, json, base64
from os import path

# LOG = logging.getLogger(__name__)

K_PRE = "RMINFO_"
K_ENABLE = "RMINFO_ENABLE"

LOG_PATH = './param_agent.log'
NOVA_PATH = '/etc/nova/nova.conf'
CINDER_PATH = '/etc/cinder/cinder.conf'

def get_range_end():
    s = bytearray(K_PRE)
    s[-1] += 1
    return bytes(s)

def restart_nova_service():
    logging.warning("Configuration changed, restart nova services!!")

def handle_enable(v):
    logging.warning("%s: %s" % (K_ENABLE, v))
    # Nova, cinder
    with open(NOVA_PATH, 'r+') as f:
        content = f.read()
        f.seek(0)
        if v == 'TRUE':
            idx = content.find('image_clear')
            if idx == -1:
                cut = content.split('[libvirt]\n')
                cut[1] = 'image_clear = zero\n' + cut[1]
                f.write(''.join([cut[0], '[libvirt]\n', cut[1]]))
                restart_nova_service()
            else:
                idx_ = content.find('image_clear = none')
                if idx_ != -1:
                    content = content.replace('image_clear = none', 'image_clear = zero')
                    f.write(content)
                    restart_nova_service()
        else:
            idx = content.find('image_clear = zero')
            if idx != -1:
                content = content.replace('image_clear = zero', 'image_clear = none')
                f.write(content)
                restart_nova_service()
            else:
                idx_ = content.find('image_clear = shred')
                if idx_ != -1:
                    content = content.replace('image_clear = shred', 'image_clear = none')
                    f.write(content)
                    restart_nova_service()

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
    if len(sys.argv) < 2:
        logging.warning("""
        Usage: remain-info-agent.py $url [$log $nova $cinder]
        :param $url: The URL of etcd server
        :param $log: optional, the path of log file, -- means default
        :param $nova: optional, the path of nova configure file, -- means default
        :param $cinder: optional, the path of cinder configure file, -- means default
        """)
        sys.exit(1)

    if len(sys.argv) >= 3:
        LOG_PATH = sys.argv[2] if sys.argv[2] != '--' else LOG_PATH

    if len(sys.argv) >= 4:
        NOVA_PATH = sys.argv[3] if sys.argv[3] != '--' else NOVA_PATH

    if len(sys.argv) >= 5:
        CINDER_PATH = sys.argv[4] if sys.argv[4] != '--' else CINDER_PATH

    if not path.exists(NOVA_PATH) or not path.exists(CINDER_PATH):
        logging.warning("Configure file not exists!")
        sys.exit(1)

    start_watch(sys.argv[1])

