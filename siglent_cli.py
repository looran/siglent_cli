#!/usr/bin/env python3

DESCRIPTION = "siglent_cli - Oscilloscope command-line screenshot/waveform download"
EXAMPLES = """"""

import argparse

import requests
import pyvisa

class Siglent(object):
    def __init__(self, ip):
        self.ip = ip
        rm = pyvisa.ResourceManager()
        self.sds = rm.open_resource("TCPIP::%s::INSTR" % self.ip)

    def dl_wf(self, filename):
        if not filename:
            filename = 'wf.bin'

        print("trigger waveform export")
        #don't use visa, easier instead of polling we just have to wait for the http request to finish
        #self.sds.write("WFDA?")
        r = requests.post('http://%s/device_read_write.php' % self.ip, data={
            "cmd": '{"cmd":"wfda?","type":"ds","to":"127.0.0.1"}',
            "action": "excutescpicmds"
        })
        if r.status_code != 200 or r.text.find('WFDA') < 0:
            raise Exception("error from oscilloscope [%d] %s" % (r.status_code, r.text))
        print('\n'.join(r.text.split('\\n')))

        print("fetching waveform file")
        r = requests.get('http://%s/web_img/usr_wf_data.bin' % self.ip)
        print("writing %d bytes to %s" % (len(r.content), filename))
        with open(filename, 'wb') as f:
            f.write(r.content)
        
    def dl_shot(self, filename):
        if not filename:
            filename = 'shot.jpg'
        print("capturing screenshot to %s" % filename)
        self.sds.write("SCDP")
        res = self.sds.read_raw()
        f = open(filename,'wb')
        f.write(res)
        f.flush()
        f.close()

    def dl_shot_vnc(self, filename):
        print("XXX this is known to crash the scope VNC server during captureScreen()")
        if not filename:
            filename = 'shot.jpg'
        print("capturing screenshot to %s" % filename)
        from vncdotool import api as vncdotool_api
        cli = vncdotool_api.connect(self.ip)
        cli.captureScreen(filename)
        cli.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EXAMPLES, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose')
    parser.add_argument('-f', '--filename', help='output filename')
    parser.add_argument('ip', help='ip address of the scope')
    parser.add_argument('action', choices=['shot', 'wf'], help='')

    args = parser.parse_args()

    s = Siglent(args.ip)
    if args.action == 'wf':
        s.dl_wf(args.filename)
    elif args.action == 'shot':
        s.dl_shot(args.filename)
