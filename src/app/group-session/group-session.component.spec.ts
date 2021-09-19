import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GroupSessionComponent } from './group-session.component';

describe('GroupSessionComponent', () => {
  let component: GroupSessionComponent;
  let fixture: ComponentFixture<GroupSessionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ GroupSessionComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(GroupSessionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
