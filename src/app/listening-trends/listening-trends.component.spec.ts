import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ListeningTrendsComponent } from './listening-trends.component';

describe('ListeningTrendsComponent', () => {
  let component: ListeningTrendsComponent;
  let fixture: ComponentFixture<ListeningTrendsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ListeningTrendsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ListeningTrendsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
