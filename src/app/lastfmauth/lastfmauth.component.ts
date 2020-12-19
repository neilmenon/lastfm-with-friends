import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, NavigationExtras, Router } from '@angular/router';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-lastfmauth',
  templateUrl: './lastfmauth.component.html',
  styleUrls: ['./lastfmauth.component.css']
})
export class LastfmauthComponent implements OnInit {
  token;
  constructor(private authService: AuthService, private route: ActivatedRoute, public router: Router) { }

  ngOnInit(): void {
    this.token = localStorage.getItem('lastfm_token');
    if (this.token == null) {
      this.route.queryParams.subscribe(params => {
        if (params['token']) {
          localStorage.setItem("lastfm_token", params['token'])
          const message: NavigationExtras = {state: {message: 'Logged in! Token: ' + params['token']}};
          this.router.navigate([''], message)
        } else {
          window.location.href = 'https://www.last.fm/api/auth/?api_key=b2ed5e82a59e49eadc2db1883daf7d58&cb=http://localhost:4200/lastfmauth';
        }
      });
    } else {
      const message: NavigationExtras = {state: {message: 'Already logged in. Token: ' + this.token}};
      this.router.navigate([''], message)
    }
  }

}
