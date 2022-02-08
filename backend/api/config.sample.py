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
    'demo_user': "", # username of demo user
    'sql_logging': False, # enable for logging all SQL queries
    'admin_username': '', # Last.fm username of the admin of the app (for admin functionality)
    'max_concurrent_full_scrapes': 2
}
