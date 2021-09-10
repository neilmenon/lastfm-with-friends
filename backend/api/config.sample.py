config = {
    'sql': {
        'user': '',
        'password': '',
        'host': '',
        'port': 3306,
        'database': 'lastfm_with_friends',
    },
    'api': {
        'key': '', # Last.fm API key. See https://www.last.fm/api/account/create
        'secret': '', # Last.fm Secret key. See https://www.last.fm/api/account/create
    },
    'server': False, # False if running on localhost, True running with uWSGI / NGINX
    'demo_user': "" # username of demo user
}
