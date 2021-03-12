import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';

@Component({
  selector: 'app-user-settings',
  templateUrl: './user-settings.component.html',
  styleUrls: ['./user-settings.component.css']
})
export class UserSettingsComponent implements OnInit {
  user;
  confirmFullScrape: boolean = false;
  confirmDeleteAccount: boolean = false;
  fullScrapeInProgress: boolean = false;
  signed_in: boolean;
  updateInterval;
  constructor(private userService: UserService, public messageService: MessageService, public router: Router) {
    this.signed_in = this.userService.isSignedIn();
    if (this.signed_in) {
      this.userService.getUser().toPromise().then(data => {
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

  }

  ngOnDestroy() {
    clearInterval(this.updateInterval)
  }

  userInterval() {
    return setInterval(() => {
      if (document.visibilityState == "visible") {
        this.userService.getUser(true).toPromise().then(data => {
          this.user = data
          this.fullScrapeInProgress = this.user.last_update && !this.user.progress? false : true
          console.log("Getting user data from Settings page...")
        })
      }
    }, 10000)
  }

  fullScrape() {
    if (this.confirmFullScrape) {
      this.fullScrapeInProgress = true
      this.userService.setUpdateInterval(5000)
      this.userService.updateUser(this.user, true).toPromise().then(data => {
        this.messageService.open("Full scrape complete!")
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
      this.userService.deleteUser(this.user).toPromise().then(data => {
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

}
