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
import { NgRedux } from '@angular-redux/store';
import { AppState } from '../store';
import { SETTINGS_MODEL, USER_MODEL } from '../actions'
import { getSettingsModel, SettingsModel } from '../models/settingsModel';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent implements OnInit, OnDestroy {
  private subscription: Subscription = new Subscription()
  signed_in: boolean = undefined;
  user: UserModel = undefined;
  settingsModel: SettingsModel
  moment: any = moment;
  userUpdateInterval: any = 30000;
  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset).pipe(map(result => result.matches), shareReplay());
  initUpdate: boolean = true
  constructor(
    private breakpointObserver: BreakpointObserver, 
    private userService: UserService, 
    public dialog: MatDialog, 
    private messageService: MessageService,
    private ngRedux: NgRedux<AppState>
  ) {
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
        this.ngRedux.dispatch({ type: USER_MODEL, userModel: this.user })
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
}
