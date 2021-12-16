import { Component, EventEmitter, Inject, OnInit, Output } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MessageService } from '../message.service';
import { GenreTopArtistsRecordModel } from '../models/commandsModel';
import { UserService } from '../user.service';

@Component({
  selector: 'app-genre-top-artists',
  templateUrl: './genre-top-artists.component.html',
  styleUrls: ['./genre-top-artists.component.css']
})
export class GenreTopArtistsComponent implements OnInit {
  resultsObject: Array<GenreTopArtistsRecordModel>
  @Output() wkFromDialog: EventEmitter<any> = new EventEmitter(true)

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: {genre: { id: number, name: string }}, 
    private userService: UserService, 
    public messageService: MessageService, 
    public dialogRef: MatDialogRef<GenreTopArtistsComponent>
  ) { }

  ngOnInit(): void {
    this.getGenreTopArtists()
  }

  getGenreTopArtists() {
    this.userService.getGenreTopArtists(this.data.genre.id).toPromise().then((data: any[]) => {
      this.resultsObject = data
    }).catch(() => {
      this.messageService.open("Error getting the top artists for this genre. Please try again.")
    })
  }

  wkTrigger(data: GenreTopArtistsRecordModel) {
    data['artist'] = data.name
    this.wkFromDialog.emit(data)
    this.dialogRef.close()
  }

}
