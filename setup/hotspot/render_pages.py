'''
    render web pages for initial hotspot setup
'''

import my_configuration as my_c

def render_confirm_cfg(ap_cfg_html_file, ap_json, errors):
    with open(ap_cfg_html_file, 'w') as html_file:
        html_file.write(f'{my_c.html_doctype}')
        html_file.write('<style>')
        html_file.write(f'{my_c.header_css}')
        html_file.write('li { text-align: left ; color: red ; }')
        html_file.write('p { text-align: left ; }')
        html_file.write('</style></head>')
        html_file.write(f'{my_c.standard_header}')
        if errors:
            html_file.write('<title>Connection Failure</title><body><h1>Connection Failure</h1><form action="" method="post" enctype="text/html" novalidate>')
            html_line = '<ul>'
            for error in errors:
                html_line += f'<li>{error}</li>'
            html_line += '</ul>'
            html_file.write(html_line)
            html_file.write('<p>Reboot to try again.</p> <p><button type="submit" name="reboot" value="reboot">Reboot</button></p> </form> </body> </html>')
        else:
            html_file.write('<div class="cleared"><h1>Confirm WiFi choice</h1></div> <form action="" method="post" enctype="application/json" novalidate>\n')
            ssid = ap_json['ssid']
            if 'IP' in ap_json:
                ip = ap_json['IP']
            elif 'DHCP' in ap_json:
                ip = ap_json['DHCP']
                html_file.write('<p>This IP address may change in future</p>\n')
            html_file.write(f'<p>Continue with WiFi network {ssid} and IP {ip}</p>\n')
        html_file.write('<p><button type="submit" name="confirm_wifi" value="confirm_wifi">Save</button><button type="cancel" name="quit" value="quit">Quit</button></p></form></body>')

def render_ap_cfg(ap_cfg_html_file, wifi_errs_file, ap_json, errors):
    f_errs = []
    with open(wifi_errs_file, 'r') as f:
        f_errs = f.readlines()
        if f_errs:
            for item in f_errs:
                errors.append(item.strip())
    if len(ap_json['access_points']) < 1:
        # either none or just the Hotspot
        errors.append('No WiFi networks, try restarting')
    preferred_ip = ap_json['preferred_ip']
    with open(ap_cfg_html_file, 'w') as html_file:
        html_file.write(f'{my_c.html_doctype}')
        html_file.write('<style>')
        html_file.write(f'{my_c.header_css}')
        html_file.write('li { text-align: left ; color: red ; }')
        html_file.write('p { text-align: left ; }')
        html_file.write('</style></head>')
        html_file.write(f'{my_c.standard_header}')
        html_file.write('<div class="cleared"><h1>Configure WiFi</h1></div> <form action="" method="post" enctype="application/json" novalidate>\n')
        if errors:
            html_line = '<ul>'
            for error in errors:
                html_line += f'<li>{error}</li>'
            html_line += '</ul>'
            html_file.write(html_line)

        html_file.write('<p><label for="ssids">Choose a WiFi network </label>')
        html_file.write('<select name="ssid" id="ssid">\n')
        for ssid in ap_json['access_points']:
            html_file.write(f'<option value="{ssid}">{ssid}</option>\n')
        html_file.write('</select></p>\n')
        html_file.write('<p>Password for WiFi network <input type="text" minlength="8" maxlength="16" size="16" name="wifi_pass" value="" /></p>\n')
        html_file.write('<p>If you leave the preferred IP blank or 0, the system will use the IP provided by the router</p>\n')
        html_file.write(f'<p>Preferred IP <input type="number" minlength="3" maxlength="3" size="3" name="preferred_ip" value="{preferred_ip}" /></p>\n')
        html_file.write('<p>After saving reconnect to the hotspot and refresh</p>')
        html_file.write('<p><button type="submit" name="save" value="save">Save</button><button type="submit" name="rescan" value="rescan">Rescan</button></p></form></body>')

