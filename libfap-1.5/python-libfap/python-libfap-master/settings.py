APRS_SERVER_HOST = 'socal.aprs2.net'
APRS_SERVER_PORT = 14580
APRS_USER = 'KG7AFQ'
APRS_PASSCODE = '18869'
FILTER_DETAILS = "filter g/BEAR100\n"


# Check that APRS_USER and APRS_PASSCODE are set
assert len(APRS_USER) > 3 and len(APRS_PASSCODE) > 0, 'Please set APRS_USER and APRS_PASSCODE in settings.py.'
