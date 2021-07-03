import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from '../message.service'
import { UserService } from '../user.service'
import * as moment from 'moment';
import { BuildModel, BuildService } from '../build.service';
import { SettingsModel } from '../models/settingsModel';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  signed_in: boolean = undefined;
  user: any = undefined;
  moment: any = moment;
  commit;
  buildInfo: BuildModel;
  userSettings: SettingsModel
  constructor(public router: Router, private messageService: MessageService, public http: HttpClient, private userService: UserService, private buildService: BuildService) {
    this.signed_in = this.userService.isSignedIn();
    if (this.signed_in) {
      this.userService.getUser().toPromise().then(data => {
        this.user = data;
        // get latest commit hash from build.json
        this.buildService.getBuildInfo().toPromise().then((data: BuildModel) => {
          this.buildInfo = data
          this.buildService.getCommitInfo(this.buildInfo.commit).toPromise().then(data => {
              this.commit = data
          })
        })
      }).catch(error => {
      })
    }
   }

  ngOnInit(): void {
    this.userSettings = this.userService.getSettings()

  }

  toggleGroup(joinCode) {
    if (this.userSettings.groupExpandedList[joinCode] === true || this.userSettings.groupExpandedList[joinCode] === false) {
      this.userSettings.groupExpandedList[joinCode] = !this.userSettings.groupExpandedList[joinCode]
    } else {
      this.userSettings.groupExpandedList[joinCode] = false
    }
    this.userService.setSettings(this.userSettings)
  }
}
