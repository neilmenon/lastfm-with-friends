import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarHorizontalPosition } from '@angular/material/snack-bar'
@Injectable({
  providedIn: 'root',
})
export class MessageService {
  message: string;
  centerPosition: MatSnackBarHorizontalPosition = 'center';
  leftPosition: MatSnackBarHorizontalPosition = "left";
  rightPosition: MatSnackBarHorizontalPosition = "right";
  positions: any = {};
  constructor(private snackBar: MatSnackBar) {
    this.positions['left'] = this.leftPosition;
    this.positions['center'] = this.centerPosition;
    this.positions['right'] = this.rightPosition;
  }
  save(message: string) {
    this.message = message;
  }

  open(message: string, position = "center", persistent: boolean = false) {
    if (persistent) {
      this.snackBar.open(message, undefined, {
        horizontalPosition: this.positions[position],
        duration: 0
      })
    } else {
      this.snackBar.open(message, "Dismiss", {
        horizontalPosition: this.positions[position],
        duration: 5000
      })
    }
  }

  copyJoinCode(joinCode: string, groupName: string) {
    const selBox: HTMLTextAreaElement = document.createElement('textarea')
    selBox.style.position = 'fixed'
    selBox.style.left = '0';
    selBox.style.top = '0';
    selBox.style.opacity = '0';
    selBox.value = joinCode;
    document.body.appendChild(selBox)
    selBox.focus()
    selBox.select()
    document.execCommand('copy')
    document.body.removeChild(selBox)
    this.open("Join code for " + groupName + " copied to clipboard.")
  }

}