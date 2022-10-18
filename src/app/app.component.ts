import { NgRedux } from '@angular-redux2/store';
import { Component, ViewEncapsulation } from '@angular/core';
import * as moment from 'moment';
import { IS_DEMO_MODE } from './actions';
import { BuildModel, BuildService } from './build.service';
import { config } from './config';
import { MessageService } from './message.service';
import { UserModel } from './models/userGroupModel';
import { ObservableStore } from './observable-store';
import { AppState } from './store';
import { UserService } from './user.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class AppComponent {
  title = 'lastfm-with-friends';
  user: UserModel;
  constructor(
    private buildService: BuildService, 
    private messageService: MessageService,
    private ngRedux: ObservableStore<AppState>
    ) {
    this.ngRedux.dispatch({ type: IS_DEMO_MODE, isDemo: localStorage.getItem("lastfm_username") == config.demo_user })
    const sub1 = this.ngRedux.select(s => s.userModel).subscribe(obj => {
      if (obj) {
        this.user = obj
      }
    })
    
    let currentBuildUnix: number = null
    let currentCommitHash: string = null
    let interval = setInterval(() => {
      if (document.visibilityState == "visible") {
        this.buildService.getBuildInfo().toPromise().then((data: BuildModel) => {
          if (data.unixTimestamp) {
            if (!currentBuildUnix || !currentCommitHash) { // load into current app state once
              currentBuildUnix = data.unixTimestamp
              currentCommitHash = data.commit
            } else {
              if (currentBuildUnix != data.unixTimestamp && currentCommitHash != data.commit) {
                this.messageService.open("New app changes published! Reload to view the latest version.", "center", true)
                clearInterval(interval)
              }
            }

          }
        }).catch(error => {
          console.log("Error getting latest build info. See below:")
          console.log(error)
        })
      }
    }, 60000)
  }
}
