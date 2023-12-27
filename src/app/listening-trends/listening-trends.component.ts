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
  view: any[] = [window.innerWidth / 1.35, window.innerHeight / 1.60];
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
  isTrackMode: boolean = true;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any, 
    private userService: UserService, 
    public dialogRef: MatDialogRef<ListeningTrendsComponent>,
    private messageService: MessageService
  ) { }

  ngOnInit(): void {
    this.listeningTrends()
  }

  listeningTrends(cmdMode=this.data.cmdMode) {
    if (cmdMode == "leaderboard-noncu") {
      this.curve = shape.curveBumpX
    } else {
      this.curve = shape.curveBasis
    }
    this.data.cmdMode = cmdMode
    this.userService.listeningTrends(
      this.data.group.join_code, 
      cmdMode, 
      this.data.wkMode, 
      this.data.wkObject, 
      !this.data.startRange ? null : this.data.startRange.format(),
      !this.data.endRange ? null : this.data.endRange.format(),
      !this.data.userObject ? null : this.data.userObject.id
    ).toPromise().then((data: any) => {
        let masterTimestamps: any[] = []
        let chartDataTmp: any[] = []
        if (!cmdMode.includes("leaderboard")) {
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
              let tmpSeries = []
              let scrobbles: number = 0
              let scrobbleListFinal: any[] = scrobbleList as any[]
              tmpEntry = {"name": username, "series": [], numEntires: scrobbleListFinal.length}
              for (let timestamp of masterTimestamps) {
                if (scrobbleListFinal.includes(timestamp)) {
                  scrobbles++
                }
                tmpSeries.push({"name": moment.unix(timestamp).toDate(), "value": scrobbles})
              }
              tmpEntry['series'] = tmpSeries
            }
            chartDataTmp.push(tmpEntry)
          }
          chartDataTmp.sort((a, b) => b.numEntires - a.numEntires)
        } else {
          for (let index in data) {
            let tmpEntry
            for (let [username, scrobbleList] of Object.entries(data[parseInt(index)])) {
              let tmpSeries = []
              let scrobbles: number = 0
              let scrobbleListFinal: any[] = scrobbleList as any[]
              tmpEntry = {"name": username, "series": [], numEntires: scrobbleListFinal.length}
              for (let [index, record] of Object.entries(scrobbleList)) {
                let [timestamp, scrobbles] = Object.entries(record)[0]
                tmpSeries.push({"name": moment.unix(parseInt(timestamp)).toDate(), "value": scrobbles})
              }
              tmpEntry['series'] = tmpSeries
            }
            chartDataTmp.push(tmpEntry)
          }
        }
        if (cmdMode == "leaderboard-cu") {
          chartDataTmp.sort((a, b) => b.series[b.series.length - 1].value - a.series[b.series.length - 1].value)
        }
        this.chartData = this.adjustSeriesArrays(chartDataTmp)
    }).catch(error => {
      this.messageService.open("There was an error generating the trends chart. Please try again.")
      console.log(error)
    })
  }

  adjustSeriesArrays(data: { name: string; series: number[] }[]): any {
    const maxSumOfLengths = 25000;
    let sumOfLengths = data.reduce((accumulator, currentValue) => accumulator + currentValue.series.length, 0);
    console.log(`Total data points to show in chart is: ${sumOfLengths} of max ${maxSumOfLengths} allowed`)

    if (sumOfLengths < maxSumOfLengths)
      return data

    if (sumOfLengths >= 2 * maxSumOfLengths) {
      while (sumOfLengths >= 2 * maxSumOfLengths) {
        data.forEach((item) => {
          item.series = item.series.filter((_, index) => (index + 1) % 2 !== 0);
        });
        sumOfLengths = data.reduce((accumulator, currentValue) => accumulator + currentValue.series.length, 0)
        console.log(`Reduced data points to ${sumOfLengths}`)
      }
    }
  
    // Calculate the optimal value of n
    let n = 50;
    let tmpSumOfLengths = sumOfLengths
    while (tmpSumOfLengths >= maxSumOfLengths) {
      n--;
      tmpSumOfLengths = sumOfLengths - Math.floor(sumOfLengths / n);
    }
  
    // Remove every nth element from each series array
    if (n > 1 && n < 50) {
      console.log(`Removing each nth item from series arrays (n = ${n})`)
      data.forEach((item) => {
        item.series = item.series.filter((_, index) => (index + 1) % n !== 0);
      });
      sumOfLengths = data.reduce((accumulator, currentValue) => accumulator + currentValue.series.length, 0);
    }
    console.log(`Final total of data points is ${sumOfLengths}`)
    return data
  }

  dateTickFormatting(val: any): string {
    return moment(val).format("MM/DD/YY")
  }

  onSelect(data): void {
    // console.log('Item clicked', JSON.parse(JSON.stringify(data)));
  }

  onActivate(data): void {
    // console.log('Activate', JSON.parse(JSON.stringify(data)));
  }

  onDeactivate(data): void {
    // console.log('Deactivate', JSON.parse(JSON.stringify(data)));
  }

  onResize(event) {
    this.view = [event.target.innerWidth / 1.35, window.innerHeight / 1.60];
  }

}
