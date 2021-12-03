import { Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { config } from '../config';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';

@Component({
  selector: 'app-switch-user',
  templateUrl: './switch-user.component.html',
  styleUrls: ['./switch-user.component.css']
})
export class SwitchUserComponent implements OnInit {
  users: Array<{ username: string, session_key:string }> = []
  userForm: FormGroup

  constructor(
    public dialogRef: MatDialogRef<SwitchUserComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private userService: UserService,
    private messageService: MessageService,
    private fb: FormBuilder
  ) { }

  ngOnInit(): void {
    this.userForm = this.fb.group({ user: [null] })

    this.userService.getUserSessions().toPromise().then((data: any[]) => {
      this.users = data
    }).catch(() => {
      this.messageService.open("Error getting users. Please try again.")
    })
  }

  cancel() {
    this.dialogRef.close()
  }

  switchUser() {
    localStorage.setItem("prev_lastfm_username", localStorage.getItem("lastfm_username"))
    localStorage.setItem("prev_lastfm_session", localStorage.getItem("lastfm_session"))
    localStorage.setItem("lastfm_username", this.userForm.controls['user'].value?.username)
    localStorage.setItem("lastfm_session", this.userForm.controls['user'].value?.session_key)
    localStorage.setItem("lastfm_show_clear_local", "Y")
    window.location.href = config.project_root
  }

}
