import { Component, Inject, OnInit, Output, EventEmitter } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MAT_MOMENT_DATE_FORMATS, MomentDateAdapter, MAT_MOMENT_DATE_ADAPTER_OPTIONS } from '@angular/material-moment-adapter';
import { DateAdapter, MAT_DATE_FORMATS, MAT_DATE_LOCALE } from '@angular/material/core';

import * as moment from 'moment';
import { MatDatepickerInputEvent } from '@angular/material/datepicker';


@Component({
  selector: 'app-custom-date-range',
  templateUrl: './custom-date-range.component.html',
  styleUrls: ['./custom-date-range.component.css'],
  providers: [
    {provide: DateAdapter, useClass: MomentDateAdapter, deps: [MAT_DATE_LOCALE]},
    {provide: MAT_DATE_FORMATS, useValue: MAT_MOMENT_DATE_FORMATS},
    {provide: MAT_MOMENT_DATE_ADAPTER_OPTIONS, useValue: {useUtc: true}}
  ],
})
export class CustomDateRangeComponent implements OnInit {
  moment = moment;
  startDate: moment.Moment;
  endDate: moment.Moment;
  yearButtons: number[] = [];
  @Output() dateChange: EventEmitter<MatDatepickerInputEvent< any>>
  @Output() submitDateRange: EventEmitter<any> = new EventEmitter(true)
  constructor(@Inject(MAT_DIALOG_DATA) public data: any, public dialogRef: MatDialogRef<CustomDateRangeComponent>) { }

  ngOnInit(): void {
    for (let y = this.moment().year(); y >= this.moment().year() - 7; y--) {
      this.yearButtons.push(y);
    }
  }

  onDateChange(event: any, type:any) {
    if (event.value !== null) {
      if (type == "start") {
        this.startDate = moment.utc(event.value)
        this.endDate = undefined
      } else {
        this.endDate = moment.utc(event.value)
      }
      if (this.startDate && this.endDate && this.endDate.diff(this.startDate) >= 0) {
        if (this.endDate.diff(this.startDate) == 0) { // if start and end same, they most likely meant just that 24 hr period
          this.endDate = moment(this.startDate).add(24, 'hours')
        }
        this.submitDateRange.emit({'startDate': this.startDate, 'endDate': this.endDate})
        this.dialogRef.close()
      }
    }
  
  }
  
  setPreset(year: number) {
    let start: moment.Moment;
    let end: moment.Moment;
    start = this.moment.utc({year: year, month: 0, day: 1}).startOf('day');
    end = this.moment.utc(start).add(1, 'year').subtract(1, 'second');
    this.submitDateRange.emit({'startDate': start, 'endDate': end});
    this.dialogRef.close();
  }
    

}
