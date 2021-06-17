import { Component } from '@angular/core';
import * as moment from 'moment';
import { BuildModel, BuildService } from './build.service';
import { MessageService } from './message.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'lastfm-with-friends';

  constructor(private buildService: BuildService, private messageService: MessageService) {
    let currentBuildUnix: number = null
    let interval = setInterval(() => {
      if (document.visibilityState == "visible") {
        this.buildService.getBuildInfo().toPromise().then((data: BuildModel) => {
          if (data.unixTimestamp) {
            if (!currentBuildUnix) { // load into current app state once
              currentBuildUnix = data.unixTimestamp
            } else {
              if (currentBuildUnix != data.unixTimestamp) {
                // let buildDate: moment.Moment = moment.unix(data.unixTimestamp).locale('en')
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
    }, 10000)
  }
}
