import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarHorizontalPosition } from '@angular/material/snack-bar'
@Injectable({
  providedIn: 'root',
})
export class MessageService {
  message: string;
  horizontalPosition: MatSnackBarHorizontalPosition = 'center';
  constructor(private snackBar: MatSnackBar) {}
  save(message: string) {
    this.message = message;
  }

  open(message: string) {
    this.snackBar.open(message, "Dismiss", {
      horizontalPosition: this.horizontalPosition,
      duration: 5000
    })
  }

}