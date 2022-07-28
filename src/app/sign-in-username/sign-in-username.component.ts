import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';

@Component({
  selector: 'app-sign-in-username',
  templateUrl: './sign-in-username.component.html',
  styleUrls: ['./sign-in-username.component.css']
})
export class SignInUsernameComponent implements OnInit {
  userForm: FormGroup
  
  constructor(
    private userService: UserService,
    private messageService: MessageService,
    private fb: FormBuilder,
    public router: Router
  ) { }

  ngOnInit(): void {
    this.userForm = this.fb.group({
      lastfmUsername: [null]
    })
  }

  validateUser() {
    this.userService.verifyUserExists(this.userForm.controls['lastfmUsername'].value.trim()).then(() => {
      this.messageService.open(`Welcome back, ${this.userForm.controls['lastfmUsername'].value.trim()}! Sending you to sign in...`, "center", true)
      localStorage.setItem("verifiedUser", "true")
      setTimeout(() => this.router.navigate(['/lastfmauth']), 2000)
    }).catch((error: HttpErrorResponse) => {
      if (error.status == 404) {
        this.messageService.open("This user is not registered with Last.fm with Friends.")
      } else {
        this.messageService.open("An unknown error occured while trying to validate your user. Please try again.")
      }
    });
  }

}
