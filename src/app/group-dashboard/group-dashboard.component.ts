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
  // wkArtist
  @ViewChild('wkArtist', { static: true }) wkArtistDom: ElementRef;
  wkArtistForm;
  wkArtistResults;
  wkArtistInit: boolean = false;

  // wkAlbum
  @ViewChild('wkAlbum', { static: true }) wkAlbumDom: ElementRef;
  wkAlbumForm;
  wkAlbumResults;
  wkAlbumInit: boolean = false;

  // wkTrack
  @ViewChild('wkTrack', { static: true }) wkTrackDom: ElementRef;
  wkTrackForm;
  wkTrackResults;
  wkTrackInit: boolean = false;
  constructor(private formBuilder: FormBuilder, private userService: UserService, private messageService: MessageService) {
    this.wkArtistForm = this.formBuilder.group({query: ['']})
    this.wkAlbumForm = this.formBuilder.group({query: ['']})
    this.wkTrackForm = this.formBuilder.group({query: ['']})
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

  wkAlbumSubmit(formData, users) {
    this.wkAlbumInit = true
    this.wkAlbumResults = null
    this.wkAlbumDom.nativeElement.style.background = ''
    this.userService.wkAlbum(formData['query'], users).toPromise().then(data => {
      this.wkAlbumResults = data
      this.wkAlbumDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkAlbumResults['album']['image_url']+')'
      this.wkAlbumDom.nativeElement.style.backgroundPosition = 'center'
      this.wkAlbumDom.nativeElement.style.backgroundRepeat = 'no-repeat'
      this.wkAlbumDom.nativeElement.style.backgroundSize = 'cover'
    }).catch(error => {
      this.wkAlbumInit = false
      if (error['status'] == 404) {
        this.wkAlbumInit = undefined;
      } else {
        this.messageService.open("An error occured submitting your request. Please try again.")
        console.log(error)
      }
    })
  }

  // wkTrackSubmit(formData, users) {
  //   this.wkTrackInit = true
  //   this.wkTrackResults = null
  //   this.wkTrackDom.nativeElement.style.background = ''
  //   this.userService.wkTrack(formData['query'], users).toPromise().then(data => {
  //     this.wkTrackResults = data
  //     this.wkTrackDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkTrackResults['artist']['image_url']+')'
  //     this.wkTrackDom.nativeElement.style.backgroundPosition = 'center'
  //     this.wkTrackDom.nativeElement.style.backgroundRepeat = 'no-repeat'
  //     this.wkTrackDom.nativeElement.style.backgroundSize = 'cover'
  //   }).catch(error => {
  //     this.wkTrackInit = false
  //     if (error['status'] == 404) {
  //       this.wkTrackInit = undefined;
  //     } else {
  //       this.messageService.open("An error occured submitting your request. Please try again.")
  //       console.log(error)
  //     }
  //   })
  // }

  sort(column, command) {
    if (command == "wkArtist") {
      if (this.wkArtistResults.users.length > 1) {
        if (this.wkArtistResults.users[0][column] < this.wkArtistResults.users[1][column]) {
          this.wkArtistResults.users.sort(((a, b) => (a[column] < b[column]) ? 1 : -1))
        } else {
          this.wkArtistResults.users.sort(((a, b) => (a[column] > b[column]) ? 1 : -1))
        }
      }
    } else if (command == "wkAlbum") {
      if (this.wkAlbumResults.users.length > 1) {
        if (this.wkAlbumResults.users[0][column] < this.wkAlbumResults.users[1][column]) {
          this.wkAlbumResults.users.sort(((a, b) => (a[column] < b[column]) ? 1 : -1))
        } else {
          this.wkAlbumResults.users.sort(((a, b) => (a[column] > b[column]) ? 1 : -1))
        }
      }
    } else if (command == "wkTrack") {
      if (this.wkTrackResults.users.length > 1) {
        if (this.wkTrackResults.users[0][column] < this.wkTrackResults.users[1][column]) {
          this.wkTrackResults.users.sort(((a, b) => (a[column] < b[column]) ? 1 : -1))
        } else {
          this.wkTrackResults.users.sort(((a, b) => (a[column] > b[column]) ? 1 : -1))
        }
      }
    }
  }

}
