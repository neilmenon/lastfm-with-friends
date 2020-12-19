import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  message;
  constructor(public router: Router) {
    const navigation = this.router.getCurrentNavigation().extras.state;
    console.log(navigation)
    if (navigation) {
      const state = navigation as {message: string};
      this.message = state.message;
    }
  }

  ngOnInit(): void {
  }

  clearToken() {
    localStorage.removeItem("lastfm_token")
  }
}
