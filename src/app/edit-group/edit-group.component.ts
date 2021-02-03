import { Component, OnInit, Input, SimpleChanges } from '@angular/core';
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
  constructor( private formBuilder: FormBuilder, private userService: UserService, public messageService: MessageService) { 
    this.groupForm = this.formBuilder.group({
      name: ['', Validators.required],
      description: ['', Validators.required]
    });
  }

  @Input() group: any;
  @Input() user: any;

  ngOnInit(): void {
    
  }

  ngOnChanges(changes: SimpleChanges) {
    this.groupForm.get('name').setValue(this.group.name)
    this.groupForm.get('description').setValue(this.group.description)
  }

  onSubmit(formData) {
    if (this.groupForm.status == "VALID") {
      console.log(formData)
    }
  }

}
