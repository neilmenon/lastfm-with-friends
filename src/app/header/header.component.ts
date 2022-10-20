import { Component, OnDestroy, OnInit } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable, Subscription } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import { UserService } from '../user.service';
import * as moment from 'moment';
import { MatDialog } from '@angular/material/dialog';
import { MessageService } from '../message.service';
import { JoinGroupComponent } from '../join-group/join-group.component';
import { UserModel } from '../models/userGroupModel';
import { NgRedux, Select } from '@angular-redux2/store';
import { AppState } from '../store';
import { SETTINGS_MODEL, USER_MODEL } from '../actions'
import { getSettingsModel, SettingsModel } from '../models/settingsModel';
import { Router } from '@angular/router';
import { config } from '../config';
import { ConfirmPopupComponent } from '../confirm-popup/confirm-popup.component';
import { SwitchUserComponent } from '../switch-user/switch-user.component';
import { FaqsComponent } from '../faqs/faqs.component';
import { CreditsComponent } from '../credits/credits.component';
import { GenericTextComponent } from '../home/home.component';
import { ObservableStore, select } from '../observable-store';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent implements OnInit, OnDestroy {
  @select(s => s.isDemo)
  isDemo: Observable<boolean>

  private subscription: Subscription = new Subscription()
  signed_in: boolean = undefined;
  user: UserModel = undefined;
  settingsModel: SettingsModel
  moment: any = moment;
  userUpdateInterval: any = 30000;
  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset).pipe(map(result => result.matches), shareReplay());
  initUpdate: boolean = true
  config: any = config
  showClearLocalData: boolean = localStorage.getItem("lastfm_show_clear_local") == "Y"

  constructor(
    private breakpointObserver: BreakpointObserver, 
    private userService: UserService, 
    public dialog: MatDialog, 
    private messageService: MessageService,
    private ngRedux: ObservableStore<AppState>,
    public router: Router
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
    
    this.signed_in = this.userService.isSignedIn();
    if (this.signed_in) {
      this.checkUserUpdate()
    } else {
      this.user = null;
    }
  }
  
  checkUserUpdate() {
    if (document.visibilityState == "visible") {
      this.userService.getUser(true).toPromise().then((data: any) => {
        this.user = data

        // put user and settings DTOs into Redux
        this.ngRedux.dispatch({ type: USER_MODEL, userModel: JSON.parse(JSON.stringify(this.user)) })
        if (!this.settingsModel) {
          this.ngRedux.dispatch({ type: SETTINGS_MODEL, settingsModel: getSettingsModel(this.user?.settings) })
        }

        if (!this.user.last_update || this.userService.isRapidRefresh()) {
          this.userUpdateInterval = 5000
        } else {
          this.userUpdateInterval = 30000
        }
        window.setTimeout(() => { this.checkUserUpdate() }, this.userUpdateInterval)
        // console.log("Checking for user update @ interval of " + this.userUpdateInterval + " ms.")
      }).catch(error => {
        if (error['status'] == 404 && this.initUpdate) {
          this.userService.clearLocalData()
        } else if (error['status'] == 401) {
          this.userService.clearLocalData()
        }
        this.user = null;
        this.messageService.open("Error getting data from the backend. Please refresh.");
      })
    } else {
      window.setTimeout(() => { this.checkUserUpdate() }, 5000)
      // console.log("[tab unfocused] Checking if tab in focus @ interval of 5000 ms.")
    }
    this.initUpdate = false
  }
  
  ngOnInit() {
    const settingsSub = this.ngRedux.select(s => s.settingsModel).subscribe(result => {
      this.settingsModel = result
    })
    
    this.subscription.add(settingsSub)
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe()
  }
  
  updateUser() {
    let tmp = this.user.last_update
    this.user.last_update = null
    this.userService.updateUser(this.user, false).toPromise().then((data: any) => {
      if (data['last_update']) {
        this.user.last_update = data['last_update']
      }
      if (data['progress']) {
        this.user.progress = data['progress']
      }
      if (data['message']) {
        this.messageService.open(data['message'])
      } else {
        if (data['tracks_fetched'] == -1) {
          this.user.last_update = tmp
          this.messageService.open("You are up to date!")
        } else if (data['tracks_fetched'] == 1) {
          this.user.last_update = data['last_update']
          this.messageService.open("Fetched 1 new track for " + this.user.username + ".")
        } else {
          this.user.last_update = data['last_update']
          this.messageService.open("Fetched "+data['tracks_fetched']+" new tracks for " + this.user.username + ".")
        }
      }
      if (!data['progress'])
        this.user.progress = 0
    }).catch(error => {
        this.user.last_update = tmp
        this.messageService.open("Error while updating your user scrobbles!")
    })
  }

  openJoinDialog() {
    let dialogRef = this.dialog.open(JoinGroupComponent)
    dialogRef.componentInstance.joinSuccess.subscribe(() => {
      this.dialog.closeAll()
    })
  }

  exitDemo() {
    this.userService.clearLocalData()
    window.location.href = config.project_root
  }

  signOut() {
    const dialogRef = this.dialog.open(ConfirmPopupComponent, {
      data: { 
        title: "Sign Out",
        message: "Are you sure you want to sign out?",
        primaryButton: "Confirm"
      }
    })
    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.router.navigate(['/signout'])
      }
    })
  }

  switchUser() {
    this.dialog.open(SwitchUserComponent)
  }

  switchBack() {
    let prev_username: string = localStorage.getItem("prev_lastfm_username")
    let prev_session: string = localStorage.getItem("prev_lastfm_session")
    if (prev_username && prev_session) {
      this.userService.clearLocalData()
      localStorage.setItem("lastfm_username", prev_username)
      localStorage.setItem("lastfm_session", prev_session)
    } else {
      this.userService.clearLocalData()
    }
    setTimeout(() => {
      window.location.href = config.project_root
    }, 200)
  }

  openFaqs() {
    this.dialog.open(FaqsComponent)
  }

  openCredits() {
    this.dialog.open(CreditsComponent)
  }

  openMobileInstructions() {
    let text: string = `Although there is no mobile app available for iOS or Android at this time, the app was designed for mobile. Using the "add to home screen" feature on your phone will give a near-native mobile experience! For instructions on how to do that for Apple / Android devices, you can reference <a href="https://natomasunified.org/kb/add-website-to-mobile-device-home-screen/" target="_blank">this article</a>.`
    this.dialog.open(GenericTextComponent, { data: { text: text, title: "Last.fm with Friends for Mobile" } })
  }
}
