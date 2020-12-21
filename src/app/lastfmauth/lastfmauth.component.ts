import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, NavigationExtras, Router } from '@angular/router';
import { MessageService } from '../message.service';
import { config } from '../config'
import { Md5 } from 'ts-md5/dist/md5';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-lastfmauth',
  templateUrl: './lastfmauth.component.html',
  styleUrls: ['./lastfmauth.component.css']
})
export class LastfmauthComponent implements OnInit {
  session;
  username;
  url_string;
  constructor(private route: ActivatedRoute, public router: Router, private messageService: MessageService, private http: HttpClient) { }

  ngOnInit(): void {
    this.session = localStorage.getItem('lastfm_session');
    if (this.session == null) {
      this.route.queryParams.subscribe(params => {
        if (params['token']) {

          let data = {}
          data['api_key'] = config.api_key;
          data['method'] = 'auth.getSession';
          data['token'] = params['token'];
          let post_data = this.sign(data);
          post_data['format'] = 'json';
          console.log(post_data)
          this.url_string = new URLSearchParams(post_data).toString()

          this.getSession().then(response => {
            console.log(response)
            this.session = response['session']['key'];
            this.username = response['session']['name']
            localStorage.setItem("lastfm_session", this.session)
            localStorage.setItem("lastfm_username", this.username)
            this.messageService.save('Successfully signed in as ' + this.username + '!')
            this.router.navigate([''])
          }).catch(error => {
            this.messageService.open("Error signing in! Last.fm returned: " + error['error']['message'])
            console.log(error)
            this.router.navigate([''])
          })
        } else {
          this.messageService.open("Sending you to authentication page...")
          window.location.href = 'https://www.last.fm/api/auth/?api_key='+ config.api_key +'&cb='+ config.project_root +'/lastfmauth';
        }
      });
    } else {
      this.messageService.save('Already signed in!')
      this.router.navigate([''])
    }
  }

  async getSession() {
    const response_data = await this.http.post("https://ws.audioscrobbler.com/2.0/?" + this.url_string, null).toPromise();
    return response_data;
    // this.http.post("https://ws.audioscrobbler.com/2.0/?" + this.url_string, null).toPromise().then(response => {
    //   console.log(response)
    //   this.session = response['session']['key'];
    //   this.username = response['session']['name']
    //   localStorage.setItem("lastfm_session", this.session)
    //   localStorage.setItem("lastfm_username", this.username)
    // })
  }

  sign(params) {
    let ss = "";
    let st = [];
    let so = {};
    Object.keys(params).forEach(function(key){
        st.push(key); // Get list of object keys
    });
    st.sort(); // Alphabetise it 
    st.forEach(function(std){
        ss = ss + std + params[std]; // build string
        so[std] = params[std];  // return object in exact same order JIC
    });
        // console.log(ss + last_fm_data['secret']);
        // api_keyAPIKEY1323454formatjsonmethodauth.getSessiontokenTOKEN876234876SECRET348264386
    let hashed_sec = Md5.hashStr(unescape(encodeURIComponent(ss + config.api_secret)));
    so['api_sig'] = hashed_sec; // Correct when calculated elsewhere.
    return so; // Returns signed POSTable object
  }

}
