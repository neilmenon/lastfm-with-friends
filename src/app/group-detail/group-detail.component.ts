import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { UserService } from '../user.service';

@Component({
  selector: 'app-group-detail',
  templateUrl: './group-detail.component.html',
  styleUrls: ['./group-detail.component.css']
})
export class GroupDetailComponent implements OnInit {
  group;
  constructor(private route: ActivatedRoute, private userService: UserService) {
    this.route.paramMap.subscribe(params => {
      this.userService.getGroup(params.get('joinCode')).toPromise().then(data => {
        this.group = data
      })
    });
   }

  ngOnInit(): void {
    
  }

}
