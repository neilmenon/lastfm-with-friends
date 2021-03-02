import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WhoKnowsTopComponent } from './who-knows-top.component';

describe('WhoKnowsTopComponent', () => {
  let component: WhoKnowsTopComponent;
  let fixture: ComponentFixture<WhoKnowsTopComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ WhoKnowsTopComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(WhoKnowsTopComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
