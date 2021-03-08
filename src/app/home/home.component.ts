import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from '../message.service'
import { UserService } from '../user.service'
import * as moment from 'moment';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  signed_in: boolean = undefined;
  user: any = undefined;
  moment: any = moment;
  commit;
  constructor(public router: Router, private messageService: MessageService, public http: HttpClient, private userService: UserService) {
    this.signed_in = this.userService.isSignedIn();
    if (this.signed_in) {
      this.userService.getUser().toPromise().then(data => {
        this.user = data;
        this.http.get('https://api.github.com/repos/neilmenon/lastfm-with-friends/git/refs/heads/master').toPromise().then(data => {
          this.http.get(data['object']['url']).toPromise().then(data => {
            this.commit = data
          })
        })
      }).catch(error => {
      })
    }
   }

  ngOnInit(): void {}
}
