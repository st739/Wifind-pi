#!/bin/env python3
'''
    Run when in hotspot mode to allow basic configuration
    display available SSIDs and allow connection to one
    no operational hotspot mode because of the difficulty of recovering from a lost hotspot password
    default hotspot will be invoked if a SSID was successfully defined, but has since changed or been removed
    in this case, clear the SSID definition
'''
import sys
import os
import io
import asyncio
import subprocess
from pathlib import Path
import json
from microdot.microdot import Microdot, Response, send_file
from render_pages import render_ap_cfg, render_confirm_cfg
import my_configuration as my_c

errors = []
wifi_json = {}
Response.default_content_type = 'text/html'

def parse_ap_cfg(creds, wifi_json):
    global errors
    errors = []
    wifi_json['wifi_pass'] = wifi_json['preferred_ip'] = None
    wifi_json['ssid'] = creds['ssid']
    if 'wifi_pass' in creds:
        wifi_json['wifi_pass'] = creds['wifi_pass'].strip()
    if creds['preferred_ip']:
        wifi_json['preferred_ip'] = creds['preferred_ip'].strip()
        int_ip = int(creds['preferred_ip'].strip())
        if int_ip >= my_c.wifi_static_ip['low'] and int_ip <= my_c.wifi_static_ip['high']:
            wifi_json["preferred_ip"] = int_ip
        else:
            errors.append(f"preferred ip must be between {my_c.wifi_static_ip['low']} and {my_c.wifi_static_ip['high']}")
            wifi_json["preferred_ip"] = ""
    return(wifi_json)

def confirm_wifi(wifi_json):
    shell_script = Path(f'{topdir}/hotspot/scripts/wifi-conf')
    password = wifi_json['wifi_pass']
    ssid = wifi_json['ssid']
    hotspot = wifi_json['hotspot_name']
    preferred_ip = wifi_json['preferred_ip']

    cmd = ['bash', f'{shell_script}', f'{ssid}', f'{password}',
           f'{hotspot}', f'{preferred_ip}']
    try:
        rc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        rc = e

    if rc.stderr:
        wifi_json['stderr'] = rc.stderr.strip()
    elif rc.stdout:
        buf = io.StringIO(rc.stdout)
        while True:
            lyne = buf.readline().strip()
            if not lyne:
                break
            if 'IP' in lyne:
                wifi_json['IP'] = lyne.split('=')[1]
            elif 'DHCP' in lyne:
                wifi_json['DHCP'] = lyne.split('=')[1]
            elif 'Connection successfully activated' in lyne:
                wifi_json['state'] = 'up'

    return wifi_json

def wifi_rescan(wifi_json):
    '''
    rescan
    '''
    shell_script = Path(f'{topdir}/hotspot/scripts/wifi-scan')
    hotspot_name = wifi_json['hotspot_name']

    cmd = ['bash', f'{shell_script}', f'{hotspot_name}']
    try:
        rc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        rc = e

    if rc.stderr:
        wifi_json['stderr'] = rc.stderr.strip()
    elif rc.stdout:
        buf = io.StringIO(rc.stdout)
        while True:
            lyne = buf.readline().strip()
            if not lyne:
                break

    wifi_json = {}
    return wifi_json

def connect_to_wifi(wifi_json):
    '''
    Have to connect to the named ssid and collect the DHCP IP
    Then, if there's a preferred IP, test ping it
    Then return either the DHCP IP or the full preferred IP
    If there's a configured nmconnection on entry, remove it
    '''
    shell_script = Path(f'{topdir}/hotspot/scripts/wifi-conn')
    password = wifi_json['wifi_pass']
    ssid = wifi_json['ssid']
    hotspot = wifi_json['hotspot_name']
    preferred_ip = wifi_json['preferred_ip']

    cmd = ['bash', f'{shell_script}', f'{ssid}', f'{password}', f'{preferred_ip}', f'{hotspot}']
    try:
        rc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        rc = e

    wifi_json['rc'] = rc.returncode
    if rc.stderr:
        # default - all errors
        wifi_json['stderr'] = rc.stderr.strip()
    elif rc.stdout:
        buf = io.StringIO(rc.stdout)
        while True:
            lyne = buf.readline().strip()
            if not lyne:
                break
            if 'IP' in lyne:
                wifi_json['IP'] = lyne.split('=')[1]
                # TEST
                wifi_json['state'] = 'up'
            elif 'DHCP' in lyne:
                wifi_json['DHCP'] = lyne.split('=')[1]
                # TEST
                wifi_json['state'] = 'up'

    return wifi_json

