import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { config } from './config'
import { MessageService } from './message.service';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  username: string = localStorage.getItem("lastfm_username");
  session_key: string = localStorage.getItem("lastfm_session");
  constructor(private http: HttpClient, public messageService: MessageService) { }

  isSignedIn() {
    return (localStorage.getItem("lastfm_username") != null) && (localStorage.getItem("lastfm_session") != null);
  }

  signOut() {
    this.messageService.open("Signing out...");
    return this.http.post(config.api_root + "/users/signout", {'username': this.username, 'session_key': this.session_key})
  }
  
  getUser() {
    return this.http.get(config.api_root + '/users/' + localStorage.getItem("lastfm_username"));
  }
}
