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
from datetime import datetime
import time
import json
from microdot.microdot import Microdot, Response, send_file
from render_pages import render_ap_cfg, render_confirm_cfg
import my_configuration as my_c

app_debug = my_c.app_debug
app_debug = True
script_dbg = my_c.script_debug
errors = []
wifi_json = {}
Response.default_content_type = 'text/html'

# FIXME
#def s_print(text):
#    # ct = time.localtime()
#    # ft = '{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(ct[0],ct[1],ct[2],ct[3],ct[4],ct[5])
#    lyne = '{:%H:%M:%S}:'.format(datetime.now()) + str(text)
#    print(lyne, flush=True)

def s_print(text):
    lyne = '{:%H:%M:%S}:'.format(datetime.now()) + str(text) + "\n"
    with open(topdir + '/python.log', 'a') as f:
        f.write(lyne)

def parse_ap_cfg(creds, wifi_json):
    # use wifi_json dict for variables
    global errors
    app_debug and s_print(f'Parse_ap_cfg: errors [{errors}]')
    errors = []
    app_debug and s_print(f'Parse_ap_cfg: incoming wifi_json [{wifi_json}]')
    # FIXME - maybe clear these based on errors?
    wifi_json['wifi_pass'] = wifi_json['preferred_ip'] = None
    wifi_json['ssid'] = creds['ssid']
    if 'wifi_pass' in creds:
        wifi_json['wifi_pass'] = creds['wifi_pass'].strip()
#    else:
#        errors.append('a password is required')
    print(f"creds [{creds}]")
    if creds['preferred_ip']:
        wifi_json['preferred_ip'] = creds['preferred_ip'].strip()
        int_ip = int(creds['preferred_ip'].strip())
        if int_ip >= my_c.wifi_static_ip['low'] and int_ip <= my_c.wifi_static_ip['high']:
            wifi_json["preferred_ip"] = int_ip
        else:
            errors.append(f"preferred ip must be between {my_c.wifi_static_ip['low']} and {my_c.wifi_static_ip['high']}")
            wifi_json["preferred_ip"] = ""

    app_debug and s_print(f'Parse_ap_cfg: wifi_json [{wifi_json}]')

#    app_debug and s_print('Parse_ap_cfg: would create WiFi entry with password')
#    wifi_json = connect_to_wifi(wifi_json) 
#    app_debug and s_print(f'Parse_ap_cfg: Connect_to_wifi result is [{wifi_json}]')
#    # read the errors and try to provide a simple message
#
#    if 'stderr' in wifi_json:
#        buf = io.StringIO(wifi_json.pop('stderr'))
#        with open(wifi_errs_file, 'w') as f:
#            f.writelines(buf)
#    else:
#        with open(wifi_json_file, 'w') as f:
#            json.dump(wifi_json, f)

    return(wifi_json)

