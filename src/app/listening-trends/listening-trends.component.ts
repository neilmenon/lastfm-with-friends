import { Component, Inject, OnInit, ViewEncapsulation } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import * as shape from 'd3-shape';
import * as moment from 'moment';
import { MessageService } from '../message.service';
import { UserService } from '../user.service';

@Component({
  selector: 'app-listening-trends',
  templateUrl: './listening-trends.component.html',
  styleUrls: ['./listening-trends.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class ListeningTrendsComponent implements OnInit {
  moment: any = moment;
  view: any[] = [window.innerWidth / 1.35, 500];
  legend: boolean = true;
  legendPosition: string = "below";
  showLabels: boolean = true;
  animations: boolean = true;
  showGridLines: boolean = false;
  xAxis: boolean = true;
  yAxis: boolean = true;
  showYAxisLabel: boolean = true;
  showXAxisLabel: boolean = true;
  xAxisLabel: string = 'Date';
  yAxisLabel: string = 'Scrobbles';
  timeline: boolean = true;
  curve: any = shape.curveBasis
  colorScheme = {
    // domain: ['#5AA454', '#E44D25', '#CFC0BB', '#7aa3e5', '#a8385d', '#aae3f5']
    domain: ['#D9863D', '#89BF7A', '#3282b8', '#F2C46D', '#bbe1fa', '#278ea5', '#b0a565', '#62a388', '#b9d2d2']
  };
  activeEntries: any[] = [];
  chartData: any[] = [];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any, 
    private userService: UserService, 
    public dialogRef: MatDialogRef<ListeningTrendsComponent>,
    private messageService: MessageService
  ) { }

  ngOnInit(): void {
    this.userService.listeningTrends(
      this.data.group.join_code, 
      this.data.cmdMode, 
      this.data.wkMode, 
      this.data.wkObject, 
      !this.data.startRange ? null : this.data.startRange.format(),
      !this.data.endRange ? null : this.data.endRange.format(),
    ).toPromise().then(data => {
        let masterTimestamps: any[] = []
        for (let index in data) {
          for (let [username, scrobbleList] of Object.entries(data[parseInt(index)])) {
            for (let timestamp of scrobbleList as any[]) {
              if (!masterTimestamps.includes(timestamp)) {
                masterTimestamps.push(timestamp)
              }
            }
          }
        }
        masterTimestamps.sort((a, b) => a - b)
        for (let index in data) {
          let tmpEntry
          for (let [username, scrobbleList] of Object.entries(data[parseInt(index)])) {
            tmpEntry = {"name": username, "series": []}
            let tmpSeries = []
            let scrobbles: number = 0
            let scrobbleListFinal: any[] = scrobbleList as any[]
            for (let timestamp of masterTimestamps) {
              if (scrobbleListFinal.includes(timestamp)) {
                scrobbles++
              }
              tmpSeries.push({"name": moment.unix(timestamp).toDate(), "value": scrobbles})
            }
            tmpEntry['series'] = tmpSeries
          }
          this.chartData.push(tmpEntry)
        }
    }).catch(error => {
      this.messageService.open("There was an error generating the trends chart. Please try again.")
      console.log(error)
    })
  }

  dateTickFormatting(val: any): string {
    return moment(val).format("MM/DD/YY")
  }

  onSelect(data): void {
    console.log('Item clicked', JSON.parse(JSON.stringify(data)));
  }

  onActivate(data): void {
    console.log('Activate', JSON.parse(JSON.stringify(data)));
  }

  onDeactivate(data): void {
    console.log('Deactivate', JSON.parse(JSON.stringify(data)));
  }

  onResize(event) {
    this.view = [event.target.innerWidth / 1.35, 500];
  }

}
