#!/bin/env python3

'''
stub to demo start an application
try/except is used to prevent multiple instance attempts
this is invoked by systemd/cust-net at boot and
networkmanager/netmon if the desired WiFi stops and starts
'''
import asyncio
import errno
import os
from microdot.microdot import Microdot

async def run_webserver():
    app = Microdot()
    @app.route("/", methods=["GET","POST"])
    def index(request):
        return 'Hello, world!'
    try:
        await app.start_server(port=80)
    except OSError as exc:
        if exc.errno == 98:     # address in use
            return
    
async def main():
    await asyncio.gather(run_webserver())
asyncio.run(main())

