import { AfterViewInit, Component, OnInit } from '@angular/core';
import { BuildModel, BuildService } from '../build.service';
import { UserService } from '../user.service';
import * as moment from 'moment';
import { NavigationEnd, Router } from '@angular/router';

@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.css']
})
export class FooterComponent implements OnInit, AfterViewInit {
  moment: any = moment
  stats: StatsModel = null
  build: BuildModel = null
  showFooter: boolean = false
  commit: any
  constructor(private userService: UserService, private buildService: BuildService, private router: Router) { }

  ngAfterViewInit(): void {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        this.getFooter()
      }
    })
  }

  ngOnInit(): void {
    
  }

  getFooter() {
    this.showFooter = false
    setTimeout(() => {
      if (!(this.build || this.stats)) {
        if (this.userService.getUser()) {
          this.userService.getUser().toPromise().then((user) => {
            if (user){
              this.showFooter = true
              this.userService.appStats().toPromise().then((data: StatsModel) => {
                this.stats = data
              })
              this.buildService.getBuildInfo().toPromise().then((data: BuildModel) => {
                this.build = data
                this.buildService.getCommitInfo(this.build.commit).toPromise().then(data => {
                  this.commit = data
                })
              })
            }
          })
        }
      } else {
        this.showFooter = true
      }
    }, 250)
  }

}

export class StatsModel {
    artists: number
    albums: number
    tracks: number
    scrobbles: number
    users: number
    groups: number

    constructor() {
      this.artists = null
      this.albums = null
      this.tracks = null
      this.scrobbles = null
      this.users = null
      this.groups = null
    }
}