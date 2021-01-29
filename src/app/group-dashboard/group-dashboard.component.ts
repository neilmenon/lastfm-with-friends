import { Component, OnInit, Input } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Validators } from '@angular/forms';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';

@Component({
  selector: 'app-group-dashboard',
  templateUrl: './group-dashboard.component.html',
  styleUrls: ['./group-dashboard.component.css']
})
export class GroupDashboardComponent implements OnInit {
  wkArtistForm;
  wkArtistResults;
  
  constructor(private formBuilder: FormBuilder, private userService: UserService, private messageService: MessageService) { 
    this.wkArtistForm = this.formBuilder.group({
      query: ['']
    })
  }

  @Input() group: any;

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
