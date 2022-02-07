# Last.fm with Friends

Last.fm with Friends extends existing Last.fm features to give music stats for a group of friends. The app runs at [lastfmwithfriends.io](https://lastfmwithfriends.io).

## How It Works
Last.fm with Friends is powered by the [Last.fm API](https://www.last.fm/api). Once you connect your Last.fm account, the app scrapes and stores your scrobbles (Last.fm lingo for music plays) in a database. Then, you can create a group and invite your friends to join the group using a join code. The app gives you and your friends cool stats and visualizations based on what everyone has listened to!

## Demo
You can demo the app at [lastfmwithfriends.io](https://lastfmwithfriends.io) to see all of the features.

## List of Featues
Last.fm with Friends includes many handy tools to view a group's listening habits. I've listed some them below.

**Important!** Most features on the app are time-adjustable! That means you can adjust the time period of which the stats are calculated to any range (e.g. what is group's top artist in the past 30 days, etc).
- **Who Knows This Artist/Album/Track** - see who knows a particular artist/album/track and how many scrobbles they have.
- **Group Sessions** - Missing scrobbles when listening with friends? Create and join listening sessions to automatically get scrobbles from another user. Already been listening with a friend in the group? Select the first track you heard and the app will get you up to speed.
- **Listening Trends - Group** - see all the group members' scrobbles mapped on a chart to see how it changes over time. Available on every artist, album and track.
- **Listening Trends - User** - see *your* tracks or albums for an artist mapped on a chart to see how your favorite track or album by that artist has changed over time.
- **Individual & Group Charts** - see which artist/album/track scores the highest in the group as well as view your individual charts.
- **Group Scrobble History** - just like your Last.fm profile, except it includes everyone's scrobbles. Also available on the artist/album/track level.
- **Listening Activity** - quickly view what everyone in the group is listening to.
- **Scrobble Leaderboard** - see who's leading the group in scrobbles.
- **Top Scrobbles** - quickly view your top tracks or albums for an artist.
- **Manually Scrobble Tracks** - quick and handy feature submit a scrobble to Last.fm directly from the app! For most extensive manual scrobbling, check out [Open Scrobbler](https://openscrobbler.com/).
- **Personal Stats Report** - get a brief, unique report everyday about your music habits at the top of your home page.
- **Top Genres** - see the group's top genres. *Coming soon!*
- **Group Mainstream Factor** - how mainstream is the group's music? *Coming soon!*

## Technical
Last.fm with Friends was built with the following technologies:

- Angular
- Flask / Python
- MariaDB
- uWSGI behind NGINX

The app is currently self-hosted on a CentOS server and is powered by an internal API to scrape from Last.fm and perform actions. Each scrobble is stored individually in a table to increase efficiency and ease-of-access for stats. Users are authenticated via a Last.fm-generated session token which the app stores when the user connects their Last.fm account. Scrobbles are fetched for each user periodically.

## Issues / Suggestions
If you encounter any issues while using the app, or want to make a suggestion for a new feature, please use the [Issues](https://github.com/neilmenon/lastfm-with-friends/issues) tab. This is a solo project by a music nerd, so feedback is most certainly welcome!

## Enjoying Last.fm with Friends?
Perhaps you could [lend a hand with the hosting costs for the app](https://www.buymeacoffee.com/neilmenon). Thank you!