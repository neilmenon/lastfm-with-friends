import { Component, ViewEncapsulation } from '@angular/core';
import * as moment from 'moment';
import { BuildModel, BuildService } from './build.service';
import { MessageService } from './message.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class AppComponent {
  title = 'lastfm-with-friends';

  constructor(private buildService: BuildService, private messageService: MessageService) {
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
