import { DOCUMENT } from '@angular/common';
import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-getting-started',
  templateUrl: './getting-started.component.html',
  styleUrls: ['./getting-started.component.css']
})
export class GettingStartedComponent implements OnInit {
  public window: Window
  constructor(
    public dialogRef: MatDialogRef<GettingStartedComponent>,
    @Inject(DOCUMENT) private document: Document
  ) { 
    this.window = this.document.defaultView
  }

  ngOnInit(): void {
  }

}
