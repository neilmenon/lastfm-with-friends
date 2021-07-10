import { Component, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';


@Component({
  selector: 'app-create-group',
  templateUrl: './create-group.component.html',
  styleUrls: ['./create-group.component.css']
})
export class CreateGroupComponent implements OnInit {
  groupForm;
  createLoading: boolean = false;
  constructor( private formBuilder: FormBuilder, private messageService: MessageService, private userService: UserService, public router: Router) { 
    this.groupForm = this.formBuilder.group({
      name: ['', Validators.required],
      description: ['', Validators.required]
    });
  }

  ngOnInit(): void {
  }

  onSubmit(formData) {
    if (this.groupForm.status == "VALID") {
      this.createLoading = true
      this.userService.createGroup(formData).toPromise().then((data: any) => {
        this.createLoading = false
        this.messageService.save('Successfully created group '+data['name']+'.')
        this.router.navigate(['groups/' + data['join_code']])
      }).catch(error => {
        this.createLoading = false
        this.messageService.open("Error creating group!")
        console.log(error)
      })
    }
  }
}
