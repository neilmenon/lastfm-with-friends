import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';

@Component({
  selector: 'app-sign-in-username',
  templateUrl: './sign-in-username.component.html',
  styleUrls: ['./sign-in-username.component.css']
})
export class SignInUsernameComponent implements OnInit {
  userForm: UntypedFormGroup
  redirecting: boolean
  
  constructor(
    private userService: UserService,
    private messageService: MessageService,
    private fb: UntypedFormBuilder,
    public router: Router
  ) { }

  ngOnInit(): void {
    this.userForm = this.fb.group({
      lastfmUsername: [null]
    })
  }

  validateUser() {
    this.userService.verifyUserExists(this.userForm.controls['lastfmUsername'].value.trim()).then((code: number) => {
      this.redirecting = true
      this.userForm.disable()
      if (code == 1) {
        this.messageService.open(`Welcome back, ${this.userForm.controls['lastfmUsername'].value.trim()}! Sending you to sign in...`, "center", true)
      } else if (code == 2) {
        this.messageService.open(`Thanks for registering! Sending you to sign in...`, "center", true)
      } else if (code == 2) {
      }
      localStorage.setItem("verifiedUser", "true")
      setTimeout(() => this.router.navigate(['/lastfmauth']), 2000)
    }).catch((error: HttpErrorResponse) => {
      if (error.status == 403) {
        this.messageService.open("Incorrect username or passphrase!")
      } else {
        this.messageService.open("An unknown error occured. Please try again.")
      }
    });
  }

}
