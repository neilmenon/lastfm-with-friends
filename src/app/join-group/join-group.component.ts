import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { Router } from '@angular/router';
import { MessageService } from '../message.service';
import { FormBuilder } from '@angular/forms';
import { Validators } from '@angular/forms';
import { UserService } from '../user.service';

@Component({
  selector: 'app-join-group',
  templateUrl: './join-group.component.html',
  styleUrls: ['./join-group.component.css']
})
export class JoinGroupComponent implements OnInit {
  joinForm;
  joinLoading: boolean = false;
  @Output() joinSuccess: EventEmitter<any> = new EventEmitter(true)
  constructor( 
    private formBuilder: FormBuilder, 
    private messageService: MessageService, 
    private userService: UserService,
    public router: Router,
  ) { 
    this.joinForm = this.formBuilder.group({
      joinCode: ['', Validators.required],
    });
  }

  ngOnInit(): void {
  }

  onSubmit(formData) {
    if (this.joinForm.status == "VALID") {
      this.joinLoading = true
      this.userService.joinGroup(formData['joinCode']).toPromise().then(data => {
        this.joinLoading = false
        this.messageService.save("You have joined " + data['name'] + ".")
        this.joinSuccess.emit()
        this.router.navigate(['groups/' + data['join_code']])
      }).catch(error => {
        this.joinLoading = false
        console.log(error)
        if (error['status'] == 409) {
          this.messageService.open("You are already in this group.")
        } else if (error['status'] == 404) {
          this.messageService.open("A group with this join code was not found.")
        } else {
          this.messageService.open("An unexpected error occurred. Please try again.")
        }
      })
    }
  }
}
