import { Component } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import { UserService } from '../user.service';
import { ChangeDetectorRef } from '@angular/core';
import * as moment from 'moment';
import { MatDialog } from '@angular/material/dialog';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent {
  signed_in: boolean = undefined;
  user: any;
  moment: any = moment;
  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(private breakpointObserver: BreakpointObserver, private userService: UserService, public dialog: MatDialog) {
    this.userService.getUser().toPromise().then(data => {
      this.user = data
      this.signed_in = this.userService.isSignedIn();
    }).catch(error => {
      this.signed_in = this.userService.isSignedIn();
    })
  }

  ngOnInit() {
    
  }

}