def run_webserver():
    app = Microdot()
    wifi_json = {}

    open(wifi_errs_file, 'w').close()

    @app.route('/', methods=['GET', 'POST'])
    @app.route('/index', methods=['GET', 'POST'])
    @app.route('/configure', methods=['GET','POST'])

    async def ap(request):
        global wifi_json, errors
        # read preferred ip and list of SSIDs created by systemd shell script
        if not 'wifi_json' in locals():
            with open(wifi_json_file, 'r') as f:
                wifi_json = json.load(f)

        if not request.form and not 'IP' in wifi_json and not 'DHCP' in wifi_json:
            # make sure we start with the correct form, not a leftover
            errors = []
            render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)
        elif request.form:
            creds = request.form
            # we are processing 2 different forms: ap_cfg or confirm_cfg
            # config choices, ssid/hotspot confirmation
            if 'quit' in creds:
                # redisplay the base config file
                open(wifi_errs_file, 'w').close()
                render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)
                return send_file(f'{ap_cfg_html_file}')
            elif 'rescan' in creds:
                errors = []
                open(wifi_errs_file, 'w').close()
                wifi_rescan(wifi_json)
                with open(wifi_json_file, 'r') as f:
                    wifi_json = json.load(f)
                render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)
                return send_file(f'{ap_cfg_html_file}')
            elif 'confirm_wifi' in creds:
                wifi_json = confirm_wifi(wifi_json)
                Path(wifi_json_file).unlink(missing_ok = True) 
                open(wifi_errs_file, 'w').close()
                # shutdown the web server
                request.app.shutdown()
                cmd = [ f'{topdir}/start_application', f'{topdir}']
                try:
                    rc = subprocess.run(cmd, capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError as e:
                    rc = e
                sys.exit(0)

            else:
                wifi_json = parse_ap_cfg(creds, wifi_json)
                if errors:
                    render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)
                    return send_file(f'{ap_cfg_html_file}')
                # test connect to the ssid
                wifi_json = connect_to_wifi(wifi_json) 
                # read the errors and try to provide a simple message

                if 'stderr' in wifi_json:
                    buf = io.StringIO(wifi_json.pop('stderr'))
                    with open(wifi_errs_file, 'w') as f:
                        f.writelines(buf)
                else:
                    with open(wifi_json_file, 'w') as f:
                        json.dump(wifi_json, f)
                
            if errors:  # render the errors
                render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)
                return send_file(f'{ap_cfg_html_file}')

            if 'IP' in wifi_json or 'DHCP' in wifi_json:
                render_confirm_cfg(ap_cfg_html_file, wifi_json, errors)
            else: 
                if errors:
                    # Fresh errors, clear the error file
                    open(wifi_errs_file, 'w').close()
                render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)

        return send_file(f'{ap_cfg_html_file}')

    # we are running as root so we can use port 80
    try:
        app.run(port=80, debug=False)
    except OSError as exc:
        if exc.errno == 98:     # address in use
            return

# initialization and startup
topdir = sys.argv[1]
wifi_errs_file = topdir + '/data/' + my_c.wifi_errs_file
wifi_json_file = topdir + '/data/' + my_c.wifi_json_file
ap_cfg_html_file = topdir + '/hotspot/templates/' + my_c.ap_cfg_html_file
my_pid=str(os.getpid())

try:
    run_webserver()
except SystemExit:
    print('Bye')
except Exception as e:
    pass
