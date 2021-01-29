import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder } from '@angular/forms';
import { Validators } from '@angular/forms';
import { MessageService } from '../message.service'
import { UserService } from '../user.service'

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  signed_in: boolean = undefined;
  user: any = undefined;
  wkArtistForm;
  wkArtistResults;
  constructor(private formBuilder: FormBuilder, public router: Router, private messageService: MessageService, public http: HttpClient, private userService: UserService) {
    this.signed_in = this.userService.isSignedIn();
    if (this.signed_in) {
      this.userService.getUser().toPromise().then(data => {
        this.user = data;
      }).catch(error => {
      })
    }
    this.wkArtistForm = this.formBuilder.group({
      query: ['']
    })

   }

  ngOnInit(): void {
    this.wkArtistSubmit({'query': "Foals"}, ["neilmenon", "ndiemer2"], "The Audiophiles")
  }

  wkArtistSubmit(formData, users, groupName) {
    this.wkArtistResults = null
    this.userService.wkArtist(formData['query'], users).toPromise().then(data => {
      this.wkArtistResults = data
    }).catch(error => {
      if (error['status'] == 404) {
        this.messageService.open("No one knows " + formData['query'] + " in " + groupName + ".")
      } else {
        this.messageService.open("An error occured submitting your request. Please try again.")
      }
    })
  }
  
  
}
