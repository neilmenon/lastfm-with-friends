import { Component, EventEmitter, Inject, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSelectChange } from '@angular/material/select';
import * as moment from 'moment';
import { ConfirmPopupComponent } from '../confirm-popup/confirm-popup.component';
import { MessageService } from '../message.service';
import { GroupSessionModel, MemberModel, UserGroupModel, UserModel } from '../models/userGroupModel';
import { UserService } from '../user.service';

@Component({
  selector: 'app-group-session',
  templateUrl: './group-session.component.html',
  styleUrls: ['./group-session.component.css']
})
export class GroupSessionComponent implements OnInit {
  user: UserModel
  session: GroupSessionModel
  moment: any = moment
  leaveEndLoading: boolean = false
  cForm: FormGroup
  groupMembersForDropdown: Array<MemberModel>
  recentTracks: Array<any> = []
  enableCatchUp: boolean = false
  playHistoryLoading: boolean
  createLoading: boolean
  existingSessions: Array<GroupSessionModel> = []
  selectedSession: GroupSessionModel
  joinLoading: boolean
  isJoinCatchUp: boolean = false
  joinCatchUpTimestamp: string

  @Output() removeSession: EventEmitter<any> = new EventEmitter(true)
  @Output() createSessionEmitter: EventEmitter<GroupSessionModel> = new EventEmitter(true)

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialog: MatDialog,
    private userService: UserService,
    public messageService: MessageService,
    public dialogRef: MatDialogRef<GroupSessionComponent>,
    private fb: FormBuilder
  ) { 
    this.user = data.user
    this.session = data.user.group_session
    this.groupMembersForDropdown = data.group.members.filter(x => x.username != this.user.username)
  }

  ngOnInit(): void {
    if (!this.session || (this.session.is_silent == true && this.user.username == this.session.owner)) {
      this.createForm()
      this.userService.getSessions(this.data.group.join_code).toPromise().then((data: Array<GroupSessionModel>) => {
        this.existingSessions = data
      }).catch(error => {
        this.messageService.open("There was an issue getting this group's active sessions. Please try again.")
      })
    }
  }

  createForm() {
    this.cForm = this.fb.group({ 
      is_silent: [null, Validators.required],
      group_jc: [this.data.group.join_code],
      silent_followee: [null],
      catch_up_timestamp: [null]
    })

    this.cForm.valueChanges.subscribe(() => {
      console.log(this.cForm.getRawValue())
    })
    
    this.cForm.controls['is_silent'].valueChanges.subscribe(() => {
      this.cForm.controls['silent_followee'].setValue(null, { emitEvent: false })
      this.cForm.controls['silent_followee'].markAsUntouched()
      this.cForm.controls['catch_up_timestamp'].setValue(null, { emitEvent: false })
      this.cForm.controls['catch_up_timestamp'].markAsUntouched()
      if (this.cForm.controls['is_silent'].value == true) {
        this.cForm.controls['silent_followee'].setValidators(Validators.required)
      } else {
        this.cForm.controls['silent_followee'].setValidators([])
        this.cForm.controls['catch_up_timestamp'].setValidators([])
      }
      this.cForm.controls['silent_followee'].updateValueAndValidity({ emitEvent: false })
      this.cForm.controls['catch_up_timestamp'].updateValueAndValidity({ emitEvent: false })
    })
  }

  leaveSession() {
    const dialogRef = this.dialog.open(ConfirmPopupComponent, {
      data: { 
        title: "Leave Session",
        message: "Are you sure you want to leave this session?",
        primaryButton: "Confirm"
      }
    })
    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.leaveEndLoading = true
        this.userService.leaveSession(this.session.id).toPromise().then(() => {
          this.leaveEndLoading = false
          this.messageService.open("Successfully left session.")
          this.removeSession.emit(true)
          this.dialogRef.close()
        }).catch(error => {
          this.leaveEndLoading = false
          if (error['error']['error']) {
            this.messageService.open(error['error']['error'])
          }
        })
      }
    })
  }

  endSession() {
    const dialogRef = this.dialog.open(ConfirmPopupComponent, {
      data: { 
        title: "End Session",
        message: "Are you sure you want to end this session?",
        primaryButton: "Confirm"
      }
    })
    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.leaveEndLoading = true
        this.userService.endSession(this.session.id).toPromise().then(() => {
          this.leaveEndLoading = false
          this.messageService.open("Successfully ended session.")
          this.removeSession.emit(true)
          this.dialogRef.close()
        }).catch(error => {
          this.leaveEndLoading = false
          if (error['error']['error']) {
            this.messageService.open(error['error']['error'])
          }
        })
      }
    })
  }

  createSession() {
    this.leaveEndLoading = true
    this.userService.createSession(this.cForm.getRawValue()).toPromise().then((data: GroupSessionModel) => {
      this.leaveEndLoading = false
      this.messageService.open("Successfully created session.")
      this.createSessionEmitter.emit(data)
      this.dialogRef.close()
    }).catch(error => {
      this.leaveEndLoading = false
      if (error['error']['error']) {
        this.messageService.open(error['error']['error'])
      }
    })
  }

  joinSession() {
    if (!this.isJoinCatchUp) {
      this.joinCatchUpTimestamp = null
    }
    this.joinLoading = true
    this.userService.joinSession(this.selectedSession.id, this.joinCatchUpTimestamp).toPromise().then((data: GroupSessionModel) => {
      this.joinLoading = false
      this.messageService.open("Successfully joined session.")
      this.createSessionEmitter.emit(data)
      this.dialogRef.close()
    }).catch(error => {
      this.joinLoading = false
      if (error['error']['error']) {
        this.messageService.open(error['error']['error'])
      }
    })

  }

  selectSession(selected: MatSelectChange) {
    this.selectedSession = selected.value
    this.joinCatchUpTimestamp = null
  }

  getPlayHistory(selected: any, joinMode=false) {
    if (!selected) { 
      selected = { 
        "value": joinMode ? this.selectedSession.owner : this.cForm.controls['silent_followee'].value 
      } 
    }
    this.recentTracks = []
    if (!joinMode) {
      if (this.enableCatchUp) {
        this.cForm.controls['catch_up_timestamp'].setValue(null)
        this.cForm.controls['catch_up_timestamp'].setValidators(Validators.required)
        this.cForm.controls['catch_up_timestamp'].updateValueAndValidity()
        this.cForm.controls['catch_up_timestamp'].markAsUntouched()
      } else {
        this.cForm.controls['catch_up_timestamp'].setValue(null)
        this.cForm.controls['catch_up_timestamp'].setValidators([])
        this.cForm.controls['catch_up_timestamp'].updateValueAndValidity()
        this.cForm.controls['catch_up_timestamp'].markAsUntouched()
      }
    }
    if ((this.enableCatchUp && !joinMode) || (this.isJoinCatchUp && joinMode)) {
      this.playHistoryLoading = true
      this.userService.getRecentTracks(selected.value).toPromise().then((data: any) => {
        this.recentTracks = data['recenttracks']['track'].filter(x => typeof(x['date']) !== "undefined")
        if (!joinMode) {
          this.cForm.controls['catch_up_timestamp'].setValue(this.recentTracks[0].date.uts)
        }
        this.playHistoryLoading = false
      }).catch(error => {
        this.messageService.open(`There was an issue getting ${selected.value}'s recent tracks. Please try again.'`)
        this.playHistoryLoading = false
      })
    }
  }

  mapMembers(members: Array<any>) {
    if (members.length == 1) { return members[0]['username'] }
    const input = members.map(x => x.username)
    const last = input.pop()
    const result = input.join(', ') + ' and ' + last
    return result
  }
}
