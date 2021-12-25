import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-faqs',
  templateUrl: './faqs.component.html',
  styleUrls: ['./faqs.component.css'],
})
export class FaqsComponent implements OnInit {
  @Input() gettingStarted: boolean = false
  
  constructor() { }

  ngOnInit(): void {
  }

}
