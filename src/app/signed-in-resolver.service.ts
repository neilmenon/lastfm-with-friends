import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot } from '@angular/router';
import { Observable } from 'rxjs';
import { MessageService } from './message.service';
import { UserService } from './user.service';

@Injectable({
  providedIn: 'root'
})
export class SignedInResolverService {

  constructor(
    private userService: UserService,
    public router: Router,
    private messageService: MessageService
  ) { }

  resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<any> {
    let guestOnlyRoute: boolean = route.data?.guestOnly
    
    if (guestOnlyRoute) {
      this.router.navigate(['/']).then(() => {
        this.messageService.open("You do not have permission to access that page.")
      })
    } else {
      if (!this.userService.isSignedIn()) {
        this.router.navigate(['/']).then(() => {
          this.messageService.open("You do not have permission to access that page.")
        })
      }
    }


    return
  }
}
