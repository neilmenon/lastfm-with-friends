import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { share } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { config } from './config'
import { MessageService } from './message.service';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  username: string = localStorage.getItem("lastfm_username");
  session_key: string = localStorage.getItem("lastfm_session");
  user: Observable<any>;
  constructor(private http: HttpClient, public messageService: MessageService) { }

  isSignedIn() {
    return (localStorage.getItem("lastfm_username") != null) && (localStorage.getItem("lastfm_session") != null);
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
  getUser(): Observable<any> {
    if (this.user) {
      return this.user;
    } else {
      this.user = this.http.get(config.api_root + '/users/' + localStorage.getItem("lastfm_username")).pipe(share());
      return this.user;
    }
  }
}
