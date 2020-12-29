import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from '../message.service'
import { UserService } from '../user.service'

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  signed_in: boolean;
  user;
  constructor(public router: Router, private messageService: MessageService, public http: HttpClient, private userService: UserService) {
    this.userService.getUser().toPromise().then(data => {
      console.log(data)
      this.user = data
    })
   }

  ngOnInit(): void {
    this.signed_in = this.userService.isSignedIn();
  }

  signOut() {
    this.userService.signOut().toPromise().then(response => {
      localStorage.removeItem("lastfm_session");
      localStorage.removeItem("lastfm_username");
      this.user = null;
      this.signed_in = null;
      this.messageService.open(response['success']);
    }).catch(error => {
      this.messageService.open("An error occured while trying to sign you out! Please try again.");
    })
    
  }
}
