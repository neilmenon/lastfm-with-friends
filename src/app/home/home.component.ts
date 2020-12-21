import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService} from '../message.service'
@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  username;
  constructor(public router: Router, private messageService: MessageService) { }

  ngOnInit(): void {
    this.username = localStorage.getItem("lastfm_username")
  }

  logOut() {
    localStorage.removeItem("lastfm_session");
    localStorage.removeItem("lastfm_username");
    this.messageService.open("Successfully logged out " + this.username);
    this.username = null;
  }
}
