import { Component } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import { UserService } from '../user.service';
import * as moment from 'moment';
import { MatDialog } from '@angular/material/dialog';
import { MessageService } from '../message.service';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent {
  signed_in: boolean = undefined;
  user: any = undefined;
  moment: any = moment;
  userUpdateInterval: any = 30000;
  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset).pipe(map(result => result.matches), shareReplay());

  constructor(private breakpointObserver: BreakpointObserver, private userService: UserService, public dialog: MatDialog, private messageService: MessageService) {
    this.signed_in = this.userService.isSignedIn();
    if (this.signed_in) {
      this.userService.getUser().toPromise().then(data => {
        this.user = data
        this.checkUserUpdate()
      }).catch(error => {
        if (error['status'] == 404) {
          this.userService.clearLocalData()
        }
        this.user = null;
        this.messageService.open("Error getting data from the backend. Please refresh.");
      })
    } else {
      this.user = null;
    }
  }

  checkUserUpdate() {
    if (document.visibilityState == "visible") {
      this.userService.getUser(true).toPromise().then(data => {
        this.user = data
        this.userUpdateInterval = this.userService.getUpdateInterval()
        if (!this.user.last_update) {
          this.userUpdateInterval = this.userService.setUpdateInterval(5000)
        } else {
          this.userUpdateInterval = this.userService.setUpdateInterval(30000)
        }
        console.log("Checking for user update @ interval of " + this.userUpdateInterval + " ms.")
        window.setTimeout(() => { this.checkUserUpdate() }, this.userUpdateInterval)
      })
    }
  }

  ngOnInit() {
    
  }

  updateUser() {
    let tmp = this.user.last_update
    this.user.last_update = null
    this.userService.updateUser(this.user, false).toPromise().then(data => {
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
}
