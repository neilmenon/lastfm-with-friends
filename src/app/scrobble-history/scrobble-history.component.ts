import { Component, OnInit, Inject, ViewChild } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';
import * as moment from 'moment';

@Component({
  selector: 'app-scrobble-history',
  templateUrl: './scrobble-history.component.html',
  styleUrls: ['./scrobble-history.component.css']
})
export class ScrobbleHistoryComponent implements OnInit {
  resultsObject: any;
  moment: any = moment;
  @ViewChild('paginator') paginator: MatPaginator

  // MatPaginator Inputs
  length = 500;
  pageSize = 50;
  pageIndex = 0;
  pageSizeOptions: number[] = [25, 50, 100, 500];

  // MatPaginator Output
  pageEvent: PageEvent;
  selectedUser: any = "all";
  sortBy: any = "track_scrobbles.timestamp";
  sortOrder: any = "DESC";
  paginationTriggered: boolean = false;
  setPageSizeOptions(setPageSizeOptionsInput: string) {
    if (setPageSizeOptionsInput) {
      this.pageSizeOptions = setPageSizeOptionsInput.split(',').map(str => +str);
    }
  }

  constructor(@Inject(MAT_DIALOG_DATA) public data: any, private userService: UserService, public messageService: MessageService) { }

  ngOnInit(): void {
    this.getHistoryPage(this.data.group.members, this.sortBy, this.sortOrder, this.pageSize, 0)
  }

  paginationChange(pageData, selectedUser, reset=false) {
    if (pageData === undefined) {
      pageData = {
        'pageSize': this.pageSize,
        'pageIndex': 0,
        'previousPageIndex': 0
      }
    }
    if (selectedUser == undefined || selectedUser == "all") {
      selectedUser = this.data.group.members
    } else {
      selectedUser = [selectedUser]
    }
    console.log(pageData)
    console.log(selectedUser)
    console.log(this.sortBy)
    console.log(this.sortOrder)
    this.paginationTriggered = true;
    if (reset) {
      this.paginator.pageIndex = 0;
    }
    let offset = reset ? 0 : (pageData['pageIndex'])*pageData['pageSize']
    this.getHistoryPage(selectedUser, this.sortBy, this.sortOrder, pageData['pageSize'], offset)
  }

  getHistoryPage(users, sortBy, sortOrder, limit, offset) {
    this.userService.scrobbleHistory(
      this.data.wkMode, 
      this.data.wkObject, 
      users, 
      sortBy,
      sortOrder,
      limit,
      offset
    ).toPromise().then(data => {
      this.resultsObject = data
      this.length = data['total']
      this.paginationTriggered = false;
    }).catch(error => {
      this.messageService.open("Error getting play history. Please try again.")
      console.log(error)
      this.paginationTriggered = false;
    })
  }

}
