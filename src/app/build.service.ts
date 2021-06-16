import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class BuildService {
  public build: BuildModel

  constructor(private http: HttpClient) {
    this.build = new BuildModel()
  }

  getBuildInfo() {
    const httpOptions = {
      headers: new HttpHeaders({'Cache-Control': 'no-cache'})
    }

    return this.http.get('assets/build.json', httpOptions)
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