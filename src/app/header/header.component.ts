import { Component } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import { UserService } from '../user.service';
import { ChangeDetectorRef } from '@angular/core';
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
  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset).pipe(map(result => result.matches), shareReplay());

  constructor(private breakpointObserver: BreakpointObserver, private userService: UserService, public dialog: MatDialog, private messageService: MessageService) {
    this.signed_in = this.userService.isSignedIn();
    if (this.signed_in) {
      this.userService.getUser().toPromise().then(data => {
        this.user = data
        setInterval(() => {
          if (document.visibilityState == "visible") {
            this.userService.getUser(true).toPromise().then(data => {
              console.log("Checking for user update...")
              this.user = data
            })
          }
        }, 30000)
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

  ngOnInit() {
    
  }

}