def confirm_wifi(wifi_json):
    shell_script = Path(f'/tmp/wifi-conf.{str(os.getpid())}')
    password = wifi_json['wifi_pass']
    ssid = wifi_json['ssid']
    hotspot = wifi_json['hotspot_name']
    preferred_ip = wifi_json['preferred_ip']
    brace = '{'
    ecarb = '}'

    # at this point, we have set a preferred ip so
    # we should come up on the preferred ip. Use ifconfig to check
    with open(shell_script, 'w') as s_s:
        s_s.write(f'''#!/usr/bin/bash
try_eval()
{brace}
    $(eval "$1" >$out 2>$err)
    rc=$?
    if [ $rc -eq 0 ] ; then
        [ -f $out ] && cat $out
    else
        [ -f $err ] && cat $err
    fi
    rm $out $err >/dev/null 2>&1
    return $rc
{ecarb}
# allow blanks in strings
ssid="{ssid}"
hotspot="{hotspot}"
password="{password}"
preferred_ip={preferred_ip}
topdir={topdir}
this=$(basename $0)
out="/tmp/$this.$$.out"
err="/tmp/$this.$$.err"
rc=
log=$topdir/nmcli.log
application_ssid_file=$topdir/data/application_ssid
echo "logging to $log" | tee $log
# rescan here. If too much time has passed, nmcli "forgets"
# nmcli device wifi >/dev/null 2>&1
nmcli device wifi > $log 2>&1
eval "nmcli device wifi connect \\"$ssid\\" password \\"$password\\" >> $log"
if [ $? -ne 0 ] ; then
    echo "Can't connect to \"$ssid\" using password" >&2
    rc=1
    # try the Trixie command
    eval "nmcli connection up \\"$ssid\\""
    if [ $? -ne 0 ] ; then
        echo "Can't bring $ssid connection up" >&2
        rc=1
    else
        echo "Brought up connection $ssid" >&2
        rc=
    fi
else
    echo "Connected to $ssid using password" >&2
    rc=
fi
echo "After nmcli connect, rc is $rc" >> $log
[ "$rc" ] && exit $rc

# ssid is up, update the application_ssid file for systemd on subsequent boots
echo $ssid > $application_ssid_file
                  
ip_mask=$(try_eval "nmcli -g IP4.ADDRESS connection show \\"$ssid\\" ")
full_ip=$(echo $ip_mask | cut -d/ -f1)
subnet_mask=$(echo $ip_mask | cut -d/ -f2)

if [ "$preferred_ip" ] ; then
   # what's our ipv4 address?
   network=$(echo $full_ip | cut -d. -f-3)
   full_preferred_ip=$network.$preferred_ip
   # do we have our preferred ip?
   ifconfig -a | grep inet | grep $full_preferred_ip >/dev/null 2>&1
   if [ $? -eq 0 ] ; then
      # we have our ip
      echo "IP=$full_preferred_ip"
      rc=0
   else
      echo "Preferred IP is in use $full_preferred_ip" >&2
      rc=1
   fi
else
   echo "DHCP=$full_ip"
   rc=0
fi
if [ "$rc" = "1" ] ; then
   echo "nmcli down \"$ssid\" - rc is 1" >> $log
   eval "nmcli connection down \\"$ssid.\\""
   echo "nmcli up $hotspot - rc is 1" >> $log
   eval "nmcli connection up \\"$hotspot\\""
else
   echo "nmcli modify \"$ssid\" >> $log
   # setting pipefail provides the return code of the pipe command
   set -o pipefail
   eval "nmcli connection modify \\"$ssid\\" ipv6.method disabled 2>&1 | tee -a $log"
   rc=$?
   set +o pipefail
   if [ "$rc" = "0" ] ; then
      echo "modify $ssid ipv6.method succeeded" >> $log
   else
      echo "modify $ssid ipv6.method failed with rc $rc" >> $log
      exit $rc
   fi
   # [ "$rc" = "0" ] || exit $rc
   echo "nmcli down $ssid" >> $log
   set -o pipefail
   eval "nmcli connection down \\"$ssid\\" 2>&1 | tee -a $log"
   rc=$?
   set +o pipefail
   if [ "$rc" = "0" ] ; then
      echo "nmcli connection down $ssid succeeded" >> $log
   else
      echo "nmcli connection down $ssid failed with rc $rc" >> $log
      exit $rc
   fi
   # [ "$rc" = "0" ] || exit $rc
   echo "nmcli up $ssid" >> $log
   set -o pipefail
   eval "nmcli connection up \\"$ssid\\" 2>&1 | tee -a $log"
   rc=$?
   set +o pipefail
   if [ "$rc" = "0" ] ; then
      echo "nmcli connection up $ssid succeeded" >> $log
   else
      echo "nmcli connection up $ssid failed with rc $rc" >> $log
      exit $rc
   fi
   # [ "$rc" = "0" ] || exit $rc
fi
exit $rc
'''
                 )

    cmd = ['bash', f'{shell_script}']
    # s_print(f'cmd is [{cmd}]')
    try:
        rc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        s_print(f'error is [{e}]')
        rc = e

    script_dbg and s_print(f'Confirm_wifi:rc is [{rc}]')
    script_dbg and s_print(f'Confirm_wifi:rc.returncode is [{rc.returncode}]')
    script_dbg and s_print(f'Confirm_wifi:rc.args is [{rc.args}]')
    # stdout/stderr are type str
    script_dbg and s_print(f'Confirm_wifi:rc.stdout is [{rc.stdout.strip()}]')
    script_dbg and s_print(f'Confirm_wifi:rc.stderr is [{rc.stderr.strip()}]')
    if rc.stderr:
        wifi_json['stderr'] = rc.stderr.strip()
    elif rc.stdout:
        buf = io.StringIO(rc.stdout)
        while True:
            lyne = buf.readline().strip()
            script_dbg and s_print(f'Confirm_wifi:lyne [{lyne}]')
            if not lyne:
                break
            if 'IP' in lyne:
                wifi_json['IP'] = lyne.split('=')[1]
            elif 'DHCP' in lyne:
                wifi_json['DHCP'] = lyne.split('=')[1]
            elif 'Connection successfully activated' in lyne:
                script_dbg and s_print('Confirm_wifi:saw "Connection successfully activated", set wifi_json[state] = up')
                wifi_json['state'] = 'up'

    # FIXME shell_script.unlink()
    return wifi_json

