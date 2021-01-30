import { listLazyRoutes } from '@angular/compiler/src/aot/lazy_routes';
import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
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
  @ViewChild('wkArtist', { static: true }) wkArtistDom: ElementRef;
  wkArtistForm;
  wkArtistResults;
  wkArtistInit: boolean = false;
  constructor(private formBuilder: FormBuilder, private userService: UserService, private messageService: MessageService) {
    this.wkArtistForm = this.formBuilder.group({
      query: ['']
    })
    
  }

  @Input() group: any;

  ngOnInit(): void {
    
  }

  wkArtistSubmit(formData, users) {
    this.wkArtistInit = true
    this.wkArtistResults = null
    this.wkArtistDom.nativeElement.style.background = ''
    this.userService.wkArtist(formData['query'], users).toPromise().then(data => {
      this.wkArtistResults = data
      this.wkArtistDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkArtistResults['artist']['image_url']+')'
      this.wkArtistDom.nativeElement.style.backgroundPosition = 'center'
      this.wkArtistDom.nativeElement.style.backgroundRepeat = 'no-repeat'
      this.wkArtistDom.nativeElement.style.backgroundSize = 'cover'
    }).catch(error => {
      this.wkArtistInit = false
      if (error['status'] == 404) {
        this.wkArtistInit = undefined;
      } else {
        this.messageService.open("An error occured submitting your request. Please try again.")
        console.log(error)
      }
    })
  }

  sort(column) {
    if (this.wkArtistResults.users.length > 1) {
      if (this.wkArtistResults.users[0][column] < this.wkArtistResults.users[1][column]) {
        this.wkArtistResults.users.sort(((a, b) => (a[column] < b[column]) ? 1 : -1))
      } else {
        this.wkArtistResults.users.sort(((a, b) => (a[column] > b[column]) ? 1 : -1))
      }
    }
  }

}
