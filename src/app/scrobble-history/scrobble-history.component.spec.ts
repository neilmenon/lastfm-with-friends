import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScrobbleHistoryComponent } from './scrobble-history.component';

describe('ScrobbleHistoryComponent', () => {
  let component: ScrobbleHistoryComponent;
  let fixture: ComponentFixture<ScrobbleHistoryComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ScrobbleHistoryComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ScrobbleHistoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
