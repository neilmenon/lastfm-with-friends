import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { share } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { config } from './config'
import { MessageService } from './message.service';

@Injectable()
export class UserService {
  username: string = localStorage.getItem("lastfm_username");
  session_key: string = localStorage.getItem("lastfm_session");
  user: Observable<any>;
  rapidRefresh: boolean = false;
  constructor(private http: HttpClient, public messageService: MessageService) { }

  isSignedIn() {
    return (localStorage.getItem("lastfm_username") != null) && (localStorage.getItem("lastfm_session") != null);
  }

  setRapidRefresh(rapidRefresh:boolean) {
    this.rapidRefresh = rapidRefresh
    return this.rapidRefresh
  }

  isRapidRefresh() {
    return this.rapidRefresh
  }

  clearLocalData() {
    localStorage.removeItem("lastfm_username")
    localStorage.removeItem("lastfm_session")
  }

  signOut() {
    this.messageService.open("Signing out...");
    this.user = null;
    return this.http.post(config.api_root + "/users/signout", {'username': this.username, 'session_key': this.session_key})
  }
  
  /**
   * Prevent making multiple API requests for the same endpoint on different components.
   * Thanks to https://stackoverflow.com/a/50865911/14861722 for solution
  */
  getUser(force = false): Observable<any> {
    if (this.user && !force) {
      return this.user;
    } else {
      this.user = this.http.get(config.api_root + '/users/' + localStorage.getItem("lastfm_username")).pipe(share());
      return this.user;
    }
  }

  updateUser(userObject: any, fullScrape: boolean) {
    return this.http.post(config.api_root + '/users/update', {
      'username': this.username, 
      'session_key': this.session_key,
      'user_id': userObject['user_id'],
      'full_scrape': fullScrape
    })
  }

  deleteUser(userObject) {
    return this.http.post(config.api_root + '/users/delete', {
      'username': this.username, 
      'session_key': this.session_key,
      'user_id': userObject['user_id'],
    })
  }

  createGroup(formData) {
    return this.http.post(config.api_root + '/groups', {
      'name': formData['name'], 
      'description': formData['description'], 
      'username': this.username, 
      'session_key': this.session_key
    })
  }

  getGroup(joinCode:string) {
    return this.http.post(config.api_root + '/groups/' + joinCode, {'username': this.username, 'session_key': this.session_key})
  }

  joinGroup(joinCode:string) {
    return this.http.post(config.api_root + '/groups/join', {
      'username': this.username, 
      'session_key': this.session_key,
      'join_code': joinCode
    })
  }

  leaveGroup(joinCode:string) {
    return this.http.post(config.api_root + '/groups/' + joinCode + '/leave', {'username': this.username, 'session_key': this.session_key})
  }

  kickMember(userToKick:string, joinCode:string) {
    return this.http.post(config.api_root + '/groups/' + joinCode + '/kick', {
      'username': this.username, 
      'session_key': this.session_key,
      'user_to_kick': userToKick,
    })
  }

  deleteGroup(joinCode:string) {
    return this.http.post(config.api_root + '/groups/' + joinCode + '/delete', {'username': this.username, 'session_key': this.session_key})
  }

  editGroup(joinCode:string, formData) {
    return this.http.post(config.api_root + '/groups/' + joinCode + '/edit', {
      'username': this.username,
      'session_key': this.session_key,
      'name': formData['name'],
      'description': formData['description'],
      'owner': formData['owner']
    })
  }

  wkArtist(query, users, startRange=null, endRange=null) {
    return this.http.post(config.api_root + "/commands/wkartist", {
      'username': this.username,
      'session_key': this.session_key,
      'query': query,
      'users': users,
      'start_range': startRange,
      'end_range': endRange
    })
  }

  wkAlbum(query, users, startRange=null, endRange=null) {
    return this.http.post(config.api_root + "/commands/wkalbum", {
      'username': this.username,
      'session_key': this.session_key,
      'query': query,
      'users': users,
      'start_range': startRange,
      'end_range': endRange
    })
  }

  wkTrack(query, users, startRange=null, endRange=null) {
    return this.http.post(config.api_root + "/commands/wktrack", {
      'username': this.username,
      'session_key': this.session_key,
      'query': query,
      'users': users,
      'start_range': startRange,
      'end_range': endRange
    })
  }

  nowPlaying(join_code) {
    return this.http.post(config.api_root + "/commands/nowplaying", {
      'username': this.username,
      'session_key': this.session_key,
      'join_code': join_code
    })
  }

  scrobbleHistory(wkMode, wkObject, users, sortBy, sortOrder, limit, offset, startRange=null, endRange=null,) {
    let payload = {
      'username': this.username,
      'session_key': this.session_key,
      'wk_mode': wkMode,
      'users': users,
      'start_range': startRange,
      'end_range': endRange,
      'sort_by': sortBy,
      'sort_order': sortOrder,
      'limit': limit,
      'offset': offset
    }
    if (wkMode != "overall") {
      payload['artist_id'] = wkObject['artist']['id']
    }
    if (wkMode == "track") {
      payload['track'] = wkObject['track']['name']
    } else if (wkMode == "album") {
      payload['album_id'] = wkObject['album']['id']
    }
    return this.http.post(config.api_root + "/commands/history", payload)
  }

  whoKnowsTop(wkMode, users, artistId, albumId=null, trackMode=false) {
    let payload = {
      'username': this.username,
      'session_key': this.session_key,
      'wk_mode': wkMode,
      'users': users,
      'artist_id': artistId,
      'album_id': albumId,
      'track_mode': trackMode
    }
    return this.http.post(config.api_root + "/commands/wktop", payload)
  }

  scrobbleLeaderboard(users, startRange, endRange) {
    return this.http.post(config.api_root + "/commands/scrobble-leaderboard", {
      'username': this.username,
      'session_key': this.session_key,
      'users': users,
      'start_range': startRange,
      'end_range': endRange
    })
  }

  wkAutocomplete(wkMode, query) {
    return this.http.post(config.api_root + "/commands/wkautocomplete", {
      'username': this.username,
      'session_key': this.session_key,
      'wk_mode': wkMode,
      'query': query
    })
  }

  artistRedirects(artistString) {
    return this.http.post(config.api_root + "/commands/artistredirects", {
      'username': this.username,
      'session_key': this.session_key,
      'artist_string': artistString,
    })
  }

  charts(chartMode, chartType, users, startRange=null, endRange=null) {
    return this.http.post(config.api_root + "/commands/charts", {
      'username': this.username,
      'session_key': this.session_key,
      'chart_mode': chartMode,
      'chart_type': chartType,
      'users': users,
      'start_range': startRange,
      'end_range': endRange,
    })
  }

  listeningTrends(joinCode, cmdMode, wkMode, wkObject, startRange=null, endRange=null) {
    let payload = {
      'username': this.username,
      'session_key': this.session_key,
      'join_code': joinCode,
      'cmd_mode': cmdMode,
      'wk_options': null,
      'start_range': startRange,
      'end_range': endRange
    }
    if (cmdMode == "wk") {
      let wkOptions = {
        'wk_mode': wkMode,
        'artist_id': wkObject.artist.id
      }
      if (wkMode == "album") {
        wkOptions['album_id'] = wkObject.album.id
      } else if (wkMode == "track") {
        wkOptions['track'] = wkObject.track.name
      }
      payload['wk_options'] = wkOptions
    }
    return this.http.post(config.api_root + "/commands/listeningtrends", payload)
  }
}
