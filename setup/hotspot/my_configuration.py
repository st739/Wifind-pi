'''
shared configuration information
for initial setup of hotspot and connection to WiFi
'''

ap_cfg_html_file = "ap_cfg.html"
log_file = "log.txt"
wifi_json_file = "wifi.json"
wifi_errs_file = "wifi.errs"

# low and high limits for preferred_ip
wifi_static_ip = { 'low' : 100, 'high' : 250 }

index_css = " .parent { text-align: left; } .left { display: inline-block; float: left; line-height: 30px; width: 50%; padding-right: 1rem; vertical-align: middle; } .closed { display: inline-block; float: left; background-color: Gold; width: 20px; height: 20px; border-radius: 50%; vertical-align: middle; } .opened { display: inline-block; float: left; background-color: MediumSpringGreen; width: 20px; height: 20px; border-radius: 50%; vertical-align: middle; } .empty { display: inline-block; float: left; background-color: gray; width: 20px; height: 20px; border-radius: 50%; vertical-align: middle; }"
# padding is top, right, bottom, left
header_css = "html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;} .container { max-width: 600px; padding: 5px 20px 5px 0px; } .text_subcontainer { background-color: white; float: left; padding: 7px 10px 7px 5px; text-align: center; font-family: 'Helvetica', sans-serif; } .subcontainer { background-color: white; float: left; border: 2px solid #dcdcdc; padding: 5px 10px 5px 5px; border-radius: 10px; text-align: center; font-family: 'Helvetica', sans-serif; } a { color: royalblue; text-decoration: none; font-weight: bold; } a:visited { color: purple; text-decoration: none; } .cleared { clear: left; } "
standard_header = "<body>"
html_doctype = "<!DOCTYPE html> <head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"><meta http-equiv=\"Cache-Control\" content=\"no-cache, no-store, must-revalidate\"> <meta http-equiv=\"Pragma\" content=\"no-cache\"> <meta http-equiv=\"Expires\" content=\"0\">"
