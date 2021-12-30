import { Component, OnInit, Input, ViewChild, ElementRef } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { FormBuilder, FormGroup } from '@angular/forms';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';
import * as moment from 'moment';
import { ScrobbleHistoryComponent } from '../scrobble-history/scrobble-history.component';
import { WhoKnowsTopComponent } from '../who-knows-top/who-knows-top.component';
import { MatSliderChange } from '@angular/material/slider';
import { BehaviorSubject, Observable, Subscription } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { CustomDateRangeComponent } from '../custom-date-range/custom-date-range.component';
import { MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { DeviceDetectorService } from 'ngx-device-detector';
import { MatOption } from '@angular/material/core';
import { ListeningTrendsComponent } from '../listening-trends/listening-trends.component';
import { SettingsModel } from '../models/settingsModel';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import { discreteTimePeriods, releaseTypes } from '../constants';
import { TimePeriodModel } from '../models/timePeriodModel';
import { UserGroupModel, UserModel } from '../models/userGroupModel';
import { select } from '@angular-redux/store';
import { ConfirmPopupComponent } from '../confirm-popup/confirm-popup.component';
import { HttpScrobbleModel } from '../models/httpScrobbleModel';
import { GenreTopArtistsRecordModel } from '../models/commandsModel';
import { GenreTopArtistsComponent } from '../genre-top-artists/genre-top-artists.component';

@Component({
  selector: 'app-group-dashboard',
  templateUrl: './group-dashboard.component.html',
  styleUrls: ['./group-dashboard.component.css']
})
export class GroupDashboardComponent implements OnInit {
  @select(s => s.isDemo)
  isDemo: Observable<boolean>

  @Input() group: UserGroupModel
  @Input() user: UserModel
  @Input() userSettings: SettingsModel

  moment: any = moment;
  deviceInfo: any = null;

  // mappings for all date sliders/dropdowns
  leaderboardSliderMappings: Array<TimePeriodModel> = discreteTimePeriods;

  // wkArtist
  @ViewChild('wkArtist', { static: true }) wkArtistDom: ElementRef;
  wkArtistForm: FormGroup;
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
  wkAlbumForm: FormGroup;
  wkAlbumResults;
  wkAlbumInit: boolean = false;
  wkAlbumSelectedIndex: number = this.leaderboardSliderMappings.length - 1;
  wkAlbumIsCustomDateRange: boolean = false;
  wkAlbumValueSubject = new BehaviorSubject<number>(1);
  wkAlbumDateLoading: boolean = false;
  wkAlbumCustomStartDate: moment.Moment;
  wkAlbumCustomEndDate: moment.Moment;

  // wkTrack
  @ViewChild('wkTrack', { static: true }) wkTrackDom: ElementRef;
  wkTrackForm: FormGroup;
  wkTrackResults;
  wkTrackInit: boolean = false;
  wkTrackSelectedIndex: number = this.leaderboardSliderMappings.length - 1;
  wkTrackIsCustomDateRange: boolean = false;
  wkTrackValueSubject = new BehaviorSubject<number>(1);
  wkTrackDateLoading: boolean = false;
  wkTrackCustomStartDate: moment.Moment;
  wkTrackCustomEndDate: moment.Moment;

  // nowplaying
  nowPlayingResults: Array<any> = null;
  npInterval: any;
  nowPlayingTimeoutReached: boolean = false;

  // scrobbleLeaderboard
  @ViewChild('scrobbleLeaderboard', { static: true }) leaderboardDom: ElementRef;
  leaderboardSelectedIndex: number = null; // real-time slider value
  leaderboardLoadedIndex: number = null; // http request-dependent value
  leaderboardObject: any;
  leaderboardLoading: boolean = true;
  leaderboardValueSubject: BehaviorSubject<number>
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
  @ViewChild('chartEveryone') private chartEveryoneSelected: MatOption;
  chartSelectedUser: any;
  chartReleaseTypeOptions: Array<string> = releaseTypes;
  chartReleaseType: string;
  chartDropdownDate: number;
  chartLoading: boolean = false;
  chartIsCustomDate: boolean = false;
  chartCustomStartDate: moment.Moment;
  chartCustomEndDate: moment.Moment;
  chartResults;
  chartTopEntry;

  constructor(
    private formBuilder: FormBuilder, 
    private userService: UserService, 
    public messageService: MessageService, 
    public dialog: MatDialog, 
    private detectorService: DeviceDetectorService
  ) {
    moment.locale('en-short', {
      relativeTime: {
        future: 'in %s',
        past: '%s',
        s:  '%ds',
        ss: '%ds',
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

  ngOnInit(): void {
      // initialize setting-dependent configs
      this.chartReleaseType = this.userSettings.chartReleaseType != "random" ? this.userSettings.chartReleaseType : 
      this.chartReleaseTypeOptions[Math.floor(Math.random() * this.chartReleaseTypeOptions.length)]
    
      this.chartDropdownDate = this.userSettings.chartTimePeriodDays == 0 ? 
        this.leaderboardSliderMappings[Math.floor(Math.random() * this.leaderboardSliderMappings.length)].days :
        this.userSettings.chartTimePeriodDays

      let tmpIndex: number = this.leaderboardSliderMappings.findIndex(x => x.days == this.userSettings.leaderboardTimePeriodDays)
      let randomTimePeriodIndex: number = Math.floor(Math.random() * this.leaderboardSliderMappings.length)
      this.leaderboardSelectedIndex = tmpIndex == -1 ? randomTimePeriodIndex : tmpIndex
      this.leaderboardLoadedIndex = this.leaderboardSelectedIndex
      this.leaderboardValueSubject = new BehaviorSubject<number>(this.leaderboardSelectedIndex);
      
      this.deviceInfo = this.detectorService.getDeviceInfo()
      
      // launch charts
      if (this.userSettings.chartUser == "everyone") {
        let negOne = [-1]
        this.chartSelectedUser = negOne.concat(this.group.members.map(u => u.id))
      } else {
        this.chartSelectedUser = [this.user.user_id]
      }
      this.charts()

      // now playing
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
      // wkArtist slider change
      this.wkArtistValueSubject.pipe(debounceTime(1000)).subscribe(value => {
        if (this.wkArtistResults) {
          if (value == this.leaderboardSliderMappings.length-1) { // All time
            this.wkArtistSubmit({'query': this.wkArtistResults.artist.name}, this.group.members, null, null, true)
          } else {
            let endRange = moment.utc()
            let startRange = moment.utc().subtract(this.leaderboardSliderMappings[value]['days'], 'd')
            this.wkArtistSubmit({'query': this.wkArtistResults.artist.name}, this.group.members, startRange, endRange, true)
          }
        }
      })
      // wkAlbum slider change
      this.wkAlbumValueSubject.pipe(debounceTime(1000)).subscribe(value => {
        if (this.wkAlbumResults) {
          if (value == this.leaderboardSliderMappings.length-1) { // All time
            this.wkAlbumSubmit({'query': this.wkAlbumResults.artist.name + " - " + this.wkAlbumResults.album.name}, this.group.members, null, null, true)
          } else {
            let endRange = moment.utc()
            let startRange = moment.utc().subtract(this.leaderboardSliderMappings[value]['days'], 'd')
            this.wkAlbumSubmit({'query': this.wkAlbumResults.artist.name + " - " + this.wkAlbumResults.album.name}, this.group.members, startRange, endRange, true)
          }
        }
      })
      // wkTrack slider change
      this.wkTrackValueSubject.pipe(debounceTime(1000)).subscribe(value => {
        if (this.wkTrackResults) {
          if (value == this.leaderboardSliderMappings.length-1) { // All time
            this.wkTrackSubmit({'query': this.wkTrackResults.artist.name + " - " + this.wkTrackResults.track.name}, this.group.members, null, null, true)
          } else {
            let endRange = moment.utc()
            let startRange = moment.utc().subtract(this.leaderboardSliderMappings[value]['days'], 'd')
            this.wkTrackSubmit({'query': this.wkTrackResults.artist.name + " - " + this.wkTrackResults.track.name}, this.group.members, startRange, endRange, true)
          }
        }
      })
      // scrobble leaderboard slider change
      this.leaderboardValueSubject.pipe(debounceTime(1000)).subscribe(value => {
        if (value == this.leaderboardSliderMappings.length-1) { // All time
          this.scrobbleLeaderboard(value, this.group.members.map(u => u.id))
        } else {
          let endRange = moment.utc()
          let startRange = moment.utc().subtract(this.leaderboardSliderMappings[value]['days'], 'd')
          this.scrobbleLeaderboard(value, this.group.members.map(u => u.id), startRange, endRange)
        }
      })
      // wk autocomplete
      this.wkAutoSubject.pipe(debounceTime(250)).subscribe(value => {
        if (value) {
          this.userService.wkAutocomplete(value['wkMode'], value['query']).toPromise().then((data: any) => {
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
    this.userService.wkArtist(formData['query'], users.map(u => u.id), startRange ? startRange.format() : null, endRange ? endRange.format() : null).toPromise().then((data: any) => {
      if (!fromSliderChange) {
        this.wkArtistDateLoading = true
        this.wkArtistResults = data
        this.wkArtistDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkArtistResults['artist']['image_url']+')'
        this.wkArtistDom.nativeElement.style.backgroundPosition = 'center'
        this.wkArtistDom.nativeElement.style.backgroundRepeat = 'no-repeat'
        this.wkArtistDom.nativeElement.style.backgroundSize = 'cover'
      }
      if (this.detectorService.isMobile()) {
        this.wkArtistInput.closePanel()
        this.wkArtistInputRaw.nativeElement.blur();  
      }
      let wkUsers: Array<number> = data?.users.map(u => u.id)
      this.userService.wkCharts(wkUsers, data.artist.id, null, null, startRange?.format(), endRange?.format()).toPromise().then((results: any) => {
        this.wkArtistDateLoading = false;
        if (results) {
          for (let i = 0; i < results?.length; i++) {
            data?.users.forEach(x => {
              if (results[i].id == x.id) {
                x.rankNum = results[i].rank
              }
            })
          }
        }
        if (fromSliderChange) {
          this.wkArtistResults = data
        }
        if (data['artist']['fallback'] && !data['artist']['redirect']) {
          this.messageService.open("No one knows \"" + formData['query'] + "\" in " + this.group.name + ". Showing results for " + data['artist']['name'] + ".")
        } else if (data['artist']['redirect']) {
          this.messageService.open("Redirected to " + data['artist']['name'] + ".")
        }
      })
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
    this.userService.artistRedirects(artistString['query']).toPromise().then((data: any) => {
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

  wkAlbumSubmit(formData, users, startRange=null, endRange=null, fromSliderChange:boolean=false, partialResult=false) {
    if (!partialResult) {
      this.wkAlbumInit = true
      if (!fromSliderChange) {
        this.wkAlbumResults = null
        this.wkAlbumDom.nativeElement.style.background = ''
      }
      this.userService.wkAlbum(formData['query'], users.map(u => u.id), startRange ? startRange.format() : null, endRange ? endRange.format() : null).toPromise().then((data: any) => {
        // check if this entry is in the top for each user
        if (!fromSliderChange) {
          this.wkAlbumDateLoading = true
          this.wkAlbumResults = data
          this.wkAlbumDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkAlbumResults['album']['image_url']+')'
          this.wkAlbumDom.nativeElement.style.backgroundPosition = 'center'
          this.wkAlbumDom.nativeElement.style.backgroundRepeat = 'no-repeat'
          this.wkAlbumDom.nativeElement.style.backgroundSize = 'cover'
        }
        if (this.detectorService.isMobile()) {
          this.wkAlbumInput.closePanel()
          this.wkAlbumInputRaw.nativeElement.blur();
        }
        let wkUsers: Array<number> = data?.users.map(u => u.id)
        this.userService.wkCharts(wkUsers, data.artist.id, data.album.id, null, startRange?.format(), endRange?.format()).toPromise().then((results: any) => {
          this.wkAlbumDateLoading = false;
          if (results) {
            for (let i = 0; i < results?.length; i++) {
              data?.users.forEach(x => {
                if (results[i].id == x.id) {
                  x.rankNum = results[i].rank
                }
              })
            }
          }
          if (fromSliderChange) {
            this.wkAlbumResults = data
          }
        })
      }).catch(error => {
        if (this.detectorService.isMobile()) {
          this.wkAlbumInput.closePanel()
          this.wkAlbumInputRaw.nativeElement.blur();
        }
        this.wkAlbumDateLoading = false;
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

  wkTrackSubmit(formData, users, startRange=null, endRange=null, fromSliderChange:boolean=false, partialResult=false) {
    if (!partialResult) {
      this.wkTrackInit = true
      if (!fromSliderChange) {
        this.wkTrackResults = null
        this.wkTrackDom.nativeElement.style.background = ''
      }
      this.userService.wkTrack(formData['query'], users.map(u => u.id), startRange ? startRange.format() : null, endRange ? endRange.format() : null).toPromise().then((data: any) => {
        // check if this entry is in the top for each user
        if (!fromSliderChange) {
          this.wkTrackDateLoading = true
          this.wkTrackResults = data
          this.wkTrackDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url('+this.wkTrackResults['track']['image_url']+')'
          this.wkTrackDom.nativeElement.style.backgroundPosition = 'center'
          this.wkTrackDom.nativeElement.style.backgroundRepeat = 'no-repeat'
          this.wkTrackDom.nativeElement.style.backgroundSize = 'cover'
        }
        if (this.detectorService.isMobile()) {
          this.wkTrackInput.closePanel()
          this.wkTrackInputRaw.nativeElement.blur();
        }
        let wkUsers: Array<number> = data?.users.map(u => u.id)
        this.userService.wkCharts(wkUsers, data.artist.id, null, data.track.name, startRange?.format(), endRange?.format()).toPromise().then((results: any) => {
          this.wkTrackDateLoading = false;
          if (results) {
            for (let i = 0; i < results?.length; i++) {
              data?.users.forEach(x => {
                if (results[i].id == x.id) {
                  x.rankNum = results[i].rank
                }
              })
            }
          }
          if (fromSliderChange) {
            this.wkTrackResults = data
          }
        })
      }).catch(error => {
        if (this.detectorService.isMobile()) {
          this.wkTrackInput.closePanel()
          this.wkTrackInputRaw.nativeElement.blur();
        }
        this.wkTrackInit = false
        this.wkTrackDateLoading = false;
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
    this.userService.nowPlaying(this.group.join_code).toPromise().then((data: any) => {
      this.nowPlayingResults = data
    }).catch(error => {
      this.nowPlayingResults = undefined
    })
  }

  nowPlayingToWk(entry, wkArtist: HTMLElement=null, startRange:moment.Moment=null, endRange:moment.Moment=null, fromChart:boolean=false) {
    this.wkArtistSuggestions = {'suggestions': [], 'partial_result': false}
    this.wkAlbumSuggestions = {'suggestions': [], 'partial_result': false}
    this.wkTrackSuggestions = {'suggestions': [], 'partial_result': false}
    
    this.wkArtistForm.get('query').setValue(entry.artist)
    this.wkArtistSubmit({'query': entry.artist}, this.group.members, startRange, endRange)
    if (fromChart) {
      this.wkArtistIsCustomDateRange = this.chartIsCustomDate
      if (!this.chartIsCustomDate) {
        this.wkArtistSelectedIndex = this.leaderboardSliderMappings.findIndex(o => o.days == this.chartDropdownDate)
      } else {
        this.wkArtistCustomStartDate = startRange
        this.wkArtistCustomEndDate = endRange
      }
    } else if (!(startRange && endRange)) {
      this.wkArtistSelectedIndex = this.leaderboardSliderMappings.length - 1
      this.wkArtistIsCustomDateRange = false
    }
    
    if (entry.album !== undefined) {
      let albumFinal = entry.album == '' ? 'Unknown Album' : entry.album
      let albumQuery = entry.artist + " - " + albumFinal
      this.wkAlbumForm.get('query').setValue(albumQuery)
      if (fromChart) {
        this.wkAlbumIsCustomDateRange = this.chartIsCustomDate
        if (!this.chartIsCustomDate) {
          this.wkAlbumSelectedIndex = this.leaderboardSliderMappings.findIndex(o => o.days == this.chartDropdownDate)
        } else {
          this.wkAlbumCustomStartDate = startRange
          this.wkAlbumCustomEndDate = endRange
        }
      } else if (!(startRange && endRange)) {
        this.wkAlbumSelectedIndex = this.leaderboardSliderMappings.length - 1
        this.wkAlbumIsCustomDateRange = false
      }
      this.wkAlbumSubmit({'query': albumQuery}, this.group.members, startRange, endRange)
    }
    
    if (entry.track !== undefined) {
      let trackQuery = entry.artist + " - " + entry.track
      this.wkTrackForm.get('query').setValue(trackQuery)
      if (fromChart) {
        this.wkTrackIsCustomDateRange = this.chartIsCustomDate
        if (!this.chartIsCustomDate) {
          this.wkTrackSelectedIndex = this.leaderboardSliderMappings.findIndex(o => o.days == this.chartDropdownDate)
        } else {
          this.wkTrackCustomStartDate = startRange
          this.wkTrackCustomEndDate = endRange
        }
      } else if (!(startRange && endRange)) {
        this.wkTrackSelectedIndex = this.leaderboardSliderMappings.length - 1
        this.wkTrackIsCustomDateRange = false
      }
      this.wkTrackSubmit({'query': trackQuery}, this.group.members, startRange, endRange)
    }
    
    if (wkArtist)
      wkArtist.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"})
  }

  scrobbleHistory(wkMode, wkObj, users, startRange:moment.Moment=null, endRange:moment.Moment=null, chartUser=null) {
    let tmp = JSON.parse(JSON.stringify(wkObj))
    let wkObject = JSON.parse(JSON.stringify(wkObj))
    if (chartUser) {
      wkObject = {
        'artist': {'id': tmp?.artist_id, 'name': tmp?.artist}, 
        'track': {},
        'album': {}
      }
      if (wkMode == "track") {
        wkObject['track']['name'] = tmp['track']
      } else if (wkMode == "album") {
        wkObject['album']['id'] = tmp['album_id']
        wkObject['album']['name'] = tmp['album']
      }
    }
    if (wkObject)
      wkObject['total_scrobbles'] = tmp['total_scrobbles'] ? tmp['total_scrobbles'] : (tmp['total'] ? tmp['total'] : tmp['scrobbles'])
    let dialogRef = this.dialog.open(ScrobbleHistoryComponent, {
      data: {
        group: this.group,
        wkMode: wkMode,
        wkObject: wkObject,
        users: users,
        user: this.user,
        startRange: startRange,
        endRange: endRange,
        chartUser: chartUser
      }
    })
    let wkSub = dialogRef.componentInstance.wkFromDialog.subscribe((entry: any) => {
      let targetIndex: number, isCustomDate: boolean
      if (entry['isFromChart']) { // who knows called from Charts
        targetIndex = this.leaderboardSliderMappings.findIndex(o => o.days == this.chartDropdownDate)
        isCustomDate = this.chartIsCustomDate
      } else {
        if (wkMode == "track") {
          targetIndex = this.wkTrackSelectedIndex
          isCustomDate = this.wkTrackIsCustomDateRange
        } else if (wkMode == "album") {
          targetIndex = this.wkAlbumSelectedIndex
          isCustomDate = this.wkAlbumIsCustomDateRange
        } else if (wkMode == "artist") {
          targetIndex = this.wkArtistSelectedIndex
          isCustomDate = this.wkArtistIsCustomDateRange
        } else if (wkMode == "overall") {
          targetIndex = this.leaderboardSelectedIndex
          isCustomDate = this.isCustomDateRange
        }
      }
      this.wkTrackSelectedIndex = targetIndex
      this.wkTrackIsCustomDateRange = isCustomDate
      this.wkTrackCustomStartDate = entry['startDate']
      this.wkTrackCustomEndDate = entry['endDate']
      this.wkAlbumSelectedIndex = targetIndex
      this.wkAlbumIsCustomDateRange = isCustomDate
      this.wkAlbumCustomStartDate = entry['startDate']
      this.wkAlbumCustomEndDate = entry['endDate']
      this.wkArtistSelectedIndex = targetIndex
      this.wkArtistIsCustomDateRange = isCustomDate
      this.wkArtistCustomStartDate = entry['startDate']
      this.wkArtistCustomEndDate = entry['endDate']
      this.nowPlayingToWk(entry, null, entry['startDate'], entry['endDate'], false)
    })
    let wkTopSub = dialogRef.componentInstance.wkFromTopDialog.subscribe((data: any) => {
      this.whoKnowsTop(data.wkMode, data.wkObject, data.selectedUser, data['startDate'], data['endDate'])
    })
    dialogRef.afterClosed().subscribe(() => {
      wkSub.unsubscribe()
      wkTopSub.unsubscribe()
    })
  }

  whoKnowsTop(wkMode, wkObject, selectedUser, startRange: moment.Moment, endRange:moment.Moment) {
    let dialogRef = this.dialog.open(WhoKnowsTopComponent, {
      data : {
        group: this.group,
        wkMode: wkMode,
        wkObject: wkObject,
        user: this.user,
        selectedUser: selectedUser,
        startRange: startRange,
        endRange: endRange
      }
    })
    let wkSub = dialogRef.componentInstance.wkFromDialog.subscribe((entry) => {
      let targetIndex: number, isCustomDate: boolean
      if (wkMode == "track") {
        targetIndex = this.wkTrackSelectedIndex
        isCustomDate = this.wkTrackIsCustomDateRange
      } else if (wkMode == "album") {
        targetIndex = this.wkAlbumSelectedIndex
        isCustomDate = this.wkAlbumIsCustomDateRange
      } else if (wkMode == "artist") {
        targetIndex = this.wkArtistSelectedIndex
        isCustomDate = this.wkArtistIsCustomDateRange
      } else if (wkMode == "overall") {
        targetIndex = this.leaderboardSelectedIndex
        isCustomDate = this.isCustomDateRange
      }
      this.wkTrackSelectedIndex = targetIndex
      this.wkTrackIsCustomDateRange = isCustomDate
      this.wkTrackCustomStartDate = entry['startDate']
      this.wkTrackCustomEndDate = entry['endDate']
      this.wkAlbumSelectedIndex = targetIndex
      this.wkAlbumIsCustomDateRange = isCustomDate
      this.wkAlbumCustomStartDate = entry['startDate']
      this.wkAlbumCustomEndDate = entry['endDate']
      this.wkArtistSelectedIndex = targetIndex
      this.wkArtistIsCustomDateRange = isCustomDate
      this.wkArtistCustomStartDate = entry['startDate']
      this.wkArtistCustomEndDate = entry['endDate']
      this.nowPlayingToWk(entry, null, entry['startDate'], entry['endDate'], false)
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
    this.userService.scrobbleLeaderboard(users, startFinal, endFinal).toPromise().then((data: any) => {
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
    this.wkArtistCustomStartDate = null
    this.wkArtistCustomEndDate = null
    this.wkArtistValueSubject.next(event.value);
  }

  onwkAlbumSliderChange(event: MatSliderChange) {
    this.wkAlbumDateLoading = true;
    this.wkAlbumSelectedIndex = event.value
    this.wkAlbumIsCustomDateRange = false;
    this.wkAlbumCustomStartDate = null
    this.wkAlbumCustomEndDate = null
    this.wkAlbumValueSubject.next(event.value);
  }

  onwkTrackSliderChange(event: MatSliderChange) {
    this.wkTrackDateLoading = true;
    this.wkTrackSelectedIndex = event.value
    this.wkTrackIsCustomDateRange = false;
    this.wkTrackCustomStartDate = null
    this.wkTrackCustomEndDate = null
    this.wkTrackValueSubject.next(event.value);
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
      } else if (title == 'Who Knows This Album') {
        this.wkAlbumDateLoading = true
        this.wkAlbumIsCustomDateRange = true
        this.wkAlbumCustomStartDate = data.startDate
        this.wkAlbumCustomEndDate = data.endDate
        this.wkAlbumSubmit({'query': this.wkAlbumResults.artist.name + " - " + this.wkAlbumResults.album.name}, this.group.members, data.startDate, data.endDate)
      } else if (title == 'Who Knows This Track') {
        this.wkTrackDateLoading = true
        this.wkTrackIsCustomDateRange = true
        this.wkTrackCustomStartDate = data.startDate
        this.wkTrackCustomEndDate = data.endDate
        this.wkTrackSubmit({'query': this.wkTrackResults.artist.name + " - " + this.wkTrackResults.track.name}, this.group.members, data.startDate, data.endDate)
      }
    })
    dialogRef.afterClosed().subscribe(() => {
      dateSub.unsubscribe()
    })
  }

  wkAutocomplete(wkMode, event) {
    this.wkAutoSubject.next({'wkMode': wkMode, 'query': event})
  }

  charts(customStartDate: moment.Moment=null, customEndDate: moment.Moment=null, everyoneToggled=false, fromWk=false) {
    if (everyoneToggled) {
      let negOne = [-1]
      if (this.chartEveryoneSelected.selected) {
        this.chartSelectedUser = negOne.concat(this.group.members.map(u => u.id))
      } else {
        this.chartSelectedUser = []
      }
    }
    this.chartLoading = true;
    this.chartsDom.nativeElement.style.backgroundImage = 'linear-gradient(rgba(43, 43, 43, 0.767), rgba(43, 43, 43, 0.829)), url("data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==")'
    this.chartResults = null
    let chartMode, users, startRange=null, endRange=null;
    if (this.chartSelectedUser.length > 1) {
      chartMode = "group"
    } else {
      chartMode = "individual"
    }
    users = this.chartSelectedUser
    if ((customStartDate && customEndDate) || (customStartDate && customEndDate && this.chartDropdownDate == -2)) {
      startRange = customStartDate.format()
      endRange = customEndDate.format()
      this.chartCustomStartDate = customStartDate
      this.chartCustomEndDate = customEndDate
      this.chartIsCustomDate = true
      this.chartDropdownDate = -2
    } else if (this.chartDropdownDate == -2) {
      this.chartIsCustomDate = true
    } else if (this.chartDropdownDate != -1) {
      endRange = moment.utc().format()
      startRange = moment.utc().subtract(this.chartDropdownDate, 'd').format()
      this.chartIsCustomDate = false
      this.chartCustomStartDate = null
      this.chartCustomEndDate = null
    } else {
      this.chartIsCustomDate = false
      this.chartCustomStartDate = null
      this.chartCustomEndDate = null
    }
    if (window.innerWidth <= 960 && fromWk) {
      this.chartsDom.nativeElement.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"})
    } else if (fromWk) {
      this.wkArtistDom.nativeElement.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"})
    }
    this.userService.charts(chartMode, this.chartReleaseType, users, startRange, endRange).toPromise().then((data: any) => {
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

  listeningTrends(cmdMode, wkMode, wkObject, startRange:moment.Moment=null, endRange:moment.Moment=null, userObject=null) {
    let dialogRef = this.dialog.open(ListeningTrendsComponent, {
      data : {
        cmdMode: cmdMode,
        wkMode: wkMode,
        wkObject: wkObject,
        startRange: startRange,
        endRange: endRange,
        group: this.group,
        userObject: userObject
      }
    })
  }

  scrobbleTrack() {
    let entry: HttpScrobbleModel = new HttpScrobbleModel()
    entry.artist = this.wkTrackResults['artist']['name']
    entry.track = this.wkTrackResults['track']['name']
    entry.album = this.wkTrackResults['track']['album_name']
    const dialogRef = this.dialog.open(ConfirmPopupComponent, {
      data: { 
        title: `Scrobble ${entry.artist} - ${entry.track}`,
        message: "Are you sure you want to manually scrobble this track?",
        primaryButton: "Submit Scrobble"
      }
    })
    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.messageService.open(`Scrobbling ${entry.artist} - ${entry.track}...`, "center", true)
        this.userService.getHttpScrobblePayload([entry]).toPromise().then((tracks: Array<any>) => {
          this.userService.scrobbleTrack(tracks[0]).toPromise().then((data: any) => {
            console.log(data)
            this.messageService.open("Successfully submitted scrobble.")
          }).catch(error1 => {
            this.messageService.open("There was an error submitting this scrobble to Last.fm. Please try again.")
          })
        }).catch(error2 => {
          this.messageService.open("There was an error getting the signed object from the backend. Please try again.")
        })
      }
    })
  }

  genreTopArtists(genre: { id: number, name: string }) {
    let dialogRef = this.dialog.open(GenreTopArtistsComponent, { data: { genre } })
    let wkSub = dialogRef.componentInstance.wkFromDialog.subscribe((entry: GenreTopArtistsRecordModel) => {
      this.wkArtistSelectedIndex = this.leaderboardSliderMappings.length - 1
      this.wkArtistIsCustomDateRange = false
      this.wkArtistCustomStartDate = null
      this.wkArtistCustomEndDate = null
      this.nowPlayingToWk(entry, null)
    })
    dialogRef.afterClosed().subscribe(() => {
      wkSub.unsubscribe()
    })
  }

}