def wifi_rescan(wifi_json):
    '''
    rescan
    '''
    shell_script = Path(f'/tmp/wifi-scan.{str(os.getpid())}')
    brace = '{'
    ecarb = '}'
    hotspot_name = wifi_json['hotspot_name']

    with open(shell_script, 'w') as s_s:
        s_s.write(f'''#!/usr/bin/bash
topdir={topdir}
hotspot_name="{hotspot_name}"
json="{brace} \\"hotspot_name\\": \\"$hotspot_name\\", \\"preferred_ip\\": \\"\\", \\"access_points\\": ["
# set IFS to nl to prevent word split on silly hotspot names
IFS='
'
for line in $(nmcli --terse device wifi list | cut -d: -f8,12)
do
   ap=$(echo $line|cut -d: -f1)
   # lose non-numerics if they turn up in field 12
   stren=$(echo $line|cut -d: -f2|sed 's/[^0-9]*//g')
   [ "$stren" ] || stren=0 # this will drop aps with non-numeric strength
   # arb choice of 45 to weed out weak aps
   # in office, home networks are < 45
   if [ $stren -gt 45 ] ; then
      json="$json \\"$ap\\","
   fi
done
unset IFS
json=$(echo $json | sed 's/,$/]{ecarb}/')
echo $json > $topdir/data/wifi.json
exit 0
'''
                 )
    cmd = ['bash', f'{shell_script}']
    # s_print(f'cmd is [{cmd}]')
    try:
        rc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        s_print(f'error is [{e}]')
        rc = e

    script_dbg and s_print(f'Rescan_wifi:rc is [{rc}]')
    script_dbg and s_print(f'Rescan_wifi:rc.returncode is [{rc.returncode}]')
    script_dbg and s_print(f'Rescan_wifi:rc.args is [{rc.args}]')
    # stdout/stderr are type str
    script_dbg and s_print(f'Rescan_wifi:rc.stdout is [{rc.stdout.strip()}]')
    script_dbg and s_print(f'Rescan_wifi:rc.stderr is [{rc.stderr.strip()}]')
    if rc.stderr:
        wifi_json['stderr'] = rc.stderr.strip()
    elif rc.stdout:
        buf = io.StringIO(rc.stdout)
        while True:
            lyne = buf.readline().strip()
            script_dbg and s_print(f'Rescan_wifi:lyne [{lyne}]')
            if not lyne:
                break

    wifi_json = {}
    # FIXME shell_script.unlink()
    return wifi_json

