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
  signed_in: boolean = undefined;
  user: any;
  constructor(public router: Router, private messageService: MessageService, public http: HttpClient, private userService: UserService) {
    this.userService.getUser().toPromise().then(data => {
      this.user = data;
      console.log(typeof(this.user))
      this.signed_in = this.userService.isSignedIn();
    }).catch(error => {
      this.signed_in = this.userService.isSignedIn();
    })
   }

  ngOnInit(): void {
    this.signed_in = this.userService.isSignedIn();
  }

    
}
