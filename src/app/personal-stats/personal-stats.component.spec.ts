import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonalStatsComponent } from './personal-stats.component';

describe('PersonalStatsComponent', () => {
  let component: PersonalStatsComponent;
  let fixture: ComponentFixture<PersonalStatsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PersonalStatsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PersonalStatsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
