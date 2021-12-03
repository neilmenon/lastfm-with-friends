import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { share } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { config } from './config'
import { MessageService } from './message.service';
import { SettingsModel } from './models/settingsModel';
import { NgRedux } from '@angular-redux/store';
import { AppState } from './store';
import { SETTINGS_MODEL } from './actions';
import { HttpScrobbleModel } from './models/httpScrobbleModel';

@Injectable()
export class UserService {
  username: string = localStorage.getItem("lastfm_username");
  session_key: string = localStorage.getItem("lastfm_session");
  user: Observable<any>;
  rapidRefresh: boolean = false;
  constructor(
    private http: HttpClient, 
    public messageService: MessageService,
    private ngRedux: NgRedux<AppState>
  ) { }

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
    localStorage.removeItem("lastfm_show_clear_local")
    localStorage.removeItem("prev_lastfm_username")
    localStorage.removeItem("prev_lastfm_session")
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
      let u = localStorage.getItem("lastfm_username")
      if (u) {
        this.user = this.http.get(config.api_root + '/users/' + u).pipe(share());
        return this.user;
      }
      return null
    }
  }

  setSettings(settings: SettingsModel, showMessage: boolean) {
    this.http.post(config.api_root + '/users/' + this.username + '/settings', {
      'settings': JSON.stringify(settings),
      'session_key': this.session_key
    }).toPromise().then(() => {
      this.ngRedux.dispatch({ type: SETTINGS_MODEL, settingsModel: settings })
      if (showMessage) {
        this.messageService.open("Successfully updated user settings.")
      }
    }).catch(error => {
      console.log(error)
      if (showMessage) {
        this.messageService.open("Unable to save user settings. Please try again.")
      }
    })
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

  whoKnowsTop(wkMode, users, artistId, startRange, endRange, albumId=null, trackMode=false) {
    let payload = {
      'username': this.username,
      'session_key': this.session_key,
      'wk_mode': wkMode,
      'users': users,
      'artist_id': artistId,
      'album_id': albumId,
      'track_mode': trackMode,
      'start_range': startRange,
      'end_range': endRange
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

  listeningTrends(joinCode, cmdMode, wkMode, wkObject, startRange=null, endRange=null, user=null) {
    let payload = {
      'username': this.username,
      'session_key': this.session_key,
      'join_code': joinCode,
      'cmd_mode': cmdMode,
      'wk_options': null,
      'start_range': startRange,
      'end_range': endRange
    }
    if (cmdMode == "wk" || cmdMode == "user-track" || cmdMode == "user-album") {
      let wkOptions = {
        'wk_mode': wkMode,
        'artist_id': wkObject.artist.id
      }
      if (wkMode == "album") {
        wkOptions['album_id'] = wkObject.album.id
      } else if (wkMode == "track") {
        wkOptions['track'] = wkObject.track.name
      }
      if (cmdMode == "user-track" || cmdMode == "user-album") {
        wkOptions['user_id'] = user
      }
      payload['wk_options'] = wkOptions
    }
    return this.http.post(config.api_root + "/commands/listeningtrends", payload)
  }

  appStats() {
    return this.http.post(config.api_root + "/tasks/app-stats", {
      'db_store': false
    })
  }

  wkCharts(users: Array<number>, artistId: number, albumId: number=null, track: string=null, startRange=null, endRange=null) {
    return this.http.post(config.api_root + "/commands/wkcharts", {
      'username': this.username,
      'session_key': this.session_key,
      'users': users,
      'artist_id': artistId,
      'album_id': albumId,
      'track': track,
      'start_range': startRange,
      'end_range': endRange
    })
  }

  getDemoUser() {
    return this.http.post(config.api_root + "/demo", { "username": config.demo_user })
  }

  leaveSession(sessionId: number) {
    return this.http.post(config.api_root + "/group-sessions/leave", { 
      'username': this.username,
      'session_key': this.session_key,
      'session_id': sessionId
    })
  }

  endSession(sessionId: number) {
    return this.http.post(config.api_root + "/group-sessions/end", { 
      'username': this.username,
      'session_key': this.session_key,
      'session_id': sessionId
    })
  }

  createSession(payload: any) {
    return this.http.post(config.api_root + "/group-sessions/create", { 
      'username': this.username,
      'session_key': this.session_key,
      ...payload
    })
  }

  joinSession(sessionId: number, catch_up_timestamp: string, joinCode: string) {
    return this.http.post(config.api_root + "/group-sessions/join", { 
      'username': this.username,
      'session_key': this.session_key,
      'session_id': sessionId,
      'group_jc': joinCode,
      'catch_up_timestamp': catch_up_timestamp
    })
  }

  getSessions(joinCode: string) {
    return this.http.post(config.api_root + "/group-sessions/list", { 
      'username': this.username,
      'session_key': this.session_key,
      'join_code': joinCode
    })
  }
  
  kickUserFromSession(sessionId: number, kickUser: string) {
    return this.http.post(config.api_root + "/group-sessions/kick", { 
      'username': this.username,
      'session_key': this.session_key,
      'session_id': sessionId,
      'kick_user': kickUser
    })
  }

  getRecentTracks(username: string) {
    return this.http.get(`https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=${username}&api_key=${config.api_key}&format=json`)
  }

  getHttpScrobblePayload(tracks: Array<HttpScrobbleModel>) {
    return this.http.post(config.api_root + "/commands/get-signed-scrobbles", {
      'username': this.username,
      'session_key': this.session_key,
      'tracks': tracks
    })
  }

  scrobbleTrack(payload: any) {

    return this.http.post("https://ws.audioscrobbler.com/2.0", (new URLSearchParams(payload)).toString(), {
      headers: new HttpHeaders().set('Content-Type', 'application/x-www-form-urlencoded')
    })
  }

  getUserSessions() {
    return this.http.post(config.api_root + '/users-sessions', {
      'username': this.username,
      'session_key': this.session_key
    })
  }
}
