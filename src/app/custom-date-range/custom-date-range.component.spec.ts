import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CustomDateRangeComponent } from './custom-date-range.component';

describe('CustomDateRangeComponent', () => {
  let component: CustomDateRangeComponent;
  let fixture: ComponentFixture<CustomDateRangeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CustomDateRangeComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CustomDateRangeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
