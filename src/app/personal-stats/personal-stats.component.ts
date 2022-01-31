import { Component, Input, OnInit } from '@angular/core';
import * as moment from 'moment';
import { PersonalStatsModel, UserModel } from '../models/userGroupModel';

@Component({
  selector: 'app-personal-stats',
  templateUrl: './personal-stats.component.html',
  styleUrls: ['./personal-stats.component.css']
})
export class PersonalStatsComponent implements OnInit {
  @Input("user") user: UserModel
  stats: PersonalStatsModel
  moment = moment
  activeHourText: string = ""

  constructor() { }

  ngOnInit(): void {
    this.stats = this.user.stats
    this.activeHourText = this.getActiveHourText()
  }

  getActiveHourText(): string {
    let hour: number = moment().utc().set({ hour: this.stats.most_active_hour, minute: 0 }).local().hour()
    let randomArtist: string = this.randomChoice(this.stats.top_rising).artist
    switch(hour) {
      case 0:
      case 1:
        return this.randomChoice(["I should probably sleep", "the new release owl", "checking for a new [artist] track", "midnight with [artist]"]).replace("[artist]", randomArtist)
      
      case 2:
      case 3:
      case 4:
        return this.randomChoice(["the sleep does not exist", "when your music gets weird", "the night owl", "insomnia scrobbler", "[artist] says you can sleep now"]).replace("[artist]", randomArtist)

      case 5:
      case 6:
        return this.randomChoice(["morning melodies", "is the sun even out?", "the early morning listener", "the dawn of scrobbles", "the pretenious morning scrobbler", "too early for [artist]..."]).replace("[artist]", randomArtist)
      
      case 7:
      case 8:
      case 9:
      case 10:
      case 11:
        return this.randomChoice(["bands with breakfast", "your toast with jams", "the morning listener", "starting the day with [artist]"]).replace("[artist]", randomArtist)

      case 12:
      case 13:
      case 14:
      case 15:
      case 16:
      case 17:
        return this.randomChoice(["the daytime scrobbler", "the daytime grind with [artist]", "spinning some [artist]"]).replace("[artist]", randomArtist)

      case 18:
      case 19:
      case 20:
        return this.randomChoice(["the sundown scrobbler", "sunset with [artist]"]).replace("[artist]", randomArtist)

      case 21:
      case 22:
      case 23:
        return this.randomChoice(["the night listener", "scrobbles before bed", "winding down with [artist]"]).replace("[artist]", randomArtist)

    }
  }

  randomChoice(arr: Array<any>): any {
    return arr[Math.floor(Math.random()*arr.length)]
  }

}
