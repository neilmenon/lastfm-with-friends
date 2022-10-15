import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, Inject, OnDestroy, OnInit, QueryList, ViewChildren } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from '../message.service'
import { UserService } from '../user.service'
import * as moment from 'moment';
import { BuildModel, BuildService } from '../build.service';
import { getSettingsModel, SettingsModel } from '../models/settingsModel';
import { GroupSessionMemberModel, GroupSessionModel, UserModel } from '../models/userGroupModel';
import { NgRedux, Select } from '@angular-redux2/store';
import { AppState } from '../store';
import { Observable, Subscription } from 'rxjs';
import { IS_DEMO_MODE, USER_MODEL } from '../actions';
import { config } from '../config';
import { MatDialog, MatDialogRef, MatDialogState, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { GroupSessionComponent } from '../group-session/group-session.component';
import { PluralizePipe } from '../pluralize.pipe';
import { GettingStartedComponent } from '../getting-started/getting-started.component';
import { SignInUsernameComponent } from '../sign-in-username/sign-in-username.component';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit, OnDestroy {
  @Select(s => s.isDemo)
  isDemo: Observable<boolean>
  
  private subscription: Subscription = new Subscription()
  signed_in: boolean = undefined;
  user: UserModel = undefined;
  moment: any = moment;
  commit;
  buildInfo: BuildModel;
  userSettings: SettingsModel
  now = moment()
  dialogRef: MatDialogRef<GroupSessionComponent, any>

  demoLoading: boolean = false
  @ViewChildren('groupDoms') groupDoms: QueryList<ElementRef>
  constructor(
    public router: Router, 
    public messageService: MessageService, 
    public http: HttpClient, 
    private userService: UserService, 
    private buildService: BuildService,
    private ngRedux: NgRedux<AppState>,
    public dialog: MatDialog,
    private pluralizePipe: PluralizePipe
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
        if (obj) {
          // Notifications for people joining/leaving the session
          if (obj.group_session && this.user.group_session && this.dialogRef?.getState() != MatDialogState.OPEN) {
            if (obj.group_session.members.length < this.user.group_session.members.length) { // user(s) left session
              let leftSession: Array<GroupSessionMemberModel> = this.user.group_session.members.filter(this.compareUsers(obj.group_session.members))
              if (leftSession.length > 0) {
                let listMembers: string = this.mapMembers(leftSession)
                this.messageService.open(`${listMembers} left the session.`)
              }
            } else if (obj.group_session.members.length > this.user.group_session.members.length) { // user(s) joined session
              let joinedSession: Array<GroupSessionMemberModel> = obj.group_session.members.filter(this.compareUsers(this.user.group_session.members))
              if (joinedSession.length > 0) {
                let listMembers: string = this.mapMembers(joinedSession)
                this.messageService.open(`${listMembers} joined the session.`)
              }
            }
          }
          this.user.group_session = JSON.parse(JSON.stringify(obj?.group_session))
          this.user.last_update = obj?.last_update
        }
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
    this.dialogRef = this.dialog.open(GroupSessionComponent, {
      data: {
        group: group,
        user: this.user,
      }
    })

    // when "End Session" or "Leave Session"
    let removeSub = this.dialogRef.componentInstance.removeSession.subscribe(() => {
      this.user.group_session = null
      this.ngRedux.dispatch({ type: USER_MODEL, userModel: JSON.parse(JSON.stringify(this.user)) })
    })

    // when "Create Session" or "Join Session"
    let createSub = this.dialogRef.componentInstance.createSessionEmitter.subscribe((data: GroupSessionModel) => {
      this.user.group_session = data
      this.ngRedux.dispatch({ type: USER_MODEL, userModel: JSON.parse(JSON.stringify(this.user)) })
    })

    this.dialogRef.afterClosed().subscribe(() => {
      removeSub.unsubscribe()
      createSub.unsubscribe()
    })
  }

  compareUsers(otherArray: Array<GroupSessionMemberModel>) {
    return (current: GroupSessionMemberModel) => {
      return otherArray.filter((other) => {
        return other.username == current.username
      }).length == 0
    }
  }

  mapMembers(members: Array<any>) {
    if (members.length == 1) { return members[0]['username'] }
    const input = members.map(x => x.username)
    const last = input.pop()
    const result = input.join(', ') + ' and ' + last
    return result
  }

  gettingStarted() {
    this.dialog.open(GettingStartedComponent)
  }

  openPersonalStatsInfo() {
    let text: string = `Personal stat reports are generated daily. The time period used to calculate the stats varies per user, based on how much you listen.<br><br>This report was generated on <strong><u>${ moment(this.user.stats?.date_generated).local().format() }</u></strong> with a time period of <strong><u>${this.user.stats?.time_period_days} days</u></strong> until <em>today</em> (which means the stats will change slightly each day).`
    this.dialog.open(GenericTextComponent, { data: { text: text, title: "About Personal Stats Report" } })
  }

  validateUser() {
    this.dialog.open(SignInUsernameComponent)
  }
}

@Component({
  selector: 'generic-text-component',
  template: '<h3 mat-dialog-title class="center">{{ data.title }}</h3> <div [innerHTML]="data.text" class="center"></div>'
})
export class GenericTextComponent {
  constructor(@Inject(MAT_DIALOG_DATA) public data: {text: string, title: string}) {

  }
}