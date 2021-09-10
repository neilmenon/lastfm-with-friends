import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';
import * as moment from 'moment';
import { GroupDetailModel, UserModel } from '../models/userGroupModel';
import { select } from '@angular-redux/store';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-group-detail',
  templateUrl: './group-detail.component.html',
  styleUrls: ['./group-detail.component.css']
})
export class GroupDetailComponent implements OnInit {
  @select(s => s.isDemo)
  isDemo: Observable<boolean>
  
  group: GroupDetailModel;
  user: UserModel;
  moment: any = moment;
  deleteConfirmed: boolean = false;
  leaveConfirmed: boolean = false;
  kickingUser: string = null;
  kickLoading: boolean = false;
  constructor(private route: ActivatedRoute, private userService: UserService, public messageService: MessageService, public router: Router) {
    this.route.paramMap.subscribe(params => {
      this.userService.getGroup(params.get('joinCode')).toPromise().then((data: any) => {
        this.group = data
        this.userService.getUser().toPromise().then((data: any) => {
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
    if (this.leaveConfirmed) {
      this.userService.leaveGroup(this.group['join_code']).toPromise().then((data: any) => {
        this.messageService.save("You have left the group " + this.group['name'] + ".")
        this.router.navigate(['/'])
      }).catch(error => {
        this.messageService.open("Unable to leave group. Please try again.")
        this.leaveConfirmed = false
        console.log(error)
      })
    } else {
      this.leaveConfirmed = true
    }
  }

  deleteGroup() {
    if (this.deleteConfirmed) {
      this.userService.deleteGroup(this.group['join_code']).toPromise().then((data: any) => {
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

  kickMember(username) {
    if (this.kickingUser) {
      this.kickLoading = true
      this.userService.kickMember(this.kickingUser, this.group['join_code']).toPromise().then((data: any) => {
        this.kickLoading = false
        this.group = data
        this.messageService.open("Successfully kicked " + username + ".")
        this.kickingUser = null
      }).catch(error => {
        this.kickLoading = false
        this.kickingUser = null
        this.messageService.open("Unable to kick " + username + ". Please try again.")
      })
    } else {
      this.kickingUser = username;
    }
  }

  reflectChanges(group: GroupDetailModel) {
    this.group = group
  }

}
