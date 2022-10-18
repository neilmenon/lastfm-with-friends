import { Component, EventEmitter, Inject, OnInit, Output } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';
import * as moment from 'moment';
import { Select } from '@angular-redux2/store';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-who-knows-top',
  templateUrl: './who-knows-top.component.html',
  styleUrls: ['./who-knows-top.component.css']
})
export class WhoKnowsTopComponent implements OnInit {
  //@Select(s => s.isDemo)
  isDemo: Observable<boolean>
  
  resultsObject: any;
  moment: any = moment;
  topStartDate: moment.Moment;
  topEndDate: moment.Moment;
  topStartDateString: string
  topEndDateString: string

  trackMode: boolean = true;
  selectedUser: any;

  @Output() wkFromDialog: EventEmitter<any> = new EventEmitter(true)
  @Output() scrobbleFromDialog: EventEmitter<any> = new EventEmitter(true)
  constructor(@Inject(MAT_DIALOG_DATA) public data: any, private userService: UserService, public messageService: MessageService, public dialogRef: MatDialogRef<WhoKnowsTopComponent>) { }

  ngOnInit(): void {
    this.topStartDate = this.data.startRange
    this.topEndDate = this.data.endRange
    this.topStartDateString = this.data.startRange ? this.data.startRange.format() : null
    this.topEndDateString = this.data.endRange ? this.data.endRange.format() : null,
    this.whoKnowsTop(this.data.wkMode, 
      [this.data.selectedUser.id], 
      this.data.wkObject.artist.id, 
      this.topStartDateString, 
      this.topEndDateString, 
      this.data.wkMode == "album" ? this.data.wkObject.album.id : null, 
      true
    )
    this.selectedUser = this.data.selectedUser.id
  }

  whoKnowsTop(wkMode, users, artistId, startRange, endRange, albumId=null, trackMode=false) {
    this.resultsObject = null
    this.userService.whoKnowsTop(wkMode, users, artistId, startRange, endRange, albumId, trackMode).toPromise().then((data: any) => {
      this.resultsObject = data
    }).catch(error => {
      this.messageService.open("Error getting top scrobbles. Please try again.")
      console.log(error)
    })
  }

  wkTrigger(data) {
    data['artist'] = this.data.wkObject.artist.name
    data['wkMode'] = this.data.wkMode
    data['startDate'] = this.topStartDate
    data['endDate'] = this.topEndDate
    this.wkFromDialog.emit(data)
    this.dialogRef.close()
  }

  scrobbleTrigger(entry) {
    let track: { artist: { name: string }, track: { name: string, album_name: string } } = {
      artist: { name: this.data.wkObject.artist.name },
      track: { name: entry.track, album_name: entry.album }
    }
    this.scrobbleFromDialog.emit(track)
  }
}
