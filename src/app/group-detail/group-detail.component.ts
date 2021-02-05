import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';
import * as moment from 'moment';

@Component({
  selector: 'app-group-detail',
  templateUrl: './group-detail.component.html',
  styleUrls: ['./group-detail.component.css']
})
export class GroupDetailComponent implements OnInit {
  group;
  user;
  moment: any = moment;
  deleteConfirmed: boolean = false;
  constructor(private route: ActivatedRoute, private userService: UserService, private messageService: MessageService, public router: Router) {
    this.route.paramMap.subscribe(params => {
      this.userService.getGroup(params.get('joinCode')).toPromise().then(data => {
        this.group = data
        this.userService.getUser().toPromise().then(data => {
          this.user = data
        })
      }).catch(error => {
        if (error['status'] == 404 || error['status'] == 401) {
          this.messageService.save("Group not found.")
          this.router.navigate(['/'])
        }
      })
    });
   }

  ngOnInit(): void {
    
  }

  leaveGroup() {
    this.userService.leaveGroup(this.group['join_code']).toPromise().then(data => {
      this.messageService.save("You have left the group " + this.group['name'] + ".")
      this.router.navigate(['/'])
    }).catch(error => {
      this.messageService.open("Unable to leave group. Please try again.")
      console.log(error)
    })
  }

  deleteGroup() {
    if (this.deleteConfirmed) {
      this.userService.deleteGroup(this.group['join_code']).toPromise().then(data => {
        this.messageService.save("You have deleted the group " + this.group['name'] + ".")
        this.router.navigate(['/'])
      }).catch(error => {
        this.messageService.open("Unable to delete group. Please try again.")
        this.deleteConfirmed = false
        console.log(error)
      })
    } else {
      this.deleteConfirmed = true
    }
  }

  reflectChanges(group: any) {
    this.group = group
  }

}
