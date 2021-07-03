import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { share } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class BuildService {
  public build: BuildModel
  commitInfo: Observable<any>

  constructor(private http: HttpClient) {
    this.build = new BuildModel()
  }

  getBuildInfo() {
    const httpOptions = {
      headers: new HttpHeaders({'Cache-Control': 'no-cache'})
    }

    return this.http.get('assets/build.json', httpOptions)
  }

  getCommitInfo(commitHash: string): Observable<any> {
    if (this.commitInfo) {
      return this.commitInfo
    } else {
      this.commitInfo = this.http.get('https://api.github.com/repos/neilmenon/lastfm-with-friends/git/commits/' + commitHash).pipe(share())
      return this.commitInfo
    }
  }
}

export class BuildModel {
  unixTimestamp: number
  commit: string

  constructor() {
    this.unixTimestamp = null
    this.commit = null
  }
}