import { Component, OnInit, Input, SimpleChanges, Output, EventEmitter } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Validators } from '@angular/forms';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';

@Component({
  selector: 'app-edit-group',
  templateUrl: './edit-group.component.html',
  styleUrls: ['./edit-group.component.css']
})
export class EditGroupComponent implements OnInit {
  groupForm;
  editConfirmed: boolean = false;
  loadingEdit: boolean = false;
  constructor( private formBuilder: FormBuilder, private userService: UserService, public messageService: MessageService) { 
    this.groupForm = this.formBuilder.group({
      name: ['', Validators.required],
      description: ['', Validators.required],
      owner: ['', Validators.required]
    });
  }
  
  @Input() group: any;
  @Input() user: any;
  @Output() onGroupChange: EventEmitter<any> = new EventEmitter()
  
  ngOnInit(): void {
    let owner = this.group.owner
  }

  ngOnChanges(changes: SimpleChanges) {
    let owner = this.group.owner
    this.groupForm.get('name').setValue(this.group.name)
    this.groupForm.get('description').setValue(this.group.description)
    this.groupForm.get('owner').setValue(owner)
  }

  onSubmit(formData) {
    if (this.editConfirmed) {
      if (this.groupForm.status == "VALID") {
        this.editConfirmed = false
        this.loadingEdit = true
        this.userService.editGroup(this.group.join_code, formData).toPromise().then(data => {
          this.messageService.open("Successfully edited " + this.group.name + ".", "right")
          this.group = data
          this.loadingEdit = false
          this.onGroupChange.emit(data)
        }).catch(error => {
          this.messageService.open("An error occured while trying to edit " + this.group.name + ". Please try again.", "right")
          this.loadingEdit = false
          console.log(error)
        })
      }
    } else {
      this.editConfirmed = true
    }
  }

  changingOwnership(): boolean {
    return this.groupForm.get('owner').value != this.group.owner
  }
}
