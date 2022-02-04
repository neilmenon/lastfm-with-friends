import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AboutGroupSessionsComponent } from './about-group-sessions.component';

describe('AboutGroupSessionsComponent', () => {
  let component: AboutGroupSessionsComponent;
  let fixture: ComponentFixture<AboutGroupSessionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AboutGroupSessionsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AboutGroupSessionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
