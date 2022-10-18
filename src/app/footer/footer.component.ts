import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { BuildModel, BuildService } from '../build.service';
import { UserService } from '../user.service';
import * as moment from 'moment';
import { NavigationEnd, Router } from '@angular/router';
import { NgRedux } from '@angular-redux2/store';
import { AppState } from '../store';
import { Subscription } from 'rxjs';
import { ObservableStore } from '../observable-store';

@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.css']
})
export class FooterComponent implements OnInit, AfterViewInit, OnDestroy {
  moment: any = moment
  stats: StatsModel = null
  build: BuildModel = null
  showFooter: boolean = false
  commit: any
  subscription: Subscription
  constructor(
    private userService: UserService, 
    private buildService: BuildService, 
    private router: Router,
    private ngRedux: ObservableStore<AppState>
  ) { }
  
  ngAfterViewInit(): void {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        // this.getFooter()
      }
    })
  }
  
  ngOnInit(): void {
    this.subscription = this.ngRedux.select(s => s.userModel).subscribe(obj => {
      if (obj && !(this.build || this.stats)) {
        this.showFooter = true
        this.userService.appStats().toPromise().then((data: StatsModel) => {
          this.stats = data
        })
        this.buildService.getBuildInfo().toPromise().then((data: BuildModel) => {
          this.build = data
          this.buildService.getCommitInfo(this.build.commit).toPromise().then((data: any) => {
            this.commit = data
          })
        })
      }
    })
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe()
  }
}

export class StatsModel {
  artists: number
    albums: number
    tracks: number
    scrobbles: number
    users: number
    groups: number
    genres: number

    constructor() {
      this.artists = null
      this.albums = null
      this.tracks = null
      this.scrobbles = null
      this.users = null
      this.groups = null
      this.genres = null
    }
}