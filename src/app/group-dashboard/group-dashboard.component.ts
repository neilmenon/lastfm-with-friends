import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
import {MatDialog, MAT_DIALOG_DATA} from '@angular/material/dialog';
import { FormBuilder } from '@angular/forms';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';
import * as moment from 'moment';
import { ScrobbleHistoryComponent } from '../scrobble-history/scrobble-history.component';
import { WhoKnowsTopComponent } from '../who-knows-top/who-knows-top.component';
import { MatSliderChange } from '@angular/material/slider';
import { BehaviorSubject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';

@Component({
  selector: 'app-group-dashboard',
  templateUrl: './group-dashboard.component.html',
  styleUrls: ['./group-dashboard.component.css']
})
export class GroupDashboardComponent implements OnInit {
  moment: any = moment;

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

  // nowplaying
  nowPlayingResults = null;
  npInterval: any;
  nowPlayingTimeoutReached: boolean = false;

  // scrobbleLeaderboard
  @ViewChild('scrobbleLeaderboard', { static: true }) leaderboardDom: ElementRef;
  leaderboardSliderMappings: any = [
    {'label': '24 hours', 'days': 1},
    {'label': '7 days', 'days': 7},
    {'label': '14 days', 'days': 14},
    {'label': '30 days', 'days': 30},
    {'label': '60 days', 'days': 60},
    {'label': '90 days', 'days': 90},
    {'label': '180 days', 'days': 180},
    {'label': '365 days', 'days': 365},
    {'label': 'All time', 'days': -1}
  ];
  leaderboardSelectedIndex: number = 1; // real-time slider value
  leaderboardLoadedIndex: number = 1; // http request-dependent value
  leaderboardObject: any;
  leaderboardLoading: boolean = true;
  valueSubject = new BehaviorSubject<number>(1);
  constructor(private formBuilder: FormBuilder, private userService: UserService, public messageService: MessageService, public dialog: MatDialog) {
    moment.locale('en-short', {
      relativeTime: {
        future: 'in %s',
        past: '%s',
        s:  '%s',
        ss: '%ss',
        m:  '1m',
        mm: '%dm',
        h:  '1h',
        hh: '%dh',
        d:  '1d',
        dd: '%dd',
        M:  '1mo',
        MM: '%dmo',
        y:  '1y',
        yy: '%dY'
      }
    });
    this.wkArtistForm = this.formBuilder.group({query: ['']})
    this.wkAlbumForm = this.formBuilder.group({query: ['']})
    this.wkTrackForm = this.formBuilder.group({query: ['']})
  }

  @Input() group: any;
  @Input() user: any;

  ngOnInit(): void {
      this.nowPlayingStartInterval();
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState == "visible") {
          if (this.nowPlayingTimeoutReached) { // they revisited tab, start interval again
            this.nowPlayingTimeoutReached = false;
            this.nowPlayingStartInterval();
          } else {
            this.nowPlaying();
          }
        }
      })
      this.valueSubject.pipe(debounceTime(1000)).subscribe(value => {
        if (value == this.leaderboardSliderMappings.length-1) { // All time
          this.scrobbleLeaderboard(value, this.group.members.map(u => u.id))
        } else {
          let endRange = moment.utc()
          let startRange = moment.utc().subtract(this.leaderboardSliderMappings[value]['days'], 'd')
          this.scrobbleLeaderboard(value, this.group.members.map(u => u.id), startRange, endRange)
        }
      })
  }

  nowPlayingStartInterval() {
    this.nowPlaying()
    let counter = 0
    this.npInterval = setInterval(() => {
      if (counter >= 1080)  { // if open for 3 hours (180 iters * 10 seconds)... that's enough
        clearInterval(this.npInterval);
        this.nowPlayingTimeoutReached = true
        this.nowPlayingResults = []
      } else if (document.visibilityState == "visible") {
        this.nowPlaying();
      }
      counter++
    }, 10000)
  }

  ngOnDestroy() {
    clearInterval(this.npInterval);
  }

  wkArtistSubmit(formData, users) {
    this.wkArtistInit = true
    this.wkArtistResults = null
    this.wkArtistDom.nativeElement.style.background = ''
    this.userService.wkArtist(formData['query'], users.map(u => u.id)).toPromise().then(data => {
      this.wkArtistResults = data
      this.wkArtistDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkArtistResults['artist']['image_url']+')'
      this.wkArtistDom.nativeElement.style.backgroundPosition = 'center'
      this.wkArtistDom.nativeElement.style.backgroundRepeat = 'no-repeat'
      this.wkArtistDom.nativeElement.style.backgroundSize = 'cover'
      if (data['artist']['fallback']) {
        this.messageService.open("No one knows \"" + formData['query'] + "\" in " + this.group.name + ". Showing results for " + data['artist']['name'] + ".")
      }
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
    this.userService.wkAlbum(formData['query'], users.map(u => u.id)).toPromise().then(data => {
      this.wkAlbumResults = data
      this.wkAlbumDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkAlbumResults['album']['image_url']+')'
      this.wkAlbumDom.nativeElement.style.backgroundPosition = 'center'
      this.wkAlbumDom.nativeElement.style.backgroundRepeat = 'no-repeat'
      this.wkAlbumDom.nativeElement.style.backgroundSize = 'cover'
    }).catch(error => {
      this.wkAlbumInit = false
      if (error['status'] == 404) {
        this.wkAlbumInit = undefined;
      } else if(error['status'] == 400) {
        this.messageService.open("Improperly formatted query (format: Artist - Album)")
      } else {
        this.messageService.open("An error occured submitting your request. Please try again.")
        console.log(error)
      }
    })
  }

  wkTrackSubmit(formData, users) {
    this.wkTrackInit = true
    this.wkTrackResults = null
    this.wkTrackDom.nativeElement.style.background = ''
    this.userService.wkTrack(formData['query'], users.map(u => u.id)).toPromise().then(data => {
      this.wkTrackResults = data
      this.wkTrackDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkTrackResults['track']['image_url']+')'
      this.wkTrackDom.nativeElement.style.backgroundPosition = 'center'
      this.wkTrackDom.nativeElement.style.backgroundRepeat = 'no-repeat'
      this.wkTrackDom.nativeElement.style.backgroundSize = 'cover'
    }).catch(error => {
      this.wkTrackInit = false
      if (error['status'] == 404) {
        this.wkTrackInit = undefined;
      } else if(error['status'] == 400) {
        this.messageService.open("Improperly formatted query (format: Artist - Track)")
      } else {
        this.messageService.open("An error occured submitting your request. Please try again.")
        console.log(error)
      }
    })
  }

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

  nowPlaying(loading=false) {
    if (loading)
      this.nowPlayingResults = null
    this.userService.nowPlaying(this.group.join_code).toPromise().then(data => {
      this.nowPlayingResults = data;
    }).catch(error => {
      this.nowPlayingResults = undefined
    })
  }

  nowPlayingToWk(entry, wkArtist: HTMLElement=null) {
    let albumQuery = entry.artist + " - " + entry.album
    this.wkArtistForm.get('query').setValue(entry.artist)
    this.wkAlbumForm.get('query').setValue(albumQuery)
    this.wkArtistSubmit({'query': entry.artist}, this.group.members)
    this.wkAlbumSubmit({'query': albumQuery}, this.group.members)
    if (entry.track !== undefined) {
      let trackQuery = entry.artist + " - " + entry.track
      this.wkTrackForm.get('query').setValue(trackQuery)
      this.wkTrackSubmit({'query': trackQuery}, this.group.members)
    }
    if (wkArtist)
      wkArtist.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"})
  }

  scrobbleHistory(wkMode, wkObject, users) {
    let dialogRef = this.dialog.open(ScrobbleHistoryComponent, {
      data: {
        group: this.group,
        wkMode: wkMode,
        wkObject: wkObject,
        users: users,
        user: this.user
      }
    })
    let wkSub = dialogRef.componentInstance.wkFromDialog.subscribe((entry) => {
      this.nowPlayingToWk(entry)
    })
    let wkTopSub = dialogRef.componentInstance.wkFromTopDialog.subscribe(data => {
      this.whoKnowsTop(data.wkMode, data.wkObject, data.selectedUser)
    })
    dialogRef.afterClosed().subscribe(() => {
      wkSub.unsubscribe()
      wkTopSub.unsubscribe()
    })
  }

  whoKnowsTop(wkMode, wkObject, selectedUser) {
    let dialogRef = this.dialog.open(WhoKnowsTopComponent, {
      data : {
        group: this.group,
        wkMode: wkMode,
        wkObject: wkObject,
        user: this.user,
        selectedUser: selectedUser
      }
    })
    let wkSub = dialogRef.componentInstance.wkFromDialog.subscribe((entry) => {
      this.nowPlayingToWk(entry)
    })
    dialogRef.afterClosed().subscribe(() => {
      wkSub.unsubscribe()
    })
  }

  scrobbleLeaderboard(indexValue, users, startRange=null, endRange=null) {
    this.userService.scrobbleLeaderboard(users, startRange, endRange).toPromise().then(data => {
      this.leaderboardLoadedIndex = indexValue;
      this.leaderboardObject = data
      this.leaderboardLoading = false
      this.leaderboardDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.leaderboardObject.leaderboard[0]['profile_image']+')'
      this.leaderboardDom.nativeElement.style.backgroundPosition = 'center'
      this.leaderboardDom.nativeElement.style.backgroundRepeat = 'no-repeat'
      this.leaderboardDom.nativeElement.style.backgroundSize = 'cover'
    }).catch(error => {
      this.messageService.open("There was an issue getting the scrobble leaderboard. Please try again")
      console.log(error)
      this.leaderboardLoading = false
      this.leaderboardLoadedIndex = indexValue;
    })
  }

  onleaderboardSliderChange(event: MatSliderChange) {
    this.leaderboardLoading = true;
    this.leaderboardSelectedIndex = event.value
    this.valueSubject.next(event.value);
  }

}
