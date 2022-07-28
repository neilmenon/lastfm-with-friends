import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, NavigationExtras, Router } from '@angular/router';
import { MessageService } from '../message.service';
import { config } from '../config'
import { Md5 } from 'ts-md5/dist/md5';
import { HttpClient } from '@angular/common/http';
import { UserService } from '../user.service';

@Component({
  selector: 'app-lastfmauth',
  templateUrl: './lastfmauth.component.html',
  styleUrls: ['./lastfmauth.component.css']
})
export class LastfmauthComponent implements OnInit {
  constructor(private route: ActivatedRoute, public router: Router, private messageService: MessageService, private http: HttpClient, private userService: UserService) { }

  ngOnInit(): void {
    if (localStorage.getItem("verifiedUser") != "true") {
      this.messageService.save('You do not have access to sign in to Last.fm with Friends.')
      this.router.navigate([''])
    } else {
      let session = localStorage.getItem('lastfm_session');
      if (session == null) {
        this.route.queryParams.subscribe(params => {
          if (params['token']) {
            this.messageService.open('Signing in...', "center", true)
            this.authenticate(params['token']).then(response => {
              localStorage.setItem("lastfm_session", response['session_key'])
              localStorage.setItem("lastfm_username", response['username'])
              window.location.href = config.project_root;
            }).catch(error => {
              console.log(error)
              if (error['error']['error']) {
                this.messageService.save(error['error']['error'])
              } else {
                this.messageService.save("Authentication failed. Most likely the backend service is down.")
              }
              this.router.navigate([''])
            })
          } else {
            this.messageService.open("Sending you to authentication page...", "center", true)
            window.location.href = 'https://www.last.fm/api/auth/?api_key='+ config.api_key +'&cb='+ config.project_root +'/lastfmauth';
          }
        });
      } else {
        this.messageService.save('Already signed in!')
        this.router.navigate([''])
      }
    }
  }

  async authenticate(token: string) {
    const response_data = await this.http.post(config.api_root + '/users/authenticate', {"token": token}).toPromise();
    return response_data;
  }
}
