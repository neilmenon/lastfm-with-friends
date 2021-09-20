import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, OnDestroy, OnInit, QueryList, ViewChildren } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from '../message.service'
import { UserService } from '../user.service'
import * as moment from 'moment';
import { BuildModel, BuildService } from '../build.service';
import { getSettingsModel, SettingsModel } from '../models/settingsModel';
import { GroupSessionModel, UserModel } from '../models/userGroupModel';
import { NgRedux, select } from '@angular-redux/store';
import { AppState } from '../store';
import { Observable, Subscription } from 'rxjs';
import { IS_DEMO_MODE } from '../actions';
import { config } from '../config';
import { MatDialog } from '@angular/material/dialog';
import { GroupSessionComponent } from '../group-session/group-session.component';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit, OnDestroy {
  @select(s => s.isDemo)
  isDemo: Observable<boolean>
  
  private subscription: Subscription = new Subscription()
  signed_in: boolean = undefined;
  user: UserModel = undefined;
  moment: any = moment;
  commit;
  buildInfo: BuildModel;
  userSettings: SettingsModel

  demoLoading: boolean = false
  @ViewChildren('groupDoms') groupDoms: QueryList<ElementRef>
  constructor(
    public router: Router, 
    public messageService: MessageService, 
    public http: HttpClient, 
    private userService: UserService, 
    private buildService: BuildService,
    private ngRedux: NgRedux<AppState>,
    public dialog: MatDialog
  ) {
    this.signed_in = this.userService.isSignedIn();
    if (this.signed_in) {
      this.userService.getUser().toPromise().then((data: any) => {
        this.user = data;
        // get latest commit hash from build.json
        // this.buildService.getBuildInfo().toPromise().then((data: BuildModel) => {
        //   this.buildInfo = data
        //   this.buildService.getCommitInfo(this.buildInfo.commit).toPromise().then((data: any) => {
        //       this.commit = data
        //   })
        // })
      }).catch(error => {
      })
    }
   }
   
  ngOnInit(): void {
     const sub1 = this.ngRedux.select(s => s.settingsModel).subscribe(obj => {
       if (obj) {
         this.userSettings = obj
       }
     })

     setTimeout(() => {
      const sub2 = this.ngRedux.select(s => s.userModel).subscribe(obj => {
        this.user.group_session = JSON.parse(JSON.stringify(obj?.group_session))
      })
      this.subscription.add(sub2)
     }, 10000)

     this.subscription.add(sub1)
  }
  
  ngOnDestroy(): void {
    this.subscription.unsubscribe()
  }

  toggleGroup(joinCode) {
    if (this.userSettings.groupExpandedList[joinCode] === true || this.userSettings.groupExpandedList[joinCode] === false) {
      this.userSettings.groupExpandedList[joinCode] = !this.userSettings.groupExpandedList[joinCode]
      if (this.userSettings.groupExpandedList[joinCode] == true) {
        setTimeout(() => {
          let target: HTMLElement = this.groupDoms.filter(x => x.nativeElement.id == "group-" + joinCode)[0].nativeElement
          target.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"})
        }, 200)
      }
    } else {
      this.userSettings.groupExpandedList[joinCode] = false
    }
    this.userService.setSettings(this.userSettings, false)
  }

  enterDemo() {
    this.messageService.open("Entering demo mode, please wait...")
    this.demoLoading = true
    setTimeout(() => {
      this.userService.getDemoUser().toPromise().then((response: any) => {
        localStorage.setItem("lastfm_session", response['session_key'])
        localStorage.setItem("lastfm_username", response['username'])
        this.userService.username = response['username']
        this.userService.session_key = response['session_key']
        this.userService.setSettings(getSettingsModel(null), false)
        // this.ngRedux.dispatch({ type: IS_DEMO_MODE, isDemo: true })
        window.location.href = config.project_root
      }).catch(error => {
        console.log(error)
        this.demoLoading = false
        this.messageService.open("There was an issue signing into the demo user! Please try again later. We apologize for the inconvenience.")
      })
    }, 2000)
  }

  exitDemo() {
    this.userService.clearLocalData()
    window.location.href = config.project_root
  }

  openGroupSession(group) {
    let dialogRef = this.dialog.open(GroupSessionComponent, {
      data: {
        group: group,
        user: this.user,
      }
    })

    // when "End Session" or "Leave Session"
    let removeSub = dialogRef.componentInstance.removeSession.subscribe(() => {
      this.user.group_session = null
    })

    // when "Create Session" or "Join Session"
    let createSub = dialogRef.componentInstance.createSessionEmitter.subscribe((data: GroupSessionModel) => {
      this.user.group_session = data
    })

    dialogRef.afterClosed().subscribe(() => {
      removeSub.unsubscribe()
      createSub.unsubscribe()
    })
  }
}