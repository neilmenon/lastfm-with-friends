import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { FormBuilder } from '@angular/forms';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';
import * as moment from 'moment';
import { ScrobbleHistoryComponent } from '../scrobble-history/scrobble-history.component';
import { WhoKnowsTopComponent } from '../who-knows-top/who-knows-top.component';
import { MatSliderChange } from '@angular/material/slider';
import { BehaviorSubject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { CustomDateRangeComponent } from '../custom-date-range/custom-date-range.component';
import { MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { DeviceDetectorService } from 'ngx-device-detector';

@Component({
  selector: 'app-group-dashboard',
  templateUrl: './group-dashboard.component.html',
  styleUrls: ['./group-dashboard.component.css']
})
export class GroupDashboardComponent implements OnInit {
  moment: any = moment;
  deviceInfo: any = null;

  // mappings for all date sliders/dropdowns
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

  // wkArtist
  @ViewChild('wkArtist', { static: true }) wkArtistDom: ElementRef;
  wkArtistForm;
  wkArtistResults;
  wkArtistInit: boolean = false;
  wkArtistRedirectLoading: boolean = false;
  wkArtistSelectedIndex: number = this.leaderboardSliderMappings.length - 1;
  wkArtistIsCustomDateRange: boolean = false;
  wkArtistValueSubject = new BehaviorSubject<number>(1);
  wkArtistDateLoading: boolean = false;
  wkArtistCustomStartDate: moment.Moment;
  wkArtistCustomEndDate: moment.Moment;

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
  leaderboardSelectedIndex: number = 1; // real-time slider value
  leaderboardLoadedIndex: number = 1; // http request-dependent value
  leaderboardObject: any;
  leaderboardLoading: boolean = true;
  leaderboardValueSubject = new BehaviorSubject<number>(1);
  customStartDate: moment.Moment;
  customEndDate: moment.Moment;
  isCustomDateRange: boolean = false;

  // wkAutocomplete
  @ViewChild('wkArtistInput', { read : MatAutocompleteTrigger}) wkArtistInput: MatAutocompleteTrigger;
  @ViewChild('wkAlbumInput', { read : MatAutocompleteTrigger}) wkAlbumInput: MatAutocompleteTrigger;
  @ViewChild('wkTrackInput', { read : MatAutocompleteTrigger}) wkTrackInput: MatAutocompleteTrigger;
  @ViewChild('wkArtistInput', { static: false }) private wkArtistInputRaw: ElementRef;
  @ViewChild('wkAlbumInput', { static: false }) private wkAlbumInputRaw: ElementRef;
  @ViewChild('wkTrackInput', { static: false }) private wkTrackInputRaw: ElementRef;
  wkAutoSubject = new BehaviorSubject<Object>(null);
  wkArtistSuggestions: any = {'suggestions': [], 'partial_result': false};
  wkAlbumSuggestions: any = {'suggestions': [], 'partial_result': false};
  wkTrackSuggestions: any = {'suggestions': [], 'partial_result': false};

  // individualGroupCharts
  @ViewChild('individualGroupCharts', { static: true }) chartsDom: ElementRef;
  chartSelectedUser: any = "all";
  chartReleaseType: string = "track";
  chartDropdownDate: number = 30;
  chartLoading: boolean = false;
  chartIsCustomDate: boolean = false;
  chartCustomStartDate: moment.Moment;
  chartCustomEndDate: moment.Moment;
  chartResults;
  chartTopEntry;

  constructor(private formBuilder: FormBuilder, private userService: UserService, public messageService: MessageService, public dialog: MatDialog, private detectorService: DeviceDetectorService) {
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
      this.deviceInfo = this.detectorService.getDeviceInfo()
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
      // leaderboard slider change
      this.leaderboardValueSubject.pipe(debounceTime(1000)).subscribe(value => {
        if (value == this.leaderboardSliderMappings.length-1) { // All time
          this.scrobbleLeaderboard(value, this.group.members.map(u => u.id))
        } else {
          let endRange = moment.utc()
          let startRange = moment.utc().subtract(this.leaderboardSliderMappings[value]['days'], 'd')
          this.scrobbleLeaderboard(value, this.group.members.map(u => u.id), startRange, endRange)
        }
      })
      // wkArtist slider change
      this.wkArtistValueSubject.pipe(debounceTime(1000)).subscribe(value => {
        if (this.wkArtistResults) {
          if (value == this.leaderboardSliderMappings.length-1) { // All time
            this.wkArtistSubmit({'query': this.wkArtistResults.artist.name}, this.group.members)
          } else {
            let endRange = moment.utc()
            let startRange = moment.utc().subtract(this.leaderboardSliderMappings[value]['days'], 'd')
            this.wkArtistSubmit({'query': this.wkArtistResults.artist.name}, this.group.members, startRange, endRange, true)
          }
        }
      })
      // wk autocomplete
      this.wkAutoSubject.pipe(debounceTime(500)).subscribe(value => {
        if (value) {
          this.userService.wkAutocomplete(value['wkMode'], value['query']).toPromise().then(data => {
            if (value['wkMode'] == "artist") {
              this.wkArtistSuggestions = data
            } else if (value['wkMode'] == "album") {
              this.wkAlbumSuggestions = data
            } else { // track
              this.wkTrackSuggestions = data
            }
          })
        }
      })
      // charts
      this.charts();
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

  wkArtistSubmit(formData, users, startRange=null, endRange=null, fromSliderChange:boolean=false) {
    this.wkArtistInit = true
    if (!fromSliderChange) {
      this.wkArtistResults = null
      this.wkArtistDom.nativeElement.style.background = ''
    }
    this.userService.wkArtist(formData['query'], users.map(u => u.id), startRange ? startRange.format() : null, endRange ? endRange.format() : null).toPromise().then(data => {
      this.wkArtistDateLoading = false;
      this.wkArtistResults = data
      if (!fromSliderChange) {
        this.wkArtistDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkArtistResults['artist']['image_url']+')'
        this.wkArtistDom.nativeElement.style.backgroundPosition = 'center'
        this.wkArtistDom.nativeElement.style.backgroundRepeat = 'no-repeat'
        this.wkArtistDom.nativeElement.style.backgroundSize = 'cover'
      }
      if (this.detectorService.isMobile()) {
        this.wkArtistInput.closePanel()
        this.wkArtistInputRaw.nativeElement.blur();  
      }
      if (data['artist']['fallback'] && !data['artist']['redirect']) {
        this.messageService.open("No one knows \"" + formData['query'] + "\" in " + this.group.name + ". Showing results for " + data['artist']['name'] + ".")
      } else if (data['artist']['redirect']) {
        this.messageService.open("Redirected to " + data['artist']['name'] + ".")
      }
    }).catch(error => {
      if (this.detectorService.isMobile()) {
        this.wkArtistInput.closePanel()
        this.wkArtistInputRaw.nativeElement.blur();  
      }
      this.wkArtistDateLoading = false;
      this.wkArtistInit = false
      if (error['status'] == 404) {
        this.wkArtistInit = undefined;
      } else {
        this.messageService.open("An error occured submitting your request. Please try again.")
        console.log(error)
      }
    })
  }

  artistRedirects(artistString) {
    this.wkArtistRedirectLoading = true
    this.userService.artistRedirects(artistString['query']).toPromise().then(data => {
      this.wkArtistRedirectLoading = false
      if (data['artist']) {
        this.messageService.open("A redirect to \"" + data['artist'] + "\" was found. Adding to database...")
        setTimeout(() => {
          this.wkArtistSubmit(artistString, this.group.members)
        }, 3000)
      } else {
        this.messageService.open("An artist redirect for \"" + artistString['query'] + "\" was not found on Last.fm.")
      }
    }).catch(error => {
      this.wkArtistRedirectLoading = false
      this.messageService.open("An error occured while checking Last.fm for an artist redirect. Please try again.")
    })
  }

  wkAlbumSubmit(formData, users, partialResult=false) {
    if (!partialResult) {
      this.wkAlbumInit = true
      this.wkAlbumResults = null
      this.wkAlbumDom.nativeElement.style.background = ''
      this.userService.wkAlbum(formData['query'], users.map(u => u.id)).toPromise().then(data => {
        this.wkAlbumResults = data
        this.wkAlbumDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkAlbumResults['album']['image_url']+')'
        this.wkAlbumDom.nativeElement.style.backgroundPosition = 'center'
        this.wkAlbumDom.nativeElement.style.backgroundRepeat = 'no-repeat'
        this.wkAlbumDom.nativeElement.style.backgroundSize = 'cover'
        if (this.detectorService.isMobile()) {
          this.wkAlbumInput.closePanel()
          this.wkAlbumInputRaw.nativeElement.blur();
        }
      }).catch(error => {
        if (this.detectorService.isMobile()) {
          this.wkAlbumInput.closePanel()
          this.wkAlbumInputRaw.nativeElement.blur();
        }
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
    } else {
      setTimeout(() => {
        this.wkAlbumInput.openPanel()
      }, 750)
    }
  }

  wkTrackSubmit(formData, users, partialResult=false) {
    if (!partialResult) {
      this.wkTrackInit = true
      this.wkTrackResults = null
      this.wkTrackDom.nativeElement.style.background = ''
      this.userService.wkTrack(formData['query'], users.map(u => u.id)).toPromise().then(data => {
        this.wkTrackResults = data
        this.wkTrackDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkTrackResults['track']['image_url']+')'
        this.wkTrackDom.nativeElement.style.backgroundPosition = 'center'
        this.wkTrackDom.nativeElement.style.backgroundRepeat = 'no-repeat'
        this.wkTrackDom.nativeElement.style.backgroundSize = 'cover'
        if (this.detectorService.isMobile()) {
          this.wkTrackInput.closePanel()
          this.wkTrackInputRaw.nativeElement.blur();
        }
      }).catch(error => {
        if (this.detectorService.isMobile()) {
          this.wkTrackInput.closePanel()
          this.wkTrackInputRaw.nativeElement.blur();
        }
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
    } else {
      setTimeout(() => {
        this.wkTrackInput.openPanel()
      }, 750)
    }
  }

  sort(column, command) {
    if (command == "wkArtist") {
      if (this.wkArtistResults.users.length > 1) {
        if (this.wkArtistResults.users[0][column] < this.wkArtistResults.users[this.wkArtistResults.users.length-1][column]) {
          this.wkArtistResults.users.sort(((a, b) => (a[column] < b[column]) ? 1 : -1))
        } else {
          this.wkArtistResults.users.sort(((a, b) => (a[column] > b[column]) ? 1 : -1))
        }
      }
    } else if (command == "wkAlbum") {
      if (this.wkAlbumResults.users.length > 1) {
        if (this.wkAlbumResults.users[0][column] < this.wkAlbumResults.users[this.wkAlbumResults.users.length-1][column]) {
          this.wkAlbumResults.users.sort(((a, b) => (a[column] < b[column]) ? 1 : -1))
        } else {
          this.wkAlbumResults.users.sort(((a, b) => (a[column] > b[column]) ? 1 : -1))
        }
      }
    } else if (command == "wkTrack") {
      if (this.wkTrackResults.users.length > 1) {
        if (this.wkTrackResults.users[0][column] < this.wkTrackResults.users[this.wkTrackResults.users.length-1][column]) {
          this.wkTrackResults.users.sort(((a, b) => (a[column] < b[column]) ? 1 : -1))
        } else {
          this.wkTrackResults.users.sort(((a, b) => (a[column] > b[column]) ? 1 : -1))
        }
      }
    } else if (command == "charts") {
      if (this.chartResults.length > 1) {
        if (this.chartResults[0][column] < this.chartResults[this.chartResults.length-1][column]) {
          this.chartResults.sort(((a, b) => (a[column] < b[column]) ? 1 : -1))
        } else {
          this.chartResults.sort(((a, b) => (a[column] > b[column]) ? 1 : -1))
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

  nowPlayingToWk(entry, wkArtist: HTMLElement=null, startRange=null, endRange=null) {
    this.wkArtistSuggestions = {'suggestions': [], 'partial_result': false}
    this.wkAlbumSuggestions = {'suggestions': [], 'partial_result': false}
    this.wkTrackSuggestions = {'suggestions': [], 'partial_result': false}
    
    this.wkArtistForm.get('query').setValue(entry.artist)
    this.wkArtistSubmit({'query': entry.artist}, this.group.members)
    this.wkArtistIsCustomDateRange = false
    this.wkArtistSelectedIndex = this.leaderboardSliderMappings.length - 1
    
    if (entry.album !== undefined) {
      let albumQuery = entry.artist + " - " + entry.album
      this.wkAlbumForm.get('query').setValue(albumQuery)
      this.wkAlbumSubmit({'query': albumQuery}, this.group.members)
    }
    
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

  scrobbleLeaderboard(indexValue, users, startRange=null, endRange=null, custom:boolean=false) {
    let startFinal, endFinal
    if (custom) {
      startFinal = startRange.format()
      endFinal = endRange.format()
    } else {
      startFinal = startRange
      endFinal = endRange
    }
    this.userService.scrobbleLeaderboard(users, startFinal, endFinal).toPromise().then(data => {
      this.leaderboardLoadedIndex = indexValue !== null ? indexValue : this.leaderboardLoadedIndex;
      this.leaderboardObject = data
      this.leaderboardLoading = false
      if (this.leaderboardObject.leaderboard.length > 0) {
        this.leaderboardDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.leaderboardObject.leaderboard[0]['profile_image']+')'
        this.leaderboardDom.nativeElement.style.backgroundPosition = 'center'
        this.leaderboardDom.nativeElement.style.backgroundRepeat = 'no-repeat'
        this.leaderboardDom.nativeElement.style.backgroundSize = 'cover'
      } else {
        this.leaderboardDom.nativeElement.style.backgroundImage = 'none'
      }
      if (custom) {
        this.isCustomDateRange = true
        this.customStartDate = startRange
        this.customEndDate = endRange
      }
    }).catch(error => {
      this.messageService.open("There was an issue getting the scrobble leaderboard. Please try again")
      console.log(error)
      this.leaderboardLoading = false
      this.leaderboardLoadedIndex = indexValue !== null ? indexValue : this.leaderboardLoadedIndex;
    })
  }

  onleaderboardSliderChange(event: MatSliderChange) {
    this.leaderboardLoading = true;
    this.leaderboardSelectedIndex = event.value
    this.isCustomDateRange = false;
    this.leaderboardValueSubject.next(event.value);
  }

  onwkArtistSliderChange(event: MatSliderChange) {
    this.wkArtistDateLoading = true;
    this.wkArtistSelectedIndex = event.value
    this.wkArtistIsCustomDateRange = false;
    this.wkArtistValueSubject.next(event.value);
  }

  customDateRange(title) {
    let dialogRef = this.dialog.open(CustomDateRangeComponent, {
      data: {
        'title': title
      }
    })
    let dateSub = dialogRef.componentInstance.submitDateRange.subscribe((data) => {
      if (title == 'Scrobble Leaderboard') {
        this.leaderboardLoading = true
        this.scrobbleLeaderboard(null, this.group.members.map(u => u.id), data.startDate, data.endDate, true)
      } else if (title == 'Individual & Group Charts') {
        this.chartLoading = true
        this.chartCustomStartDate = data.startDate
        this.chartCustomEndDate = data.endDate
        this.charts(data.startDate, data.endDate)
      } else if (title == 'Who Knows This Artist') {
        this.wkArtistDateLoading = true
        this.wkArtistIsCustomDateRange = true
        this.wkArtistCustomStartDate = data.startDate
        this.wkArtistCustomEndDate = data.endDate
        this.wkArtistSubmit({'query': this.wkArtistResults.artist.name}, this.group.members, data.startDate, data.endDate)
      }
    })
    dialogRef.afterClosed().subscribe(() => {
      dateSub.unsubscribe()
    })
  }

  wkAutocomplete(wkMode, event) {
    this.wkAutoSubject.next({'wkMode': wkMode, 'query': event})
  }

  charts(customStartDate: moment.Moment=null, customEndDate: moment.Moment=null) {
    this.chartLoading = true;
    this.chartsDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url("data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==")'
    this.chartResults = null
    let chartMode, users, startRange=null, endRange=null;
    if (this.chartSelectedUser == "all") {
      users = this.group.members.map(u => u.id)
      chartMode = "group"
    } else {
      users = [this.chartSelectedUser]
      chartMode = "individual"
    }
    if (customStartDate && customEndDate) {
      startRange = customStartDate.format()
      endRange = customEndDate.format()
      this.chartIsCustomDate = true
    } else if (this.chartDropdownDate != -1) {
      endRange = moment.utc().format()
      startRange = moment.utc().subtract(this.chartDropdownDate, 'd').format()
      this.chartIsCustomDate = false
    } else {
      this.chartIsCustomDate = false
    }
    this.userService.charts(chartMode, this.chartReleaseType, users, startRange, endRange).toPromise().then(data => {
      this.chartResults = data
      this.chartTopEntry = data[0]
      this.chartLoading = false;
      let imageUrl;
      if (this.chartResults.length > 0) {
        if (this.chartReleaseType == 'track' || this.chartReleaseType == 'album') {
          imageUrl = this.chartResults[0].image
        } else {
          imageUrl = this.chartResults[0].artist_image
        }
        this.chartsDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+imageUrl+')'
        this.chartsDom.nativeElement.style.backgroundPosition = 'center'
        this.chartsDom.nativeElement.style.backgroundRepeat = 'no-repeat'
        this.chartsDom.nativeElement.style.backgroundSize = 'cover'
      }
    }).catch(error => {
      this.chartLoading = false;
      this.messageService.open("Error while trying to generate the chart! Please try again.")
    })
  }

}