def connect_to_wifi(wifi_json):
    '''
    Have to connect to the named ssid and collect the DHCP IP
    Then, if there's a preferred IP, test ping it
    Then return either the DHCP IP or the full preferred IP
    If there's a configured nmconnection on entry, remove it
    '''
    shell_script = Path(f'/tmp/wifi-conn.{str(os.getpid())}')
    password = wifi_json['wifi_pass']
    ssid = wifi_json['ssid']
    hotspot = wifi_json['hotspot_name']
    preferred_ip = wifi_json['preferred_ip']
    # this required to avoid escape hell or inability to escape
    brace = '{'
    ecarb = '}'

    with open(shell_script, 'w') as s_s:
        s_s.write(f'''#!/usr/bin/bash
try_eval()
{brace}
    $(eval "$1" >$out 2>$err)
    rc=$?
    if [ $rc -eq 0 ] ; then
        [ -f $out ] && cat $out
    else
        [ -f $err ] && cat $err
    fi
    rm $out $err >/dev/null 2>&1
    return $rc
{ecarb}
# allow blanks in ssid and password
ssid="{ssid}"
hotspot="{hotspot}"
password="{password}"
preferred_ip={preferred_ip}
this=$(basename $0)
out="/tmp/$this.$$.out"
err="/tmp/$this.$$.err"
tries=3
try=1
# clear an existing ssid entry - avoid possible "IP in use" error
# which could happen if the user quits from the confirmation page
eval "nmcli connection delete \\"$ssid\\" >/dev/null 2>&1"
# refresh the list of available networks
# otherwise we could fail to connect
nmcli device wifi >/dev/null 2>&1
while [ $try -le $tries ] ;
do
    result=$(try_eval "nmcli device wifi connect \\"$ssid\\" password \\"$password\\"")
    rc=$?
    if [ $rc -ne 0 ] ; then
        # echo "$try Connect to $ssid failed with error [$result]" >&2
        sleep 5
    else
        echo "PASS:Connected to $ssid"
        break
    fi
    try=$(($try+1))
done
if [ $try -ge $tries ] ; then
    # echo "FAIL:Can't connect to $ssid, error [$error], rc $rc" >&2
    # error message for wrong password is confusing 
    # "secrets were required but not provided..." - simplify
    error=$(echo $result | sed 's/Error: //')
    echo $error | grep -wE 'required|provided' >/dev/null && error="Wrong password"
    echo "FAIL:Can't connect to $ssid, $error" >&2
    # whack any nmcli entry
    eval "nmcli connection delete \\"$ssid\\" >/dev/null 2>&1"
    exit 1
fi

ip_mask=$(try_eval "nmcli -g IP4.ADDRESS connection show \\"$ssid\\" ")
full_ip=$(echo $ip_mask | cut -d/ -f1)
subnet_mask=$(echo $ip_mask | cut -d/ -f2)

if [ "$preferred_ip" ] ; then
   # what's our ipv4 address?
   network=$(echo $full_ip | cut -d. -f-3)
   full_preferred_ip=$network.$preferred_ip
   # should/shouldn't iterate here until we get a free IP?
   ping -c 3 $full_preferred_ip >/dev/null 2>&1
   if [ $? -ne 0 ] ; then
       # ip is available
       eval "nmcli connection modify --temporary \\"$ssid\\" +ipv4.address $full_preferred_ip/$subnet_mask"
       if [ $? -ne 0 ] ; then
           echo "Can't configure $full_preferred_ip on $ssid" >&2
           # whack any nmcli entry
           eval "nmcli connection delete \\"$ssid\\" >/dev/null 2>&1"
           exit 1
       fi
       echo "IP=$full_preferred_ip"
    else
       echo "Preferred IP is in use $full_preferred_ip" >&2
       # whack any nmcli entry
       eval "nmcli connection delete \\"$ssid\\" >/dev/null 2>&1"
       exit 1
   fi
else
   echo "DHCP=$full_ip"
fi
# try to lose IPv6
eval "nmcli connection modify \\"$ssid\\" ipv6.method disabled"
# FIXME - error checks?
eval "nmcli connection down \\"$ssid\\""
# [ $? -ne 0 ] && echo "Problem disabling $ssid, reboot and try again" >&2
# but bringing up the hotspot should take the ssid down
result=$(try_eval "nmcli connection up \\"$hotspot\\"")
if [ $? -ne 0 ] ; then
    echo "$result" >&2
    exit 1
fi
exit 0
'''
                 )

    cmd = ['bash', f'{shell_script}']
    script_dbg and s_print(f'cmd is [{cmd}]')
    try:
        rc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        s_print(f'error is [{e}]')
        rc = e

    script_dbg and s_print(f'rc is [{rc}]')
    script_dbg and s_print(f'rc.returncode is [{rc.returncode}]')
    wifi_json['rc'] = rc.returncode
    script_dbg and s_print(f'rc.args is [{rc.args}]')
    # stdout/stderr are type str
    script_dbg and s_print(f'rc.stdout is [{rc.stdout.strip()}]')
    script_dbg and s_print(f'rc.stderr is [{rc.stderr.strip()}]')
    if rc.stderr:
        # default - all errors
        wifi_json['stderr'] = rc.stderr.strip()
        # a selective error
