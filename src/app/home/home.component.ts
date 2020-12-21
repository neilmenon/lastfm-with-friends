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
  signed_in;
  constructor(public router: Router, private messageService: MessageService) { }

  ngOnInit(): void {
    this.username = localStorage.getItem("lastfm_username")
    this.signed_in =localStorage.getItem("lastfm_username") != null
  }

  signOut() {
    localStorage.removeItem("lastfm_session");
    localStorage.removeItem("lastfm_username");
    this.messageService.open("Successfully signed out " + this.username);
    this.username = null;
    this.signed_in = null;
  }
}
