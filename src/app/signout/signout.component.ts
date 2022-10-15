import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';
import { config } from '../config'
import { NgRedux } from '@angular-redux2/store';
import { AppState } from '../store';
import { IS_DEMO_MODE } from '../actions';

@Component({
  selector: 'app-signout',
  templateUrl: './signout.component.html',
  styleUrls: ['./signout.component.css']
})
export class SignoutComponent implements OnInit {

  constructor(
    private messageService: MessageService, 
    private userService: UserService, 
    public router: Router,
    private ngRedux: NgRedux<AppState>
  ) { }

  ngOnInit(): void {
    this.signOut()
  }

  signOut() {
    this.messageService.open('Signing out...');
    this.userService.signOut().toPromise().then(response => {
      localStorage.removeItem("lastfm_session");
      localStorage.removeItem("lastfm_username");
      this.ngRedux.dispatch({ type: IS_DEMO_MODE, isDemo: false })
      window.location.href = config.project_root;
    }).catch(error => {
      this.messageService.save("An error occured while trying to sign you out! Please try again.");
      this.router.navigate(['/'])
    })
  }
}
