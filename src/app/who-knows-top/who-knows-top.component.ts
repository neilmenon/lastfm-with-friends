import { Component, EventEmitter, Inject, OnInit, Output } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';
import * as moment from 'moment';

@Component({
  selector: 'app-who-knows-top',
  templateUrl: './who-knows-top.component.html',
  styleUrls: ['./who-knows-top.component.css']
})
export class WhoKnowsTopComponent implements OnInit {
  resultsObject: any;
  moment: any = moment;

  trackMode: boolean = true;
  selectedUser: any;

  @Output() wkFromDialog: EventEmitter<any> = new EventEmitter(true)
  constructor(@Inject(MAT_DIALOG_DATA) public data: any, private userService: UserService, public messageService: MessageService, public dialogRef: MatDialogRef<WhoKnowsTopComponent>) { }

  ngOnInit(): void {
    this.whoKnowsTop(this.data.wkMode, [this.data.selectedUser.id], this.data.wkObject.artist.id, this.data.wkMode == "album" ? this.data.wkObject.album.id : null, true)
    this.selectedUser = this.data.selectedUser.id
  }

  whoKnowsTop(wkMode, users, artistId, albumId=null, trackMode=false) {
    this.resultsObject = null
    this.userService.whoKnowsTop(wkMode, users, artistId, albumId, trackMode).toPromise().then(data => {
      this.resultsObject = data
    }).catch(error => {
      this.messageService.open("Error getting top scrobbles. Please try again.")
      console.log(error)
    })
  }

  wkTrigger(data) {
    data['artist'] = this.data.wkObject.artist.name
    console.log(data)
    this.wkFromDialog.emit(data)
    this.dialogRef.close()
  }

}
