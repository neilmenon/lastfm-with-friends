import { Component, OnInit } from '@angular/core';
import { MessageService } from '../message.service';
import { NavigationEnd, Router } from '@angular/router';

@Component({
  selector: 'app-messages',
  templateUrl: './messages.component.html',
  styleUrls: ['./messages.component.css']
})
export class MessagesComponent implements OnInit {
  constructor(public messageService: MessageService, private router: Router) { 
    router.events.subscribe(val => {
      if (val instanceof NavigationEnd && val.url != "/lastfmauth") {
        if (this.messageService.message)
          this.messageService.open(this.messageService.message);
          this.messageService.message = null;
      }
    });
  }

  ngOnInit(): void {
  }

}