#        for line in rc.stderr.splitlines():
#            script_dbg and s_print(f'stderr line [{line}]')
#            if 'required, but not provided' in line:    # "Secrets required, but not provided"
#                wifi_json['stderr'] = f'Wrong password for {ssid}'
#                break
    elif rc.stdout:
        buf = io.StringIO(rc.stdout)
        while True:
            lyne = buf.readline().strip()
            s_print(f'lyne is [{lyne}]')
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

    # FIXME shell_script.unlink()
    return wifi_json

def run_webserver():
    app_debug and s_print('Run webserver')
    app = Microdot()
    wifi_json = {}

    open(wifi_errs_file, 'w').close()

    @app.route('/', methods=['GET', 'POST'])
    @app.route('/index', methods=['GET', 'POST'])
    @app.route('/configure', methods=['GET','POST'])

    async def ap(request):
        global wifi_json, errors
        app_debug = True
        # read preferred ip and list of SSIDs created by systemd shell script
        app_debug and s_print(f'request.form [{request.form}]')
        if not 'wifi_json' in locals():
            app_debug and s_print('Ap: read wifi_json from disk')
            with open(wifi_json_file, 'r') as f:
                wifi_json = json.load(f)

        # FIXME
        # issue where pi was started ahead of router and did not successfully connect, but created NetworkManager entry
        # subsequent restarts caused logic problems
        # check for network connections?

        app_debug and s_print(f'Ap: wifi_json is [{wifi_json}]')
        if not request.form and not 'IP' in wifi_json and not 'DHCP' in wifi_json:
            # make sure we start with the correct form, not a leftover
            errors = []
            render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)
        elif request.form:
            creds = request.form
            # we are processing 2 different forms: ap_cfg or confirm_cfg
            # config choices, ssid/hotspot confirmation
            app_debug and s_print(f'Ap: creds are [{creds}]')
            if 'quit' in creds:
                app_debug and s_print(f'Ap: quit/rescan [{wifi_json}]')
                # redisplay the base config file (maybe with base wifi_json and no errors?)
                render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)
                return send_file(f'{ap_cfg_html_file}')
            elif 'rescan' in creds:
                app_debug and s_print(f'Ap: rescan [{wifi_json}]')
                errors = []
                open(wifi_errs_file, 'w').close()
                wifi_rescan(wifi_json)
                with open(wifi_json_file, 'r') as f:
                    wifi_json = json.load(f)
                render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)
                return send_file(f'{ap_cfg_html_file}')
            elif 'confirm_wifi' in creds:
                app_debug and s_print('Ap: process wifi confirmation')
                wifi_json = confirm_wifi(wifi_json)
                app_debug and s_print(f'Ap: Confirm_wifi [{wifi_json}]')
                app_debug and s_print(f'Ap: Confirm_wifi - remove {wifi_json_file}')
                # or selectively delete from wifi_json?
                Path(wifi_json_file).unlink(missing_ok = True) 
                open(wifi_errs_file, 'w').close()
                app_debug and s_print('Ap: Confirm_wifi - stop the config webserver')
                # shutdown the web server
                request.app.shutdown()
                app_debug and s_print('Ap: Confirm_wifi - success. Start the app')
                cmd = [ f'{topdir}/start_application', f'{topdir}']
                try:
                    rc = subprocess.run(cmd, capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError as e:
                    s_print(f'error is [{e}]')
                    rc = e

                app_debug and s_print(f'rc is [{rc}]')
                app_debug and s_print(f'rc.returncode is [{rc.returncode}]')
                app_debug and s_print(f'rc.args is [{rc.args}]')
                # stdout/stderr are type str
                app_debug and s_print(f'rc.stdout is [{rc.stdout.strip()}]')
                app_debug and s_print(f'rc.stderr is [{rc.stderr.strip()}]')

                sys.exit(0)

            else:
                # parse the render_ap_cfg form
                app_debug and s_print('Ap: parse ap cfg')
                wifi_json = parse_ap_cfg(creds, wifi_json)
                if errors:
                    render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)
                    return send_file(f'{ap_cfg_html_file}')
                # test connect to the ssid
                app_debug and s_print('Parse_ap_cfg: would create WiFi entry with password')
                wifi_json = connect_to_wifi(wifi_json) 
                app_debug and s_print(f'Parse_ap_cfg: Connect_to_wifi result is [{wifi_json}]')
                # read the errors and try to provide a simple message

                if 'stderr' in wifi_json:
                    buf = io.StringIO(wifi_json.pop('stderr'))
                    with open(wifi_errs_file, 'w') as f:
                        f.writelines(buf)
                else:
                    with open(wifi_json_file, 'w') as f:
                        json.dump(wifi_json, f)
                
            app_debug and s_print(f'Ap: WHAT TO DO, wifi_json is [{wifi_json}], errors are [{errors}]')
            if errors:  # render the errors
                # FIXME - maybe parse the errors and distill them to something meaningful?
                render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)
                return send_file(f'{ap_cfg_html_file}')

            if 'IP' in wifi_json or 'DHCP' in wifi_json:
                app_debug and s_print(f'Ap: call Render_confirm_cfg, wifi_json is [{wifi_json}]')
                # app_debug and s_print(f'Ap: render_confirm_cfg - remove {wifi_json_file}')
                # Path(wifi_json_file).unlink(missing_ok = True) 
                render_confirm_cfg(ap_cfg_html_file, wifi_json, errors)
            else: 
                app_debug and s_print('Ap: call Render_ap_cfg')
                app_debug and s_print(f'with errors [{errors}]')
                if errors:
                    # Fresh errors, clear the error file which is read by Render_ap_cfg
                    open(wifi_errs_file, 'w').close()
                render_ap_cfg(ap_cfg_html_file, wifi_errs_file, wifi_json, errors)

        return send_file(f'{ap_cfg_html_file}')

    app_debug and s_print(f'Run_server: time is {time.time()}, {time.localtime()}')
    app_debug and s_print('Run_server: run Microdot as_task')
    # we are running as root so we can use port 80
    try:
        app.run(port=80, debug=False)
    except OSError as exc:
        if exc.errno == 98:     # address in use
            return

    app_debug and s_print('Run_server: why here?')
    # TODO - clear the json file here?
    # Path(my_c.wifi_json_file).unlink(missing_ok = True) 

# initialization and startup
topdir = sys.argv[1]
s_print(f'Main: incoming args [{sys.argv}]')
s_print(f'Main: topdir [{topdir}]')
wifi_errs_file = topdir + '/data/' + my_c.wifi_errs_file
wifi_json_file = topdir + '/data/' + my_c.wifi_json_file
ap_cfg_html_file = topdir + '/hotspot/templates/' + my_c.ap_cfg_html_file

s_print(f'Main: wifi_errs_file [{wifi_errs_file}]')
s_print(f'Main: wifi_json_file [{wifi_json_file}]')
s_print(f'Main: ap_cfg_html_file [{ap_cfg_html_file}]')

my_pid=str(os.getpid())

try:
    run_webserver()
except SystemExit:
    s_print('Bye')
except Exception as e:
    s_print(f'Run_server: exception [{e}]')
