'''
shared configuration information
for initial setup of hotspot and connection to WiFi
'''

# topdir = "/usr/local/setup"
# hotspot_path = f"{topdir}/hotspot"
# template_path = f"{hotspot_path}/templates"
# index_css_file = f"{template_path}/index.css"
# ap_cfg_html_file = f"{template_path}/ap_cfg.html"
# help_html_file = f"{template_path}/help.html"
ap_cfg_html_file = "ap_cfg.html"
help_html_file = "help.html"

# log_file = f"{topdir}/log.txt"
log_file = "log.txt"

# data_path = f"{topdir}/data"
# wifi_json_file = f"{data_path}/wifi.json"
# wifi_errs_file = f"{data_path}/wifi.errs"
wifi_json_file = "wifi.json"
wifi_errs_file = "wifi.errs"

# low and high limits for preferred_ip
wifi_static_ip = { 'low' : 100, 'high' : 250 }

time_debug = False
init_debug = False
wifi_debug = True
html_debug = False
parse_debug = True
app_debug = True
script_debug = True

index_css = " .parent { text-align: left; } .left { display: inline-block; float: left; line-height: 30px; width: 50%; padding-right: 1rem; vertical-align: middle; } .closed { display: inline-block; float: left; background-color: Gold; width: 20px; height: 20px; border-radius: 50%; vertical-align: middle; } .opened { display: inline-block; float: left; background-color: MediumSpringGreen; width: 20px; height: 20px; border-radius: 50%; vertical-align: middle; } .empty { display: inline-block; float: left; background-color: gray; width: 20px; height: 20px; border-radius: 50%; vertical-align: middle; }"
# padding is top, right, bottom, left
header_css = "html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;} .container { max-width: 600px; padding: 5px 20px 5px 0px; } .text_subcontainer { background-color: white; float: left; padding: 7px 10px 7px 5px; text-align: center; font-family: 'Helvetica', sans-serif; } .subcontainer { background-color: white; float: left; border: 2px solid #dcdcdc; padding: 5px 10px 5px 5px; border-radius: 10px; text-align: center; font-family: 'Helvetica', sans-serif; } a { color: royalblue; text-decoration: none; font-weight: bold; } a:visited { color: purple; text-decoration: none; } .cleared { clear: left; } "
# new header
standard_header = "<body>"
# standard_header = "<body><div class=\"container\"><div class=\"subcontainer\"><a href=\"/configure\">Configure</a></div><div class=\"subcontainer\"><a href=\"/help\">Help</a></div></div>"
html_doctype = "<!DOCTYPE html> <head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"><meta http-equiv=\"Cache-Control\" content=\"no-cache, no-store, must-revalidate\"> <meta http-equiv=\"Pragma\" content=\"no-cache\"> <meta http-equiv=\"Expires\" content=\"0\">"
