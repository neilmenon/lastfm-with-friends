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
  constructor(private http: HttpClient, public messageService: MessageService) { }

  isSignedIn() {
    return (localStorage.getItem("lastfm_username") != null) && (localStorage.getItem("lastfm_session") != null);
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

  updateUser() {
    return this.http.post(config.api_root + '/users/update', {'username': this.username, 'session_key': this.session_key})
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

  wkArtist(query, users) {
    return this.http.post(config.api_root + "/commands/wkartist", {
      'username': this.username,
      'session_key': this.session_key,
      'query': query,
      'users': users
    })
  }

  wkAlbum(query, users) {
    return this.http.post(config.api_root + "/commands/wkalbum", {
      'username': this.username,
      'session_key': this.session_key,
      'query': query,
      'users': users
    })
  }

  wkTrack(query, users) {
    return this.http.post(config.api_root + "/commands/wktrack", {
      'username': this.username,
      'session_key': this.session_key,
      'query': query,
      'users': users
    })
  }

  nowPlaying(join_code) {
    return this.http.post(config.api_root + "/commands/nowplaying", {
      'username': this.username,
      'session_key': this.session_key,
      'join_code': join_code
    })
  }
}
