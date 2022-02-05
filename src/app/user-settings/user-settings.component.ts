import { NgRedux, select } from '@angular-redux/store';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { Observable, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { ConfirmPopupComponent } from '../confirm-popup/confirm-popup.component';
import { discreteTimePeriods, releaseTypes } from '../constants';
import { MessageService } from '../message.service';
import { getSettingsModel, SettingsModel } from '../models/settingsModel';
import { TimePeriodModel } from '../models/timePeriodModel';
import { UserModel } from '../models/userGroupModel';
import { AppState } from '../store';
import { UserService } from '../user.service';

@Component({
  selector: 'app-user-settings',
  templateUrl: './user-settings.component.html',
  styleUrls: ['./user-settings.component.css']
})
export class UserSettingsComponent implements OnInit {
  @select(s => s.isDemo)
  isDemo: Observable<boolean>

  private subscription: Subscription = new Subscription()
  user: UserModel;
  confirmFullScrape: boolean = false;
  confirmDeleteAccount: boolean = false;
  fullScrapeInProgress: boolean = false;
  reduxPatched: boolean = false
  signed_in: boolean;
  updateInterval: any;
  settingsForm: FormGroup
  releaseTypes: Array<string> = releaseTypes
  discreteTimePeriods: Array<TimePeriodModel> = discreteTimePeriods
  randomTimePeriod: TimePeriodModel = {days: 0, label: 'Random'}
  constructor(
    private userService: UserService, 
    public messageService: MessageService, 
    public router: Router,
    private fb: FormBuilder,
    private ngRedux: NgRedux<AppState>,
    public dialog: MatDialog
  ) {
    this.signed_in = this.userService.isSignedIn();
    if (this.signed_in) {
      this.userService.getUser().toPromise().then((data: any) => {
        this.user = data
        this.fullScrapeInProgress = this.user.last_update && !this.user.progress? false : true
        this.updateInterval = this.userInterval()
      }).catch(error => {
        this.messageService.open("Error getting data from the backend. Please refresh.");
      })
    } else {
      this.router.navigate(['/'])
    }
  }

  ngOnInit(): void {
    this.userService.setRapidRefresh(true)
    this.settingsForm = this.fb.group({
      chartReleaseType: [null],
      chartTimePeriodDays: [null],
      leaderboardTimePeriodDays: [null],
      trendMode: [null],
      chartUser: [null]
    })

    const sub1 = this.ngRedux.select(s => s.settingsModel).subscribe(obj => {
      if (obj && !this.reduxPatched) {
        this.settingsForm.patchValue(obj, { emitEvent: false })
        this.reduxPatched = true
      }
    })

    const sub2 = this.settingsForm.valueChanges.pipe(debounceTime(200), distinctUntilChanged()).subscribe(() => {
      this.userService.setSettings(getSettingsModel(this.settingsForm.getRawValue()), true)
    })

    this.subscription.add(sub1)
    this.subscription.add(sub2)
  }

  ngOnDestroy() {
    clearInterval(this.updateInterval)
    this.userService.setRapidRefresh(false)
    this.subscription.unsubscribe()
  }

  userInterval() {
    return setInterval(() => {
      if (document.visibilityState == "visible") {
        this.userService.getUser(true).toPromise().then((data: any) => {
          this.user = data
          this.fullScrapeInProgress = this.user.last_update && !this.user.progress? false : true
          console.log("Getting user data for Settings page...")
        })
      }
    }, 10000)
  }

  fullScrape() {
    if (this.confirmFullScrape) {
      this.fullScrapeInProgress = true
      this.userService.updateUser(this.user, true).toPromise().then((data: any) => {
        this.messageService.open("Full scrape successfully triggered for " + this.user.username + ".")
        this.fullScrapeInProgress = false;
        this.confirmFullScrape = false;
      }).catch(error => {
        if (error['status'] == 500) {
          this.messageService.save("A Last.fm network error occured during the scrape. Check the user menu bar for more details.")
          this.router.navigate(['/'])
        }
      })
    } else {
      this.confirmFullScrape = true;
    }
  }

  deleteAccount() {
    if (this.confirmDeleteAccount) {
      this.userService.deleteUser(this.user).toPromise().then((data: any) => {
        this.messageService.open("Your account has been deleted. Thanks for using Last.fm with Friends! Redirecting you...")
        this.signed_in = false
        setTimeout(() => {
          this.userService.clearLocalData()
          window.location.href = ''
        }, 2000)
      }).catch(error => {
        this.confirmDeleteAccount = false
        if (error['status'] == 409) {
          this.messageService.open("Error! You are in one or more groups. You must leave all groups you have joined before deleting your account.")
        } else {
          this.messageService.open("There was an issue while trying to delete your account. Please try again.")
        }
      })
    } else {
      this.confirmDeleteAccount = true
    }
  }

  restoreDefaultSettings() {
    const dialogRef = this.dialog.open(ConfirmPopupComponent, {
      data: { 
        title: "Reset to Default Settings",
        message: "Are you sure you want to reset your settings to their default?",
        primaryButton: "Reset"
      }
    })
    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.userService.setSettings(getSettingsModel(null), true)
        this.settingsForm.patchValue(new SettingsModel(), { emitEvent: false })
      }
    })
  }
}
