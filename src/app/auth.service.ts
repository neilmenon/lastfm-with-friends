import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  constructor(private http: HttpClient) { }

  authenticate() {
    return this.http.get('https://www.last.fm/api/auth/?api_key=b2ed5e82a59e49eadc2db1883daf7d58');
  }
}
