import { Component, OnInit, Inject, ViewChild, EventEmitter, Output } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
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
  resultsObject: any = null;
  moment: any = moment;
  @ViewChild('paginator') paginator: MatPaginator

  // MatPaginator Inputs
  length = 500;
  pageSize = 50;
  pageIndex = 0;
  pageSizeOptions: number[] = [50, 100, 250, 500];

  // MatPaginator Output
  pageEvent: PageEvent;
  selectedUser: any = "all";
  sortBy: any = "track_scrobbles.timestamp";
  sortOrder: any = "DESC";
  paginationTriggered: boolean = false;

  // dates
  historyStartDate:moment.Moment;
  historyEndDate:moment.Moment;

  @Output() wkFromDialog: EventEmitter<any> = new EventEmitter(true)
  @Output() wkFromTopDialog: EventEmitter<any> = new EventEmitter(true)
  setPageSizeOptions(setPageSizeOptionsInput: string) {
    if (setPageSizeOptionsInput) {
      this.pageSizeOptions = setPageSizeOptionsInput.split(',').map(str => +str);
    }
  }

  constructor(@Inject(MAT_DIALOG_DATA) public data: any, private userService: UserService, public messageService: MessageService, public dialogRef: MatDialogRef<ScrobbleHistoryComponent>) { }

  ngOnInit(): void {
    if (this.data.chartUser) {
      this.selectedUser = this.data.chartUser
    }
    this.historyStartDate = this.data.startRange
    this.historyEndDate = this.data.endRange
    this.getHistoryPage(this.data.chartUser && this.data.chartUser != 'all' ? [this.data.chartUser] : this.data.group.members.map(u => u.id), this.sortBy, this.sortOrder, this.pageSize, 0, this.historyStartDate ? this.historyStartDate.format() : null, this.historyEndDate ? this.historyEndDate.format() : null)
  }

  paginationChange(pageData, selectedUser, reset=false) {
    this.resultsObject = null
    if (pageData === undefined) {
      pageData = {
        'pageSize': this.pageSize,
        'pageIndex': 0,
        'previousPageIndex': 0
      }
    }
    if (selectedUser == undefined || selectedUser == "all") {
      selectedUser = this.data.group.members.map(u => u.id)
    } else {
      selectedUser = [selectedUser]
    }
    this.paginationTriggered = true;
    if (reset) {
      this.paginator.pageIndex = 0;
    }
    let offset = reset ? 0 : (pageData['pageIndex'])*pageData['pageSize']
    this.getHistoryPage(selectedUser, this.sortBy, this.sortOrder, pageData['pageSize'], offset, this.historyStartDate ? this.historyStartDate.format() : null, this.historyEndDate ? this.historyEndDate.format() : null)
  }

  getHistoryPage(users, sortBy, sortOrder, limit, offset, startRange=null, endRange=null) {
    this.userService.scrobbleHistory(
      this.data.wkMode, 
      this.data.wkObject, 
      users,
      sortBy,
      sortOrder,
      limit,
      offset,
      startRange,
      endRange
    ).toPromise().then(data => {
      this.resultsObject = data
      if (this.resultsObject === null) {
        this.length = 0
        this.resultsObject = undefined
      } else {
        this.length = data['total']
      }
      this.paginationTriggered = false;
    }).catch(error => {
      this.messageService.open("Error getting play history. Please try again.")
      console.log(error)
      this.paginationTriggered = false;
    })
  }

  wkTrigger(data) {
    data['startDate'] = this.historyStartDate
    data['endDate'] = this.historyEndDate
    this.wkFromDialog.emit(data)
    this.dialogRef.close()
  }

  wkTopTrigger(wkMode, wkObject, users, selectedUser, entry) {
    if (this.data.chartUser) {
      wkObject = null
    }
    let payload: Object = {};
    payload['wkMode'] = wkMode
    payload['users'] = users
    payload['selectedUser'] = selectedUser
    payload['startDate'] = this.historyStartDate
    payload['endDate'] = this.historyEndDate
    if (wkObject == null) {
      this.userService.wkArtist(entry.artist, users.map(u => u.id)).toPromise().then(data => {
        payload['wkObject'] = data
        this.wkFromTopDialog.emit(payload)
        this.dialogRef.close()
      }).catch(error => {
        this.messageService.open("Error getting top scrobbles. Please try again.")
      })
    } else {
      payload['wkObject'] = wkObject
      this.wkFromTopDialog.emit(payload)
      this.dialogRef.close()
    }
  }

}
